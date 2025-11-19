import threading
import sys
import time
import select
import tty
import termios
from typing import Callable, Dict, Any, Optional
import logging

class KeyboardControl:
    """
    Advanced keyboard control system for SES process monitoring
    Provides real-time keyboard input handling with various control commands
    """
    
    def __init__(self, process_node):
        self.process_node = process_node
        self.logger = logging.getLogger(f"KeyboardControl-{process_node.node_id}")
        
        # Control state
        self.running = False
        self.listener_thread = None
        self.paused = threading.Event()
        self.paused.set()  # Initially not paused
        
        # Command callbacks
        self.commands = {
            'h': self._show_help,
            'help': self._show_help,
            '?': self._show_help,
            
            'q': self._quit,
            'quit': self._quit,
            'exit': self._quit,
            
            'p': self._toggle_pause,
            'pause': self._toggle_pause,
            'resume': self._toggle_pause,
            
            's': self._show_status,
            'status': self._show_status,
            'stat': self._show_status,
            
            'b': self._show_buffer,
            'buffer': self._show_buffer,
            'buf': self._show_buffer,
            
            't': self._show_timestamp,
            'time': self._show_timestamp,
            'clock': self._show_timestamp,
            'timestamp': self._show_timestamp,
            
            'n': self._show_network,
            'network': self._show_network,
            'net': self._show_network,
            
            'e': self._show_events,
            'events': self._show_events,
            'log': self._show_events,
            
            'c': self._clear_screen,
            'clear': self._clear_screen,
            'cls': self._clear_screen,
            
            'r': self._refresh,
            'refresh': self._refresh,
            
            'd': self._show_delivery_stats,
            'delivery': self._show_delivery_stats,
            'stats': self._show_delivery_stats,
            
            'x': self._export_logs,
            'export': self._export_logs,
            
            'reset': self._reset_stats,
            'test': self._run_test
        }
        
        # State tracking
        self.command_count = 0
        self.last_command_time = time.time()
        
        # Terminal settings (Unix/Linux)
        self.old_settings = None
        
    def start(self):
        """Start keyboard listener"""
        if self.running:
            return
        
        self.running = True
        self.listener_thread = threading.Thread(target=self._listen_worker, daemon=True)
        self.listener_thread.start()
        
        self.logger.info("Keyboard control started")
        self._show_welcome_message()
    
    def stop(self):
        """Stop keyboard listener"""
        self.running = False
        
        if self.listener_thread and self.listener_thread.is_alive():
            self.listener_thread.join(timeout=1.0)
        
        # Restore terminal settings
        if self.old_settings:
            try:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)
            except:
                pass
        
        self.logger.info("Keyboard control stopped")
    
    def _listen_worker(self):
        """Main keyboard listener worker"""
        try:
            # Setup terminal for non-blocking input (Unix/Linux)
            if sys.platform != 'win32':
                self._setup_unix_terminal()
            
            while self.running:
                try:
                    if sys.platform == 'win32':
                        self._handle_windows_input()
                    else:
                        self._handle_unix_input()
                except Exception as e:
                    self.logger.error(f"Error in keyboard listener: {e}")
                    time.sleep(0.1)
                    
        except Exception as e:
            self.logger.error(f"Fatal error in keyboard listener: {e}")
        finally:
            if self.old_settings:
                try:
                    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)
                except:
                    pass
    
    def _setup_unix_terminal(self):
        """Setup Unix/Linux terminal for non-blocking input"""
        try:
            self.old_settings = termios.tcgetattr(sys.stdin)
            tty.setraw(sys.stdin.fileno())
        except:
            pass
    
    def _handle_windows_input(self):
        """Handle keyboard input on Windows"""
        try:
            import msvcrt
            if msvcrt.kbhit():
                key = msvcrt.getwch()
                if key == '\r':  # Enter key
                    command = input("\nEnter command: ").strip().lower()
                    self._process_command(command)
                elif ord(key) == 27:  # Escape key
                    print("\nPress 'q' to quit")
                else:
                    # Single character commands
                    self._process_command(key.lower())
            else:
                time.sleep(0.1)
        except Exception as e:
            self.logger.error(f"Windows input error: {e}")
            time.sleep(0.1)
    
    def _handle_unix_input(self):
        """Handle keyboard input on Unix/Linux"""
        try:
            # Check if input is available
            if select.select([sys.stdin], [], [], 0.1)[0]:
                key = sys.stdin.read(1)
                
                if key == '\n' or key == '\r':
                    # Enter pressed - get full command
                    print("\nEnter command: ", end='', flush=True)
                    # Restore normal terminal mode temporarily
                    if self.old_settings:
                        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)
                    
                    try:
                        command = input().strip().lower()
                        self._process_command(command)
                    except EOFError:
                        pass
                    
                    # Set back to raw mode
                    tty.setraw(sys.stdin.fileno())
                    
                elif ord(key) == 27:  # Escape key
                    print("\nPress 'q' to quit")
                elif key.isprintable():
                    # Single character command
                    self._process_command(key.lower())
            else:
                time.sleep(0.1)
                
        except Exception as e:
            self.logger.error(f"Unix input error: {e}")
            time.sleep(0.1)
    
    def _process_command(self, command: str):
        """Process a keyboard command"""
        if not command:
            return
        
        self.command_count += 1
        self.last_command_time = time.time()
        
        # Handle command
        if command in self.commands:
            try:
                self.commands[command]()
            except Exception as e:
                print(f"\nError executing command '{command}': {e}")
                self.logger.error(f"Command error: {e}")
        else:
            print(f"\nUnknown command: '{command}'. Press 'h' for help.")
    
    def _show_welcome_message(self):
        """Show initial welcome message"""
        print("\n" + "="*60)
        print(f"🎮 SES Process {self.process_node.node_id} - Keyboard Controls Active")
        print("="*60)
        print("Quick Commands: h=help, q=quit, p=pause, s=status, b=buffer")
        print("Press ENTER for full command mode, or single keys for quick actions")
        print("="*60 + "\n")
    
    def _show_help(self):
        """Show help information"""
        help_text = f"""
🎮 KEYBOARD CONTROLS - Process {self.process_node.node_id}
{'='*60}

📋 QUICK COMMANDS (single key):
  h, ?          - Show this help
  q             - Quit gracefully
  p             - Toggle pause/resume message sending
  s             - Show current status
  b             - Show buffer state
  t             - Show current timestamps/clocks
  n             - Show network connections
  e             - Show recent events
  c             - Clear screen
  r             - Refresh display
  d             - Show delivery statistics

📝 FULL COMMANDS (press ENTER first):
  help          - Show this help
  quit, exit    - Quit gracefully
  pause, resume - Toggle message sending
  status, stat  - Show detailed status
  buffer, buf   - Show buffer details
  time, clock   - Show vector clock details
  network, net  - Show network status
  events, log   - Show event history
  clear, cls    - Clear screen
  refresh       - Refresh display
  delivery      - Show delivery statistics
  export        - Export logs
  reset         - Reset statistics
  test          - Run connectivity test

🔧 PROCESS CONTROLS:
  Current State: {'Paused' if self.process_node.paused else 'Running'}
  Message Sending: {'Disabled' if self.process_node.paused else 'Active'}
  
📊 STATISTICS:
  Commands Executed: {self.command_count}
  Uptime: {time.time() - self.process_node.stats.get('start_time', time.time()):.1f}s

Press any key to continue...
"""
        print(help_text)
    
    def _quit(self):
        """Quit the application gracefully"""
        print(f"\n🛑 Shutting down Process {self.process_node.node_id}...")
        self.running = False
        self.process_node.stop()
        sys.exit(0)
    
    def _toggle_pause(self):
        """Toggle pause/resume message sending"""
        if self.process_node.paused:
            self.process_node.resume_sending()
            print(f"\n▶️  Process {self.process_node.node_id} message sending RESUMED")
        else:
            self.process_node.pause_sending()
            print(f"\n⏸️  Process {self.process_node.node_id} message sending PAUSED")
    
    def _show_status(self):
        """Show current process status"""
        print(f"\n📊 Process {self.process_node.node_id} Status:")
        print("-" * 40)
        
        status = self.process_node.get_status()
        
        print(f"State: {'🔴 Paused' if status.get('paused') else '🟢 Running'}")
        print(f"Uptime: {status.get('uptime_seconds', 0):.2f} seconds")
        
        msg_counts = status.get('message_counts', {})
        print(f"Messages Sent: {msg_counts.get('sent_total', 0)}")
        print(f"Messages Received: {msg_counts.get('received_total', 0)}")
        
        network_stats = status.get('network_stats', {})
        connected = network_stats.get('connected_processes', 0)
        total = network_stats.get('total_processes', 0)
        print(f"Network: {connected}/{total} processes connected")
        
        print(f"Current Clock: {status.get('current_clock', [])}")
        print()
    
    def _show_buffer(self):
        """Show buffer state"""
        print(f"\n📦 Buffer State - Process {self.process_node.node_id}:")
        print("-" * 40)
        
        try:
            buffer_summary = self.process_node.delivery_engine.buffer_manager.get_buffer_summary()
            print(buffer_summary)
            
            buffer_stats = self.process_node.delivery_engine.buffer_manager.get_stats()
            print(f"Buffer Statistics:")
            print(f"  Current Size: {buffer_stats.get('current_buffer_size', 0)}")
            print(f"  Messages Buffered: {buffer_stats.get('messages_buffered', 0)}")
            print(f"  Average Buffer Time: {buffer_stats.get('average_buffer_time', 0):.3f}s")
            
        except Exception as e:
            print(f"Error getting buffer info: {e}")
        print()
    
    def _show_timestamp(self):
        """Show current timestamps and clocks"""
        print(f"\n🕐 Timestamps - Process {self.process_node.node_id}:")
        print("-" * 40)
        
        try:
            current_clock = self.process_node.delivery_engine.get_current_clock()
            print(f"Vector Clock: {current_clock}")
            
            clock_stats = self.process_node.delivery_engine.clock.get_stats()
            print(f"Clock Statistics:")
            print(f"  Event Count: {clock_stats.get('event_count', 0)}")
            print(f"  Max Clock Value: {clock_stats.get('max_clock_value', 0)}")
            print(f"  Total Events Seen: {clock_stats.get('total_events_seen', 0)}")
            
        except Exception as e:
            print(f"Error getting clock info: {e}")
        print()
    
    def _show_network(self):
        """Show network connection status"""
        print(f"\n🌐 Network Status - Process {self.process_node.node_id}:")
        print("-" * 40)
        
        try:
            network_stats = self.process_node.network_manager.get_stats()
            connected_processes = self.process_node.network_manager.get_connected_processes()
            
            print(f"Connected to processes: {connected_processes}")
            print(f"Total connections: {len(connected_processes)}/{len(self.process_node.other_process_ids)}")
            print(f"Messages sent: {network_stats.get('messages_sent', 0)}")
            print(f"Messages received: {network_stats.get('messages_received', 0)}")
            print(f"Connection errors: {network_stats.get('connection_errors', 0)}")
            print(f"Send queue size: {network_stats.get('send_queue_size', 0)}")
            
        except Exception as e:
            print(f"Error getting network info: {e}")
        print()
    
    def _show_events(self):
        """Show recent events"""
        print(f"\n📝 Recent Events - Process {self.process_node.node_id}:")
        print("-" * 40)
        
        try:
            # Show last 10 delivery events
            recent_deliveries = self.process_node.delivery_engine.get_recent_deliveries(10)
            
            if recent_deliveries:
                print("Recent Deliveries:")
                for delivery in recent_deliveries:
                    buffer_info = " (buffered)" if delivery['was_buffered'] else " (immediate)"
                    print(f"  P{delivery['sender_id']}#{delivery['seq']}{buffer_info}")
            else:
                print("No recent deliveries")
                
        except Exception as e:
            print(f"Error getting events: {e}")
        print()
    
    def _clear_screen(self):
        """Clear the screen"""
        import os
        os.system('cls' if os.name == 'nt' else 'clear')
        self._show_welcome_message()
    
    def _refresh(self):
        """Refresh and show current status"""
        print(f"\n🔄 Refreshing Process {self.process_node.node_id}...")
        self._show_status()
    
    def _show_delivery_stats(self):
        """Show detailed delivery statistics"""
        print(f"\n📈 Delivery Statistics - Process {self.process_node.node_id}:")
        print("-" * 40)
        
        try:
            stats = self.process_node.delivery_engine.get_delivery_stats()
            delivery_stats = stats.get('delivery_stats', {})
            
            print(f"Total Delivered: {stats.get('total_delivered', 0)}")
            print(f"Immediate Deliveries: {delivery_stats.get('messages_delivered_immediate', 0)}")
            print(f"Buffered Deliveries: {delivery_stats.get('messages_delivered_buffered', 0)}")
            print(f"Cascade Deliveries: {delivery_stats.get('cascade_deliveries', 0)}")
            print(f"Duplicates Rejected: {delivery_stats.get('duplicate_messages_rejected', 0)}")
            print(f"Average Buffer Time: {stats.get('average_buffer_time', 0):.3f}s")
            
        except Exception as e:
            print(f"Error getting delivery stats: {e}")
        print()
    
    def _export_logs(self):
        """Export logs to file"""
        print(f"\n💾 Exporting logs for Process {self.process_node.node_id}...")
        
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"export_p{self.process_node.node_id}_{timestamp}.json"
            
            # This would export logs if logger was integrated
            print(f"Logs would be exported to: {filename}")
            print("(Export functionality requires logger integration)")
            
        except Exception as e:
            print(f"Error exporting logs: {e}")
        print()
    
    def _reset_stats(self):
        """Reset statistics"""
        print(f"\n🔄 Resetting statistics for Process {self.process_node.node_id}...")
        
        try:
            self.process_node.delivery_engine.reset_stats()
            print("Statistics reset successfully")
            
        except Exception as e:
            print(f"Error resetting stats: {e}")
        print()
    
    def _run_test(self):
        """Run connectivity test"""
        print(f"\n🧪 Running connectivity test for Process {self.process_node.node_id}...")
        
        try:
            connected = self.process_node.network_manager.get_connected_processes()
            total = len(self.process_node.other_process_ids)
            
            print(f"Connected to {len(connected)}/{total} processes")
            
            if len(connected) == total:
                print("✅ All connections active - Test PASSED")
            elif len(connected) >= total * 0.8:
                print("⚠️  Most connections active - Test PARTIAL")
            else:
                print("❌ Many connections missing - Test FAILED")
                
        except Exception as e:
            print(f"Error running test: {e}")
        print()
    
    def is_paused(self):
        """Check if process is paused"""
        return not self.paused.is_set()

# Test function
if __name__ == "__main__":
    # Mock process node for testing
    class MockProcessNode:
        def __init__(self):
            self.node_id = 0
            self.paused = False
            self.other_process_ids = list(range(1, 15))
            self.stats = {'start_time': time.time()}
        
        def pause_sending(self):
            self.paused = True
        
        def resume_sending(self):
            self.paused = False
        
        def stop(self):
            print("Mock process stopped")
        
        def get_status(self):
            return {
                'paused': self.paused,
                'uptime_seconds': 123.45,
                'message_counts': {'sent_total': 50, 'received_total': 45},
                'network_stats': {'connected_processes': 14, 'total_processes': 14},
                'current_clock': [1, 2, 3, 0, 0]
            }
    
    mock_node = MockProcessNode()
    keyboard = KeyboardControl(mock_node)
    
    print("Testing Keyboard Control - press 'q' to quit")
    keyboard.start()
    
    try:
        while keyboard.running:
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    
    keyboard.stop()
