"""
Network communication layer for SES distributed system
Handles TCP socket connections, message serialization, and network management
"""

import socket
import json
import threading
import time
import queue
from typing import Dict, List, Callable, Any, Optional
from datetime import datetime
import logging

class NetworkMessage:
    """Represents a network message with SES vector clock"""
    def __init__(self, sender_id: int, receiver_id: int, seq: int, 
                 vector_clock: List[int], payload: str, msg_type: str = "data"):
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.seq = seq
        self.vector_clock = vector_clock.copy()
        self.payload = payload
        self.msg_type = msg_type
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize message to dictionary for JSON transmission"""
        return {
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "seq": self.seq,
            "vector_clock": self.vector_clock,
            "payload": self.payload,
            "msg_type": self.msg_type,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NetworkMessage':
        """Deserialize message from dictionary"""
        msg = cls(
            sender_id=data["sender_id"],
            receiver_id=data["receiver_id"],
            seq=data["seq"],
            vector_clock=data["vector_clock"],
            payload=data["payload"],
            msg_type=data.get("msg_type", "data")
        )
        msg.timestamp = data.get("timestamp", datetime.now().isoformat())
        return msg

class NetworkManager:
    """Manages TCP connections and message routing for a process"""
    
    def __init__(self, process_id: int, config: Dict[str, Any], 
                 message_handler: Callable[[NetworkMessage], None]):
        self.process_id = process_id
        self.config = config
        self.message_handler = message_handler
        
        # Network configuration
        self.my_config = next(p for p in config["processes"] if p["id"] == process_id)
        self.host = self.my_config["ip"]
        self.port = self.my_config["port"]
        
        # Connection management
        self.server_socket = None
        self.client_sockets = {}  # {process_id: socket}
        self.connection_locks = {}  # {process_id: lock}
        self.connections_ready = {}  # {process_id: bool}
        
        # Threading
        self.server_thread = None
        self.running = False
        self.send_queue = queue.Queue()
        self.send_thread = None
        
        # Logging
        self.logger = logging.getLogger(f"NetworkManager-{process_id}")
        self.logger.setLevel(logging.INFO)
        
        # Statistics
        self.stats = {
            "messages_sent": 0,
            "messages_received": 0,
            "connection_errors": 0,
            "reconnections": 0
        }
        
        # Initialize locks for all other processes
        for proc in config["processes"]:
            if proc["id"] != process_id:
                self.connection_locks[proc["id"]] = threading.Lock()
                self.connections_ready[proc["id"]] = False
    
    def start_server_only(self):
        """Start only the server component (no client connections yet)"""
        self.running = True
        
        # Start server thread
        self.server_thread = threading.Thread(target=self._run_server, daemon=True)
        self.server_thread.start()
        
        # Start send queue processor
        self.send_thread = threading.Thread(target=self._process_send_queue, daemon=True)
        self.send_thread.start()
        
        self.logger.info(f"Network server started for process {self.process_id}")
    
    def start_client_connections(self):
        """Start client connections to other processes"""
        # Connect to all other processes
        for proc in self.config["processes"]:
            if proc["id"] != self.process_id:
                self._connect_to_process(proc["id"], proc["ip"], proc["port"])
        
        self.logger.info(f"Network client connections initiated for process {self.process_id}")
    
    def start(self):
        """Start the network manager (both server and client)"""
        self.start_server_only()
        self.start_client_connections()
        
        self.logger.info(f"Network manager started for process {self.process_id}")
    
    def stop(self):
        """Stop the network manager"""
        self.running = False
        
        # Close all client connections
        for proc_id, sock in list(self.client_sockets.items()):
            try:
                sock.close()
            except:
                pass
        
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        self.logger.info(f"Network manager stopped for process {self.process_id}")
    
    def _run_server(self):
        """Run server to accept incoming connections"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(20)  # Support up to 20 connections
            
            self.logger.info(f"Server listening on {self.host}:{self.port}")
            
            while self.running:
                try:
                    client_socket, address = self.server_socket.accept()
                    # Handle client in separate thread
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, address),
                        daemon=True
                    )
                    client_thread.start()
                except Exception as e:
                    if self.running:
                        self.logger.error(f"Error accepting connection: {e}")
                        
        except Exception as e:
            self.logger.error(f"Server error: {e}")
    
    def _handle_client(self, client_socket: socket.socket, address):
        """Handle incoming client connection"""
        try:
            while self.running:
                data = self._receive_message(client_socket)
                if data is None:
                    break
                
                try:
                    message = NetworkMessage.from_dict(data)
                    self.stats["messages_received"] += 1
                    self.message_handler(message)
                except Exception as e:
                    self.logger.error(f"Error processing received message: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error handling client {address}: {e}")
        finally:
            client_socket.close()
    
    def _connect_to_all(self):
        """Connect to all other processes"""
        for proc in self.config["processes"]:
            if proc["id"] != self.process_id:
                self._connect_to_process(proc["id"], proc["ip"], proc["port"])
    
    def _connect_to_process(self, proc_id: int, host: str, port: int):
        """Connect to a specific process with retry logic"""
        def connect_worker():
            max_retries = 10
            retry_delay = 1.0
            
            for attempt in range(max_retries):
                try:
                    if not self.running:
                        return
                    
                    with self.connection_locks[proc_id]:
                        if self.connections_ready[proc_id]:
                            return  # Already connected
                        
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(10.0)  # 10 second timeout
                        sock.connect((host, port))
                        
                        self.client_sockets[proc_id] = sock
                        self.connections_ready[proc_id] = True
                        
                        self.logger.info(f"Connected to process {proc_id} at {host}:{port}")
                        return
                        
                except Exception as e:
                    self.stats["connection_errors"] += 1
                    if attempt == max_retries - 1:
                        self.logger.error(f"Failed to connect to process {proc_id} after {max_retries} attempts: {e}")
                    else:
                        self.logger.warning(f"Connection attempt {attempt + 1} to process {proc_id} failed: {e}")
                        time.sleep(retry_delay)
                        retry_delay = min(retry_delay * 1.5, 10.0)  # Exponential backoff
        
        # Connect in separate thread to avoid blocking
        thread = threading.Thread(target=connect_worker, daemon=True)
        thread.start()
    
    def send_message(self, message: NetworkMessage):
        """Queue a message for sending"""
        self.send_queue.put(message)
    
    def _process_send_queue(self):
        """Process messages from send queue"""
        while self.running:
            try:
                message = self.send_queue.get(timeout=1.0)
                self._send_message_direct(message)
                self.send_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error processing send queue: {e}")
    
    def _send_message_direct(self, message: NetworkMessage):
        """Send message directly to target process"""
        target_id = message.receiver_id
        
        # Check if we have connection
        if not self.connections_ready.get(target_id, False):
            self.logger.warning(f"No connection to process {target_id}, attempting reconnect")
            target_config = next(p for p in self.config["processes"] if p["id"] == target_id)
            self._connect_to_process(target_id, target_config["ip"], target_config["port"])
            
            # Wait a bit for connection
            time.sleep(0.1)
            if not self.connections_ready.get(target_id, False):
                self.logger.error(f"Failed to send message to process {target_id}: no connection")
                return
        
        try:
            with self.connection_locks[target_id]:
                sock = self.client_sockets.get(target_id)
                if sock is None:
                    raise Exception("No socket available")
                
                success = self._send_message_to_socket(sock, message.to_dict())
                if success:
                    self.stats["messages_sent"] += 1
                else:
                    raise Exception("Failed to send message")
                    
        except Exception as e:
            self.logger.error(f"Error sending message to process {target_id}: {e}")
            # Mark connection as not ready and attempt reconnect
            with self.connection_locks[target_id]:
                self.connections_ready[target_id] = False
                if target_id in self.client_sockets:
                    try:
                        self.client_sockets[target_id].close()
                    except:
                        pass
                    del self.client_sockets[target_id]
            
            # Attempt reconnect
            target_config = next(p for p in self.config["processes"] if p["id"] == target_id)
            self._connect_to_process(target_id, target_config["ip"], target_config["port"])
    
    def _send_message_to_socket(self, sock: socket.socket, data: Dict[str, Any]) -> bool:
        """Send message data to socket"""
        try:
            json_data = json.dumps(data)
            message = json_data.encode('utf-8')
            
            # Send message length first
            length = len(message)
            sock.sendall(length.to_bytes(4, byteorder='big'))
            
            # Send message data
            sock.sendall(message)
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending to socket: {e}")
            return False
    
    def _receive_message(self, sock: socket.socket) -> Optional[Dict[str, Any]]:
        """Receive message from socket"""
        try:
            # Receive message length first
            length_data = self._receive_exact(sock, 4)
            if length_data is None:
                return None
            
            length = int.from_bytes(length_data, byteorder='big')
            
            # Receive message data
            message_data = self._receive_exact(sock, length)
            if message_data is None:
                return None
            
            json_data = message_data.decode('utf-8')
            return json.loads(json_data)
            
        except Exception as e:
            self.logger.error(f"Error receiving from socket: {e}")
            return None
    
    def _receive_exact(self, sock: socket.socket, num_bytes: int) -> Optional[bytes]:
        """Receive exactly num_bytes from socket"""
        data = b''
        while len(data) < num_bytes:
            chunk = sock.recv(num_bytes - len(data))
            if not chunk:
                return None
            data += chunk
        return data
    
    def get_stats(self) -> Dict[str, Any]:
        """Get network statistics"""
        connected_processes = sum(1 for ready in self.connections_ready.values() if ready)
        return {
            **self.stats,
            "connected_processes": connected_processes,
            "total_processes": len(self.connections_ready),
            "send_queue_size": self.send_queue.qsize()
        }
    
    def get_connected_processes(self) -> List[int]:
        """Get list of connected process IDs"""
        return [proc_id for proc_id, ready in self.connections_ready.items() if ready]

if __name__ == "__main__":
    # Simple test
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python network_manager.py <process_id>")
        sys.exit(1)
    
    process_id = int(sys.argv[1])
    
    # Load config
    with open("config.json", "r") as f:
        config = json.load(f)
    
    def test_message_handler(message: NetworkMessage):
        print(f"Received: {message.payload} from {message.sender_id}")
    
    # Create and start network manager
    nm = NetworkManager(process_id, config, test_message_handler)
    nm.start()
    
    # Send test messages
    time.sleep(2)
    for target_id in range(15):
        if target_id != process_id:
            msg = NetworkMessage(
                sender_id=process_id,
                receiver_id=target_id,
                seq=1,
                vector_clock=[0] * 15,
                payload=f"Hello from {process_id} to {target_id}"
            )
            nm.send_message(msg)
    
    # Keep running
    try:
        while True:
            time.sleep(1)
            stats = nm.get_stats()
            print(f"Stats: {stats}")
    except KeyboardInterrupt:
        nm.stop()