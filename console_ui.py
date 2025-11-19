import threading
import time
import os
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
from enum import Enum
import logging

class UIMode(Enum):
    """UI display modes"""
    FULL = "full"          # Show all information
    COMPACT = "compact"    # Show summary only
    MINIMAL = "minimal"    # Show basic info only

class ConsoleUI:
    """
    Interactive console UI for SES distributed system monitoring
    Provides real-time display of system status with filtering and controls
    """
    
    def __init__(self, process_id: int, refresh_rate: float = 1.0):
        self.process_id = process_id
        self.refresh_rate = refresh_rate
        
        # UI state
        self.running = False
        self.paused = False
        self.mode = UIMode.FULL
        self.auto_refresh = True
        
        # Display settings
        self.show_buffer = True
        self.show_clock = True
        self.show_network = True
        self.show_statistics = True
        self.show_recent_events = True
        self.max_recent_events = 10
        
        # Event filtering
        self.event_filter = None  # None means show all events
        self.event_types = ["SEND", "RECEIVE", "DELIVER", "BUFFER", "CLOCK_UPDATE", "ERROR", "INFO"]
        
        # Data sources (to be injected)
        self.get_status_callback: Optional[Callable] = None
        self.get_buffer_callback: Optional[Callable] = None
        self.get_events_callback: Optional[Callable] = None
        self.get_clock_callback: Optional[Callable] = None
        
        # Threading
        self.display_thread = None
        self.input_thread = None
        self.lock = threading.RLock()
        
        # Terminal settings
        self.clear_command = "cls" if os.name == "nt" else "clear"
        self.terminal_width = 80
        self.terminal_height = 24
        
        # Statistics
        self.refresh_count = 0
        self.start_time = time.time()
        
        # Command history
        self.command_history = []
        self.max_history = 100
        
        try:
            # Try to get terminal size
            self.terminal_width, self.terminal_height = os.get_terminal_size()
        except:
            pass  # Use defaults
    
    def set_callbacks(self, get_status: Callable, get_buffer: Callable = None,
                     get_events: Callable = None, get_clock: Callable = None):
        """Set callback functions to get data from the process"""
        self.get_status_callback = get_status
        self.get_buffer_callback = get_buffer
        self.get_events_callback = get_events
        self.get_clock_callback = get_clock
    
    def start(self):
        """Start the console UI"""
        if self.running:
            return
        
        self.running = True
        self.start_time = time.time()
        
        # Start display thread
        if self.auto_refresh:
            self.display_thread = threading.Thread(target=self._display_worker, daemon=True)
            self.display_thread.start()
        
        # Start input thread
        self.input_thread = threading.Thread(target=self._input_worker, daemon=True)
        self.input_thread.start()
        
        # Initial display
        self.refresh_display()
    
    def stop(self):
        """Stop the console UI"""
        self.running = False
        
        if self.display_thread and self.display_thread.is_alive():
            self.display_thread.join(timeout=1.0)
        
        if self.input_thread and self.input_thread.is_alive():
            self.input_thread.join(timeout=1.0)
    
    def _display_worker(self):
        """Background worker for automatic display refresh"""
        while self.running:
            if not self.paused:
                try:
                    self.refresh_display()
                except Exception as e:
                    print(f"Error in display worker: {e}")
            
            time.sleep(self.refresh_rate)
    
    def _input_worker(self):
        """Background worker for handling user input"""
        while self.running:
            try:
                self._handle_input()
            except Exception as e:
                print(f"Error in input worker: {e}")
                time.sleep(0.1)
    
    def _handle_input(self):
        """Handle user input commands"""
        try:
            # Check for keyboard input (non-blocking)
            if sys.stdin.readable():
                command = input().strip().lower()
                if command:
                    self._process_command(command)
        except:
            time.sleep(0.1)
    
    def _process_command(self, command: str):
        """Process user command"""
        self.command_history.append(command)
        if len(self.command_history) > self.max_history:
            self.command_history.pop(0)
        
        if command in ["h", "help"]:
            self._show_help()
        elif command in ["q", "quit", "exit"]:
            self.running = False
        elif command in ["p", "pause"]:
            self.paused = not self.paused
            status = "paused" if self.paused else "resumed"
            print(f"\nDisplay {status}")
        elif command in ["r", "refresh"]:
            self.refresh_display()
        elif command in ["c", "clear"]:
            self._clear_screen()
        elif command in ["m", "mode"]:
            self._cycle_mode()
        elif command in ["f", "filter"]:
            self._cycle_filter()
        elif command in ["s", "status"]:
            self._show_detailed_status()
        elif command in ["b", "buffer"]:
            self._show_buffer_details()
        elif command in ["t", "clock", "time"]:
            self._show_clock_details()
        elif command in ["n", "network"]:
            self._show_network_details()
        elif command in ["e", "events"]:
            self._show_event_history()
        elif command.startswith("rate "):
            try:
                new_rate = float(command.split()[1])
                self.refresh_rate = max(0.1, min(10.0, new_rate))
                print(f"\nRefresh rate set to {self.refresh_rate}s")
            except:
                print("\nInvalid refresh rate. Use: rate <seconds>")
        else:
            print(f"\nUnknown command: {command}. Type 'h' for help.")
    
    def refresh_display(self):
        """Refresh the console display"""
        with self.lock:
            self.refresh_count += 1
            
            if self.mode == UIMode.FULL:
                self._display_full()
            elif self.mode == UIMode.COMPACT:
                self._display_compact()
            else:
                self._display_minimal()
    
    def _display_full(self):
        """Display full information"""
        self._clear_screen()
        
        # Header
        self._print_header()
        
        # Get data
        status = self._get_status_data()
        if not status:
            print("No status data available")
            return
        
        # Main sections
        self._print_process_info(status)
        
        if self.show_network:
            self._print_network_info(status.get("network_stats", {}))
        
        if self.show_statistics:
            self._print_statistics(status)
        
        if self.show_clock:
            self._print_clock_info(status.get("current_clock", []))
        
        if self.show_buffer:
            self._print_buffer_info(status.get("delivery_stats", {}).get("buffer_stats", {}))
        
        if self.show_recent_events:
            self._print_recent_events()
        
        # Footer
        self._print_footer()
    
    def _display_compact(self):
        """Display compact information"""
        self._clear_screen()
        
        # Header
        self._print_header()
        
        # Get data
        status = self._get_status_data()
        if not status:
            print("No status data available")
            return
        
        # Compact view
        print(f"Status: {'Paused' if status.get('paused') else 'Running'}")
        print(f"Uptime: {status.get('uptime_seconds', 0):.1f}s")
        print(f"Sent: {status.get('message_counts', {}).get('sent_total', 0)}")
        print(f"Received: {status.get('message_counts', {}).get('received_total', 0)}")
        
        network_stats = status.get("network_stats", {})
        print(f"Connected: {network_stats.get('connected_processes', 0)}/{network_stats.get('total_processes', 0)}")
        
        buffer_stats = status.get("delivery_stats", {}).get("buffer_stats", {})
        print(f"Buffer: {buffer_stats.get('current_buffer_size', 0)}")
        
        clock = status.get("current_clock", [])
        clock_str = f"[{','.join(map(str, clock[:5]))}{'...' if len(clock) > 5 else ''}]"
        print(f"Clock: {clock_str}")
        
        self._print_footer()
    
    def _display_minimal(self):
        """Display minimal information"""
        status = self._get_status_data()
        if not status:
            return
        
        uptime = status.get('uptime_seconds', 0)
        sent = status.get('message_counts', {}).get('sent_total', 0)
        received = status.get('message_counts', {}).get('received_total', 0)
        connected = status.get("network_stats", {}).get('connected_processes', 0)
        
        print(f"P{self.process_id} | {uptime:.0f}s | S:{sent} R:{received} C:{connected}")
    
    def _print_header(self):
        """Print UI header"""
        separator = "=" * self.terminal_width
        title = f" SES Process {self.process_id} Monitor "
        centered_title = title.center(self.terminal_width, "=")
        
        print(centered_title)
        print(f"Mode: {self.mode.value} | Auto-refresh: {self.auto_refresh} | Rate: {self.refresh_rate}s")
        print(f"Commands: h=help, q=quit, p=pause, r=refresh, m=mode, f=filter")
        print(separator[:self.terminal_width])
    
    def _print_footer(self):
        """Print UI footer"""
        separator = "-" * self.terminal_width
        uptime = time.time() - self.start_time
        footer = f"Refreshes: {self.refresh_count} | Uptime: {uptime:.1f}s | Last: {datetime.now().strftime('%H:%M:%S')}"
        
        print(separator[:self.terminal_width])
        print(footer)
    
    def _print_process_info(self, status: Dict[str, Any]):
        """Print basic process information"""
        print("\n📊 PROCESS STATUS:")
        print(f"  Process ID: {self.process_id}")
        print(f"  Running: {status.get('running', False)}")
        print(f"  Paused: {status.get('paused', False)}")
        print(f"  Uptime: {status.get('uptime_seconds', 0):.2f} seconds")
    
    def _print_network_info(self, network_stats: Dict[str, Any]):
        """Print network status information"""
        print("\n🌐 NETWORK STATUS:")
        connected = network_stats.get('connected_processes', 0)
        total = network_stats.get('total_processes', 0)
        print(f"  Connected: {connected}/{total} processes")
        print(f"  Messages Sent: {network_stats.get('messages_sent', 0)}")
        print(f"  Messages Received: {network_stats.get('messages_received', 0)}")
        print(f"  Connection Errors: {network_stats.get('connection_errors', 0)}")
        print(f"  Send Queue Size: {network_stats.get('send_queue_size', 0)}")
    
    def _print_statistics(self, status: Dict[str, Any]):
        """Print delivery statistics"""
        print("\n📈 DELIVERY STATISTICS:")
        message_counts = status.get('message_counts', {})
        delivery_stats = status.get('delivery_stats', {}).get('delivery_stats', {})
        
        print(f"  Total Sent: {message_counts.get('sent_total', 0)}")
        print(f"  Total Received: {message_counts.get('received_total', 0)}")
        print(f"  Delivered Immediate: {delivery_stats.get('messages_delivered_immediate', 0)}")
        print(f"  Delivered from Buffer: {delivery_stats.get('messages_delivered_buffered', 0)}")
        print(f"  Cascade Deliveries: {delivery_stats.get('cascade_deliveries', 0)}")
        print(f"  Duplicates Rejected: {delivery_stats.get('duplicate_messages_rejected', 0)}")
    
    def _print_clock_info(self, clock: List[int]):
        """Print vector clock information"""
        print("\n🕐 VECTOR CLOCK:")
        if clock:
            # Show clock in chunks for readability
            chunk_size = 10
            for i in range(0, len(clock), chunk_size):
                chunk = clock[i:i+chunk_size]
                chunk_str = ', '.join(f"{i+j}:{val}" for j, val in enumerate(chunk))
                print(f"  P{i}-P{i+len(chunk)-1}: [{chunk_str}]")
        else:
            print("  Clock not available")
    
    def _print_buffer_info(self, buffer_stats: Dict[str, Any]):
        """Print buffer status information"""
        print("\n📦 BUFFER STATUS:")
        current_size = buffer_stats.get('current_buffer_size', 0)
        max_size = buffer_stats.get('max_buffer_size', 0)
        utilization = buffer_stats.get('buffer_utilization', 0.0) * 100
        
        print(f"  Current Size: {current_size}")
        print(f"  Max Size: {max_size}")
        print(f"  Utilization: {utilization:.1f}%")
        print(f"  Messages Buffered: {buffer_stats.get('messages_buffered', 0)}")
        print(f"  Messages from Buffer: {buffer_stats.get('messages_delivered_from_buffer', 0)}")
        print(f"  Average Buffer Time: {buffer_stats.get('average_buffer_time', 0.0):.3f}s")
    
    def _print_recent_events(self):
        """Print recent events"""
        if not self.get_events_callback:
            return
        
        print(f"\n📝 RECENT EVENTS (last {self.max_recent_events}):")
        try:
            events = self.get_events_callback(self.max_recent_events)
            if events:
                for event in events[-self.max_recent_events:]:
                    timestamp = event.get('timestamp', '')[:19]  # Remove microseconds
                    event_type = event.get('event_type', 'UNKNOWN')
                    message = event.get('message', '')
                    
                    # Apply filter
                    if self.event_filter and event_type != self.event_filter:
                        continue
                    
                    # Truncate long messages
                    if len(message) > 60:
                        message = message[:57] + "..."
                    
                    print(f"  {timestamp} {event_type:12} {message}")
            else:
                print("  No recent events")
        except Exception as e:
            print(f"  Error loading events: {e}")
    
    def _get_status_data(self) -> Optional[Dict[str, Any]]:
        """Get status data from callback"""
        if self.get_status_callback:
            try:
                return self.get_status_callback()
            except Exception as e:
                return {"error": str(e)}
        return None
    
    def _clear_screen(self):
        """Clear the terminal screen"""
        os.system(self.clear_command)
    
    def _cycle_mode(self):
        """Cycle through display modes"""
        modes = [UIMode.FULL, UIMode.COMPACT, UIMode.MINIMAL]
        current_index = modes.index(self.mode)
        next_index = (current_index + 1) % len(modes)
        self.mode = modes[next_index]
        print(f"\nDisplay mode: {self.mode.value}")
    
    def _cycle_filter(self):
        """Cycle through event filters"""
        filters = [None] + self.event_types
        try:
            current_index = filters.index(self.event_filter)
        except ValueError:
            current_index = 0
        
        next_index = (current_index + 1) % len(filters)
        self.event_filter = filters[next_index]
        filter_name = self.event_filter or "ALL"
        print(f"\nEvent filter: {filter_name}")
    
    def _show_help(self):
        """Show help information"""
        help_text = """
📖 SES CONSOLE COMMANDS:
  h, help     - Show this help
  q, quit     - Exit the program
  p, pause    - Pause/resume display updates
  r, refresh  - Force refresh display
  c, clear    - Clear screen
  m, mode     - Cycle display modes (full/compact/minimal)
  f, filter   - Cycle event type filters
  s, status   - Show detailed status
  b, buffer   - Show buffer details
  t, clock    - Show clock details
  n, network  - Show network details
  e, events   - Show event history
  rate <num>  - Set refresh rate (0.1-10.0 seconds)

🎛️  DISPLAY MODES:
  full        - Show all information (default)
  compact     - Show summary information
  minimal     - Show basic status line

📋 EVENT FILTERS:
  ALL         - Show all events (default)
  SEND        - Show only send events
  RECEIVE     - Show only receive events
  DELIVER     - Show only delivery events
  BUFFER      - Show only buffer events
  CLOCK_UPDATE- Show only clock updates
  ERROR       - Show only errors
  INFO        - Show only info messages
        """
        print(help_text)
        input("\nPress Enter to continue...")
    
    def _show_detailed_status(self):
        """Show detailed status information"""
        status = self._get_status_data()
        if status:
            print("\n📊 DETAILED STATUS:")
            self._print_dict(status, indent=2)
        input("\nPress Enter to continue...")
    
    def _show_buffer_details(self):
        """Show detailed buffer information"""
        if self.get_buffer_callback:
            try:
                buffer_data = self.get_buffer_callback()
                print("\n📦 BUFFER DETAILS:")
                self._print_dict(buffer_data, indent=2)
            except Exception as e:
                print(f"\nError getting buffer data: {e}")
        else:
            print("\nBuffer data not available")
        input("\nPress Enter to continue...")
    
    def _show_clock_details(self):
        """Show detailed clock information"""
        if self.get_clock_callback:
            try:
                clock_data = self.get_clock_callback()
                print("\n🕐 CLOCK DETAILS:")
                self._print_dict(clock_data, indent=2)
            except Exception as e:
                print(f"\nError getting clock data: {e}")
        else:
            print("\nClock data not available")
        input("\nPress Enter to continue...")
    
    def _show_network_details(self):
        """Show detailed network information"""
        status = self._get_status_data()
        if status:
            network_stats = status.get("network_stats", {})
            print("\n🌐 NETWORK DETAILS:")
            self._print_dict(network_stats, indent=2)
        input("\nPress Enter to continue...")
    
    def _show_event_history(self):
        """Show extended event history"""
        if self.get_events_callback:
            try:
                events = self.get_events_callback(50)  # Get last 50 events
                print("\n📝 EVENT HISTORY:")
                for event in events:
                    timestamp = event.get('timestamp', '')[:19]
                    event_type = event.get('event_type', 'UNKNOWN')
                    message = event.get('message', '')
                    print(f"  {timestamp} {event_type:12} {message}")
            except Exception as e:
                print(f"\nError getting events: {e}")
        else:
            print("\nEvent data not available")
        input("\nPress Enter to continue...")
    
    def _print_dict(self, data: Dict[str, Any], indent: int = 0):
        """Print dictionary data in a formatted way"""
        prefix = "  " * indent
        for key, value in data.items():
            if isinstance(value, dict):
                print(f"{prefix}{key}:")
                self._print_dict(value, indent + 1)
            elif isinstance(value, list):
                if len(value) <= 10:  # Show short lists
                    print(f"{prefix}{key}: {value}")
                else:  # Truncate long lists
                    print(f"{prefix}{key}: [{', '.join(map(str, value[:5]))} ... +{len(value)-5} more]")
            else:
                print(f"{prefix}{key}: {value}")

# Test function
if __name__ == "__main__":
    # Test console UI
    def mock_get_status():
        return {
            "process_id": 0,
            "running": True,
            "paused": False,
            "uptime_seconds": 123.45,
            "current_clock": [1, 2, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            "message_counts": {
                "sent_total": 50,
                "received_total": 45
            },
            "network_stats": {
                "connected_processes": 14,
                "total_processes": 14,
                "messages_sent": 50,
                "messages_received": 45
            },
            "delivery_stats": {
                "delivery_stats": {
                    "messages_delivered_immediate": 40,
                    "messages_delivered_buffered": 5
                },
                "buffer_stats": {
                    "current_buffer_size": 3,
                    "max_buffer_size": 100
                }
            }
        }
    
    def mock_get_events(count):
        return [
            {"timestamp": "2025-01-01T12:00:00", "event_type": "SEND", "message": "Sent message to P1"},
            {"timestamp": "2025-01-01T12:00:01", "event_type": "RECEIVE", "message": "Received from P2"},
            {"timestamp": "2025-01-01T12:00:02", "event_type": "DELIVER", "message": "Delivered message from P2"},
        ]
    
    ui = ConsoleUI(0)
    ui.set_callbacks(mock_get_status, get_events=mock_get_events)
    
    print("Testing Console UI - press 'q' to quit")
    ui.start()
    
    try:
        while ui.running:
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    
    ui.stop()
