import threading
import time
import random
import signal
import sys
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
import logging

# Import our components
from network_manager import NetworkManager, NetworkMessage
from deliver_engine import DeliverEngine
from config_loader import ConfigManager

class ProcessNode:
    """
    Main process node that integrates all SES components
    Handles message sending, receiving, and SES ordering
    """
    
    def __init__(self, node_id: int, config_path: str = "config.json"):
        self.node_id = node_id
        self.config_path = config_path
        
        # Load and validate configuration
        self.config_manager = ConfigManager(config_path)
        if not self.config_manager.validate():
            raise ValueError(f"Invalid configuration: {self.config_manager.get_error()}")
        
        self.config = self.config_manager.get_config()
        
        # Process information
        self.all_process_ids = [p["id"] for p in self.config["processes"]]
        self.other_process_ids = [pid for pid in self.all_process_ids if pid != node_id]
        
        # Message sending configuration
        self.send_rate = self.config.get("send_rate", 50)  # messages per minute
        self.messages_per_process = self.config.get("messages_per_process", 150)
        self.send_interval = 60.0 / self.send_rate  # seconds between messages
        
        # Startup coordination
        self.startup_delay = self.config.get("startup_delay", 10)  # Default 10 seconds
        self.enable_startup_sync = self.config.get("enable_startup_sync", True)
        
        # Core components
        self.delivery_engine = DeliverEngine(node_id, self._process_received_message)
        self.network_manager = NetworkManager(node_id, self.config, self._handle_network_message)
        
        # Threading and control
        self.sender_threads = {}  # {target_id: thread}
        self.running = False
        self.paused = False
        self.pause_event = threading.Event()
        self.pause_event.set()  # Initially not paused
        
        # Message tracking
        self.sent_messages = {}  # {target_id: count}
        self.received_messages = {}  # {sender_id: count}
        self.message_sequences = {}  # {target_id: next_seq}
        
        # Statistics
        self.stats = {
            "start_time": None,
            "messages_sent_total": 0,
            "messages_received_total": 0,
            "uptime_seconds": 0.0
        }
        
        # Logging
        self.logger = logging.getLogger(f"ProcessNode-{node_id}")
        self.logger.setLevel(logging.INFO)
        
        # Initialize message sequences
        for target_id in self.other_process_ids:
            self.sent_messages[target_id] = 0
            self.message_sequences[target_id] = 1
        
        for sender_id in self.other_process_ids:
            self.received_messages[sender_id] = 0
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.info(f"Process node {node_id} initialized")
    
    def start(self):
        """Start the process node"""
        if self.running:
            self.logger.warning("Process already running")
            return
        
        self.running = True
        self.stats["start_time"] = time.time()
        
        # Start delivery engine
        self.delivery_engine.start()
        
        # Start network manager (server only initially)
        self.network_manager.start_server_only()
        
        # Startup coordination: wait for all processes to be ready
        if self.enable_startup_sync:
            self.logger.info(f"Waiting {self.startup_delay} seconds for all processes to start...")
            time.sleep(self.startup_delay)
        
        # Now start client connections
        self.network_manager.start_client_connections()
        
        # Wait for network connections to establish
        self.logger.info("Waiting for network connections to establish...")
        self._wait_for_connections()
        
        # Start sender threads
        self._start_sender_threads()
        
        self.logger.info(f"Process node {self.node_id} started successfully")
    
    def stop(self):
        """Stop the process node gracefully"""
        if not self.running:
            return
        
        self.logger.info("Stopping process node...")
        self.running = False
        
        # Stop sender threads
        for thread in self.sender_threads.values():
            if thread.is_alive():
                thread.join(timeout=2.0)
        
        # Stop components
        self.network_manager.stop()
        self.delivery_engine.stop()
        
        # Update final statistics
        self.stats["uptime_seconds"] = time.time() - self.stats["start_time"]
        
        self.logger.info("Process node stopped")
    
    def pause_sending(self):
        """Pause message sending"""
        self.paused = True
        self.pause_event.clear()
        self.logger.info("Message sending paused")
    
    def resume_sending(self):
        """Resume message sending"""
        self.paused = False
        self.pause_event.set()
        self.logger.info("Message sending resumed")
    
    def _wait_for_connections(self):
        """Wait for network connections to establish"""
        max_wait_time = 30.0  # Maximum wait time
        check_interval = 0.5  # Check every 500ms
        start_time = time.time()
        
        while (time.time() - start_time) < max_wait_time and self.running:
            connected = self.network_manager.get_connected_processes()
            if len(connected) >= len(self.other_process_ids) * 0.8:  # 80% connected
                self.logger.info(f"Sufficient connections established: {len(connected)}/{len(self.other_process_ids)}")
                return
            
            time.sleep(check_interval)
        
        connected = self.network_manager.get_connected_processes()
        self.logger.warning(f"Started with partial connections: {len(connected)}/{len(self.other_process_ids)}")
    
    def _start_sender_threads(self):
        """Start sender threads for each target process"""
        for target_id in self.other_process_ids:
            thread = threading.Thread(
                target=self._sender_worker,
                args=(target_id,),
                name=f"Sender-{self.node_id}-to-{target_id}",
                daemon=True
            )
            thread.start()
            self.sender_threads[target_id] = thread
            
        self.logger.info(f"Started {len(self.sender_threads)} sender threads")
    
    def _sender_worker(self, target_id: int):
        """Worker thread to send messages to a specific target process"""
        messages_sent = 0
        
        self.logger.debug(f"Sender worker started for target {target_id}")
        
        while self.running and messages_sent < self.messages_per_process:
            # Wait if paused
            self.pause_event.wait()
            
            if not self.running:
                break
            
            try:
                # Create and send message
                seq = self.message_sequences[target_id]
                payload = f"Hello from P{self.node_id} to P{target_id} #{seq}"
                
                # Prepare message using delivery engine (updates clock)
                message_data = self.delivery_engine.send_message(target_id, seq, payload)
                
                # Create network message
                network_msg = NetworkMessage(
                    sender_id=self.node_id,
                    receiver_id=target_id,
                    seq=seq,
                    vector_clock=message_data["vector_clock"],
                    payload=payload
                )
                
                # Send via network manager
                self.network_manager.send_message(network_msg)
                
                # Update tracking
                self.message_sequences[target_id] += 1
                self.sent_messages[target_id] += 1
                self.stats["messages_sent_total"] += 1
                messages_sent += 1
                
                self.logger.debug(f"Sent message #{seq} to P{target_id}")
                
                # Wait before sending next message
                time.sleep(self.send_interval + random.uniform(-0.1, 0.1))  # Add jitter
                
            except Exception as e:
                self.logger.error(f"Error in sender worker for P{target_id}: {e}")
                # Don't exit on error, keep trying
                time.sleep(2.0)
                continue
        
        self.logger.debug(f"Sender worker for P{target_id} completed ({messages_sent} messages)")
    
    def _handle_network_message(self, network_msg: NetworkMessage):
        """Handle incoming network message"""
        try:
            # Convert to standard message format
            message_data = {
                "sender_id": network_msg.sender_id,
                "receiver_id": network_msg.receiver_id,
                "seq": network_msg.seq,
                "vector_clock": network_msg.vector_clock,
                "payload": network_msg.payload,
                "timestamp": network_msg.timestamp
            }
            
            # Process through delivery engine
            success = self.delivery_engine.receive_message(message_data)
            
            if success:
                self.stats["messages_received_total"] += 1
                self.received_messages[network_msg.sender_id] += 1
                
                self.logger.debug(
                    f"Received message P{network_msg.sender_id}#{network_msg.seq}: {network_msg.payload}"
                )
            
        except Exception as e:
            self.logger.error(f"Error handling network message: {e}")
    
    def _process_received_message(self, message: Dict[str, Any]):
        """Process a delivered message (called by delivery engine)"""
        # This is where the application logic would go
        # For now, just log the delivery
        self.logger.info(
            f"DELIVERED: P{message['sender_id']}#{message['seq']} - {message['payload']}"
        )
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current process status"""
        uptime = time.time() - self.stats["start_time"] if self.stats["start_time"] else 0
        
        # Get component statistics
        delivery_stats = self.delivery_engine.get_delivery_stats()
        network_stats = self.network_manager.get_stats()
        
        return {
            "process_id": self.node_id,
            "running": self.running,
            "paused": self.paused,
            "uptime_seconds": uptime,
            "network_stats": network_stats,
            "delivery_stats": delivery_stats,
            "message_counts": {
                "sent_total": self.stats["messages_sent_total"],
                "received_total": self.stats["messages_received_total"],
                "sent_per_target": self.sent_messages.copy(),
                "received_per_sender": self.received_messages.copy()
            },
            "current_clock": self.delivery_engine.get_current_clock()
        }
    
    def get_summary(self) -> str:
        """Get human-readable status summary"""
        status = self.get_status()
        
        summary = f"\n=== Process {self.node_id} Status ===\n"
        summary += f"Running: {status['running']}, Paused: {status['paused']}\n"
        summary += f"Uptime: {status['uptime_seconds']:.1f} seconds\n"
        summary += f"Messages Sent: {status['message_counts']['sent_total']}\n"
        summary += f"Messages Received: {status['message_counts']['received_total']}\n"
        summary += f"Connected Processes: {status['network_stats']['connected_processes']}/{status['network_stats']['total_processes']}\n"
        summary += f"Current Vector Clock: {status['current_clock']}\n"
        
        # Buffer information
        buffer_stats = status['delivery_stats']['buffer_stats']
        summary += f"Buffer Size: {buffer_stats['current_buffer_size']}\n"
        
        # Recent sending status
        summary += "\nSending Progress:\n"
        for target_id in sorted(self.other_process_ids):
            sent = status['message_counts']['sent_per_target'].get(target_id, 0)
            progress = (sent / self.messages_per_process) * 100
            summary += f"  To P{target_id}: {sent}/{self.messages_per_process} ({progress:.1f}%)\n"
        
        return summary
    
    def run_interactive(self):
        """Run with interactive commands"""
        self.start()
        
        print(f"\nProcess {self.node_id} started. Type 'help' for commands.")
        print("Commands: status, pause, resume, buffer, clock, quit")
        
        try:
            while self.running:
                try:
                    command = input(f"P{self.node_id}> ").strip().lower()
                    
                    if command == "help":
                        print("Commands:")
                        print("  status  - Show process status")
                        print("  pause   - Pause message sending")
                        print("  resume  - Resume message sending") 
                        print("  buffer  - Show buffer state")
                        print("  clock   - Show current vector clock")
                        print("  quit    - Stop and exit")
                    
                    elif command == "status":
                        print(self.get_summary())
                    
                    elif command == "pause":
                        self.pause_sending()
                    
                    elif command == "resume":
                        self.resume_sending()
                    
                    elif command == "buffer":
                        buffer_summary = self.delivery_engine.buffer_manager.get_buffer_summary()
                        print(buffer_summary)
                    
                    elif command == "clock":
                        clock = self.delivery_engine.get_current_clock()
                        print(f"Current vector clock: {clock}")
                    
                    elif command in ["quit", "exit", "q"]:
                        break
                    
                    elif command == "":
                        continue
                    
                    else:
                        print(f"Unknown command: {command}. Type 'help' for available commands.")
                
                except EOFError:
                    break
                except KeyboardInterrupt:
                    print("\nUse 'quit' command to exit gracefully.")
        
        finally:
            self.stop()
    
    def run_daemon(self):
        """Run process in daemon mode (non-interactive)"""
        try:
            self.logger.info(f"Starting process {self.node_id} in daemon mode")
            self.start()
            
            # Keep running until shutdown signal
            import time
            while self.running:
                time.sleep(1.0)
                
        except KeyboardInterrupt:
            self.logger.info("Received shutdown signal")
        except Exception as e:
            self.logger.error(f"Error in daemon mode: {e}")
        finally:
            self.stop()
    
    def run_until_complete(self):
        """Run until all messages are sent"""
        self.start()
        
        try:
            # Monitor progress
            while self.running:
                time.sleep(5.0)
                
                status = self.get_status()
                total_to_send = len(self.other_process_ids) * self.messages_per_process
                sent = status['message_counts']['sent_total']
                
                progress = (sent / total_to_send) * 100
                self.logger.info(f"Progress: {sent}/{total_to_send} ({progress:.1f}%)")
                
                # Check if all messages sent
                if sent >= total_to_send:
                    self.logger.info("All messages sent, waiting for remaining deliveries...")
                    time.sleep(10.0)  # Wait for remaining deliveries
                    break
                
                # Check if all sender threads completed
                active_threads = sum(1 for t in self.sender_threads.values() if t.is_alive())
                if active_threads == 0:
                    self.logger.info("All sender threads completed")
                    time.sleep(5.0)  # Wait for remaining deliveries
                    break
        
        finally:
            self.stop()

def main():
    """Main entry point"""
    if len(sys.argv) != 2:
        print("Usage: python process_node.py <process_id>")
        print("Example: python process_node.py 0")
        sys.exit(1)
    
    try:
        process_id = int(sys.argv[1])
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(f'logs/process_{process_id}.log')
            ]
        )
        
        # Create and run process
        process = ProcessNode(process_id)
        
        # Run in interactive mode for testing
        process.run_interactive()
        
    except ValueError as e:
        print(f"Invalid process ID: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
