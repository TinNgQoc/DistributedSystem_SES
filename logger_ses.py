import threading
import time
import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum

class EventType(Enum):
    """Types of events that can be logged"""
    SEND = "SEND"
    RECEIVE = "RECEIVE"
    DELIVER = "DELIVER"
    BUFFER = "BUFFER"
    CLOCK_UPDATE = "CLOCK_UPDATE"
    NETWORK_CONNECT = "NETWORK_CONNECT"
    NETWORK_DISCONNECT = "NETWORK_DISCONNECT"
    ERROR = "ERROR"
    INFO = "INFO"
    DEBUG = "DEBUG"

class LogEntry:
    """Represents a single log entry"""
    
    def __init__(self, event_type: EventType, message: str, 
                 process_id: int, timestamp: Optional[str] = None,
                 vector_clock: Optional[List[int]] = None,
                 extra_data: Optional[Dict[str, Any]] = None):
        self.event_type = event_type
        self.message = message
        self.process_id = process_id
        self.timestamp = timestamp or datetime.now().isoformat()
        self.vector_clock = vector_clock.copy() if vector_clock else None
        self.extra_data = extra_data or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "timestamp": self.timestamp,
            "process_id": self.process_id,
            "event_type": self.event_type.value,
            "message": self.message,
            "vector_clock": self.vector_clock,
            "extra_data": self.extra_data
        }
    
    def to_formatted_string(self) -> str:
        """Convert to human-readable string"""
        clock_str = f"[{','.join(map(str, self.vector_clock))}]" if self.vector_clock else "[N/A]"
        return f"[{self.timestamp}] P{self.process_id} {clock_str} {self.event_type.value}: {self.message}"

class LoggerSES:
    """
    Comprehensive logging system for SES distributed system
    Supports multiple output formats and real-time monitoring
    """
    
    def __init__(self, process_id: int, log_dir: str = "logs"):
        self.process_id = process_id
        self.log_dir = log_dir
        self.log_entries: List[LogEntry] = []
        self.lock = threading.RLock()
        
        # File paths
        os.makedirs(log_dir, exist_ok=True)
        self.text_log_path = os.path.join(log_dir, f"pid_{process_id}.txt")
        self.json_log_path = os.path.join(log_dir, f"pid_{process_id}.json")
        self.events_log_path = os.path.join(log_dir, f"events_{process_id}.log")
        
        # File handles
        self.text_file = None
        self.json_file = None
        self.events_file = None
        
        # Buffer settings
        self.buffer = []
        self.buffer_size = 100  # Flush every 100 entries
        self.last_flush_time = time.time()
        self.flush_interval = 5.0  # Flush every 5 seconds
        
        # Statistics
        self.stats = {
            "total_entries": 0,
            "entries_by_type": {event_type.value: 0 for event_type in EventType},
            "start_time": time.time()
        }
        
        # Background flush thread
        self.flush_thread = None
        self.running = False
        
        # Event listeners
        self.event_listeners = []  # List of callback functions
        
        self._open_files()
        self._start_flush_thread()
    
    def _open_files(self):
        """Open log files for writing"""
        try:
            # Clear existing files
            self.text_file = open(self.text_log_path, 'w', encoding='utf-8')
            self.events_file = open(self.events_log_path, 'w', encoding='utf-8')
            
            # Write headers
            self.text_file.write(f"=== SES Process {self.process_id} Log ===\n")
            self.text_file.write(f"Started at: {datetime.now().isoformat()}\n\n")
            self.text_file.flush()
            
            # JSON file will be written as array
            self.json_file = open(self.json_log_path, 'w', encoding='utf-8')
            self.json_file.write('[\n')
            
        except Exception as e:
            print(f"Error opening log files: {e}")
    
    def _start_flush_thread(self):
        """Start background thread for periodic flushing"""
        self.running = True
        self.flush_thread = threading.Thread(target=self._flush_worker, daemon=True)
        self.flush_thread.start()
    
    def _flush_worker(self):
        """Background worker for periodic flushing"""
        while self.running:
            try:
                time.sleep(self.flush_interval)
                current_time = time.time()
                
                # Check if it's time to flush
                if (current_time - self.last_flush_time) >= self.flush_interval:
                    self._flush()
                    
            except Exception as e:
                print(f"Error in flush worker: {e}")
    
    def log_event(self, event_type: EventType, message: str, 
                  vector_clock: Optional[List[int]] = None,
                  extra_data: Optional[Dict[str, Any]] = None):
        """Log an event"""
        with self.lock:
            # Create log entry
            entry = LogEntry(
                event_type=event_type,
                message=message,
                process_id=self.process_id,
                vector_clock=vector_clock,
                extra_data=extra_data
            )
            
            # Add to memory buffer
            self.log_entries.append(entry)
            self.buffer.append(entry)
            
            # Update statistics
            self.stats["total_entries"] += 1
            self.stats["entries_by_type"][event_type.value] += 1
            
            # Notify listeners
            for listener in self.event_listeners:
                try:
                    listener(entry)
                except Exception as e:
                    print(f"Error in event listener: {e}")
            
            # Check if buffer needs flushing
            if len(self.buffer) >= self.buffer_size:
                self._flush()
    
    def log_send(self, target_id: int, seq: int, vector_clock: List[int], payload: str = ""):
        """Log a message send event"""
        message = f"SENT to P{target_id} seq={seq} payload='{payload}'"
        self.log_event(EventType.SEND, message, vector_clock, {
            "target_id": target_id,
            "seq": seq,
            "payload": payload
        })
    
    def log_receive(self, sender_id: int, seq: int, vector_clock: List[int], payload: str = ""):
        """Log a message receive event"""
        message = f"RECEIVED from P{sender_id} seq={seq} payload='{payload}'"
        self.log_event(EventType.RECEIVE, message, vector_clock, {
            "sender_id": sender_id,
            "seq": seq,
            "payload": payload
        })
    
    def log_deliver(self, sender_id: int, seq: int, vector_clock: List[int], 
                   was_buffered: bool = False, buffer_time: float = 0.0):
        """Log a message delivery event"""
        buffer_info = f" (buffered {buffer_time:.3f}s)" if was_buffered else " (immediate)"
        message = f"DELIVERED from P{sender_id} seq={seq}{buffer_info}"
        self.log_event(EventType.DELIVER, message, vector_clock, {
            "sender_id": sender_id,
            "seq": seq,
            "was_buffered": was_buffered,
            "buffer_time": buffer_time
        })
    
    def log_buffer(self, sender_id: int, seq: int, vector_clock: List[int], reason: str = ""):
        """Log a message buffering event"""
        message = f"BUFFERED from P{sender_id} seq={seq} reason='{reason}'"
        self.log_event(EventType.BUFFER, message, vector_clock, {
            "sender_id": sender_id,
            "seq": seq,
            "reason": reason
        })
    
    def log_clock_update(self, old_clock: List[int], new_clock: List[int], reason: str = ""):
        """Log a vector clock update"""
        message = f"CLOCK UPDATE {old_clock} -> {new_clock} reason='{reason}'"
        self.log_event(EventType.CLOCK_UPDATE, message, new_clock, {
            "old_clock": old_clock,
            "new_clock": new_clock,
            "reason": reason
        })
    
    def log_network_event(self, event_type: EventType, peer_id: int, details: str = ""):
        """Log a network connection event"""
        message = f"{event_type.value} P{peer_id} {details}"
        self.log_event(event_type, message, extra_data={"peer_id": peer_id, "details": details})
    
    def log_error(self, error_message: str, exception: Optional[Exception] = None):
        """Log an error event"""
        if exception:
            message = f"ERROR: {error_message} - {str(exception)}"
            extra_data = {
                "exception_type": type(exception).__name__,
                "exception_str": str(exception)
            }
        else:
            message = f"ERROR: {error_message}"
            extra_data = {}
        
        self.log_event(EventType.ERROR, message, extra_data=extra_data)
    
    def log_info(self, info_message: str, **kwargs):
        """Log an info event"""
        message = f"INFO: {info_message}"
        self.log_event(EventType.INFO, message, extra_data=kwargs)
    
    def log_debug(self, debug_message: str, **kwargs):
        """Log a debug event"""
        message = f"DEBUG: {debug_message}"
        self.log_event(EventType.DEBUG, message, extra_data=kwargs)
    
    def _flush(self):
        """Flush buffered log entries to files"""
        if not self.buffer:
            return
        
        with self.lock:
            try:
                for entry in self.buffer:
                    # Write to text file
                    self.text_file.write(entry.to_formatted_string() + '\n')
                    
                    # Write to events file (structured format)
                    event_line = f"{entry.timestamp}\t{entry.event_type.value}\t{entry.message}\n"
                    self.events_file.write(event_line)
                    
                    # Write to JSON file
                    json_line = json.dumps(entry.to_dict(), ensure_ascii=False)
                    if self.stats["total_entries"] > len(self.buffer):  # Not first entries
                        self.json_file.write(',\n')
                    self.json_file.write(json_line)
                
                # Flush all files
                self.text_file.flush()
                self.events_file.flush()
                self.json_file.flush()
                
                # Clear buffer
                self.buffer.clear()
                self.last_flush_time = time.time()
                
            except Exception as e:
                print(f"Error flushing logs: {e}")
    
    def add_event_listener(self, callback: callable):
        """Add an event listener for real-time monitoring"""
        self.event_listeners.append(callback)
    
    def remove_event_listener(self, callback: callable):
        """Remove an event listener"""
        if callback in self.event_listeners:
            self.event_listeners.remove(callback)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get logging statistics"""
        with self.lock:
            uptime = time.time() - self.stats["start_time"]
            return {
                "process_id": self.process_id,
                "total_entries": self.stats["total_entries"],
                "entries_by_type": self.stats["entries_by_type"].copy(),
                "uptime_seconds": uptime,
                "entries_per_second": self.stats["total_entries"] / max(uptime, 1.0),
                "buffer_size": len(self.buffer),
                "files": {
                    "text_log": self.text_log_path,
                    "json_log": self.json_log_path,
                    "events_log": self.events_log_path
                }
            }
    
    def get_recent_entries(self, count: int = 10, 
                          event_filter: Optional[EventType] = None) -> List[LogEntry]:
        """Get recent log entries, optionally filtered by event type"""
        with self.lock:
            entries = self.log_entries
            
            if event_filter:
                entries = [e for e in entries if e.event_type == event_filter]
            
            return entries[-count:] if entries else []
    
    def search_entries(self, query: str, max_results: int = 100) -> List[LogEntry]:
        """Search log entries by message content"""
        with self.lock:
            query_lower = query.lower()
            results = []
            
            for entry in self.log_entries:
                if query_lower in entry.message.lower():
                    results.append(entry)
                    if len(results) >= max_results:
                        break
            
            return results
    
    def export_logs(self, output_path: str, format: str = "json"):
        """Export all logs to a file"""
        with self.lock:
            if format.lower() == "json":
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump([entry.to_dict() for entry in self.log_entries], f, indent=2)
            elif format.lower() == "text":
                with open(output_path, 'w', encoding='utf-8') as f:
                    for entry in self.log_entries:
                        f.write(entry.to_formatted_string() + '\n')
            else:
                raise ValueError(f"Unsupported format: {format}")
    
    def close(self):
        """Close the logger and flush remaining data"""
        self.running = False
        
        # Flush remaining data
        self._flush()
        
        # Close JSON array
        if self.json_file:
            self.json_file.write('\n]')
        
        # Close all files
        for file_handle in [self.text_file, self.json_file, self.events_file]:
            if file_handle:
                try:
                    file_handle.close()
                except:
                    pass
        
        # Wait for flush thread to finish
        if self.flush_thread and self.flush_thread.is_alive():
            self.flush_thread.join(timeout=1.0)
    
    def __del__(self):
        """Destructor to ensure files are closed"""
        self.close()

# Test functions
if __name__ == "__main__":
    # Test the logger
    print("Testing SES Logger...")
    
    logger = LoggerSES(0)
    
    # Test different event types
    logger.log_send(1, 1, [1, 0, 0], "Hello P1")
    logger.log_receive(1, 1, [1, 1, 0], "Hello P0")
    logger.log_deliver(1, 1, [1, 1, 0], was_buffered=False)
    logger.log_buffer(2, 1, [1, 0, 1], "Waiting for causality")
    logger.log_clock_update([1, 1, 0], [1, 1, 1], "Message delivery")
    logger.log_error("Test error message")
    logger.log_info("Test info message", test_param="value")
    
    # Test search
    results = logger.search_entries("Hello")
    print(f"Search results: {len(results)}")
    
    # Test statistics
    stats = logger.get_statistics()
    print(f"Statistics: {stats}")
    
    # Test recent entries
    recent = logger.get_recent_entries(5)
    print(f"Recent entries: {len(recent)}")
    
    time.sleep(1)  # Let flush happen
    
    logger.close()
    print("Logger test completed")
