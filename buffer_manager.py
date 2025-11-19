import threading
import heapq
import time
from typing import List, Dict, Any, Tuple, Optional, Callable
from datetime import datetime
import logging

class BufferedMessage:
    """Represents a buffered message with priority ordering"""
    
    def __init__(self, message: Dict[str, Any], buffer_time: float):
        self.message = message
        self.buffer_time = buffer_time
        self.sender_id = message['sender_id']
        self.seq = message['seq']
        self.vector_clock = message['vector_clock']
        self.attempts = 0
        self.last_attempt = buffer_time
    
    def __lt__(self, other):
        """Priority for heap: earlier buffer time has higher priority"""
        return self.buffer_time < other.buffer_time
    
    def __eq__(self, other):
        """Equality based on sender and sequence number"""
        return (self.sender_id, self.seq) == (other.sender_id, other.seq)
    
    def get_id(self) -> Tuple[int, int]:
        """Get unique identifier (sender_id, seq)"""
        return (self.sender_id, self.seq)

class BufferManager:
    """
    Manages message buffering for SES ordering
    Handles messages that cannot be delivered immediately due to causality constraints
    """
    
    def __init__(self, process_id: int, ses_checker: Callable[[Dict[str, Any]], bool]):
        self.process_id = process_id
        self.ses_checker = ses_checker  # Function to check SES delivery condition
        
        # Buffer storage
        self.buffer = []  # Priority heap of BufferedMessage objects
        self.buffer_dict = {}  # {(sender_id, seq): BufferedMessage} for fast lookup
        self.lock = threading.RLock()
        
        # Statistics and logging
        self.logger = logging.getLogger(f"BufferManager-{process_id}")
        self.stats = {
            "messages_buffered": 0,
            "messages_delivered_from_buffer": 0,
            "buffer_hits": 0,
            "buffer_misses": 0,
            "max_buffer_size": 0,
            "total_buffer_time": 0.0
        }
        
        # Configuration
        self.max_buffer_size = 1000  # Maximum number of buffered messages
        self.max_buffer_time = 300.0  # Maximum time to buffer a message (5 minutes)
        self.cleanup_interval = 60.0  # Cleanup old messages every minute
        
        # Background cleanup thread
        self.cleanup_thread = None
        self.running = False
        
        # Event listeners
        self.on_message_buffered = None  # Callback when message is buffered
        self.on_message_delivered = None  # Callback when message is delivered
        self.on_buffer_overflow = None  # Callback when buffer is full
    
    def start(self):
        """Start the buffer manager with background cleanup"""
        self.running = True
        self.cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True)
        self.cleanup_thread.start()
        self.logger.info("Buffer manager started")
    
    def stop(self):
        """Stop the buffer manager"""
        self.running = False
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=1.0)
        self.logger.info("Buffer manager stopped")
    
    def try_deliver_message(self, message: Dict[str, Any]) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Try to deliver a message. Returns (delivered, cascaded_messages)
        - delivered: True if message was delivered immediately
        - cascaded_messages: List of additional messages delivered from buffer
        """
        with self.lock:
            # Check if message can be delivered immediately
            if self.ses_checker(message):
                self.stats["buffer_hits"] += 1
                
                # Deliver this message
                delivered_messages = [message]
                self.logger.debug(f"Message {self._get_msg_id(message)} delivered immediately")
                
                # Check buffer for cascade deliveries
                cascaded = self._check_buffer_for_deliveries()
                delivered_messages.extend(cascaded)
                
                # Notify callback
                if self.on_message_delivered:
                    for msg in delivered_messages:
                        self.on_message_delivered(msg)
                
                return True, delivered_messages[1:]  # Return cascaded messages only
            
            else:
                # Buffer the message
                return self._buffer_message(message), []
    
    def _buffer_message(self, message: Dict[str, Any]) -> bool:
        """Buffer a message that cannot be delivered yet"""
        msg_id = self._get_msg_id(message)
        
        # Check for duplicate
        if msg_id in self.buffer_dict:
            self.logger.warning(f"Duplicate message {msg_id} already buffered")
            return False
        
        # Check buffer size limit
        if len(self.buffer) >= self.max_buffer_size:
            self.logger.error(f"Buffer overflow! Current size: {len(self.buffer)}")
            if self.on_buffer_overflow:
                self.on_buffer_overflow(message)
            return False
        
        # Create buffered message
        buffer_time = time.time()
        buffered_msg = BufferedMessage(message, buffer_time)
        
        # Add to buffer
        heapq.heappush(self.buffer, buffered_msg)
        self.buffer_dict[msg_id] = buffered_msg
        
        # Update statistics
        self.stats["messages_buffered"] += 1
        self.stats["buffer_misses"] += 1
        self.stats["max_buffer_size"] = max(self.stats["max_buffer_size"], len(self.buffer))
        
        self.logger.info(f"Message {msg_id} buffered (buffer size: {len(self.buffer)})")
        
        # Notify callback
        if self.on_message_buffered:
            self.on_message_buffered(message)
        
        return True
    
    def _check_buffer_for_deliveries(self) -> List[Dict[str, Any]]:
        """Check buffered messages for possible deliveries (cascade effect)"""
        delivered = []
        changed = True
        
        while changed and self.buffer:
            changed = False
            temp_buffer = []
            
            # Check all buffered messages
            while self.buffer:
                buffered_msg = heapq.heappop(self.buffer)
                msg_id = buffered_msg.get_id()
                
                if self.ses_checker(buffered_msg.message):
                    # Can deliver this message
                    delivered.append(buffered_msg.message)
                    del self.buffer_dict[msg_id]
                    
                    # Update statistics
                    self.stats["messages_delivered_from_buffer"] += 1
                    buffer_duration = time.time() - buffered_msg.buffer_time
                    self.stats["total_buffer_time"] += buffer_duration
                    
                    self.logger.info(
                        f"Message {msg_id} delivered from buffer "
                        f"(buffered for {buffer_duration:.2f}s)"
                    )
                    
                    changed = True
                    
                    # Notify callback
                    if self.on_message_delivered:
                        self.on_message_delivered(buffered_msg.message)
                
                else:
                    # Still cannot deliver
                    temp_buffer.append(buffered_msg)
            
            # Rebuild heap with remaining messages
            self.buffer = temp_buffer
            heapq.heapify(self.buffer)
        
        return delivered
    
    def force_check_buffer(self) -> List[Dict[str, Any]]:
        """Force check buffer for deliverable messages (called from external clock updates)"""
        with self.lock:
            return self._check_buffer_for_deliveries()
    
    def get_buffer_state(self) -> Dict[str, Any]:
        """Get current buffer state for debugging/monitoring"""
        with self.lock:
            messages = []
            for buffered_msg in self.buffer:
                messages.append({
                    "sender_id": buffered_msg.sender_id,
                    "seq": buffered_msg.seq,
                    "vector_clock": buffered_msg.vector_clock,
                    "buffer_time": buffered_msg.buffer_time,
                    "waiting_time": time.time() - buffered_msg.buffer_time,
                    "attempts": buffered_msg.attempts
                })
            
            return {
                "buffer_size": len(self.buffer),
                "max_buffer_size": self.max_buffer_size,
                "messages": sorted(messages, key=lambda x: x["buffer_time"])
            }
    
    def get_buffer_summary(self) -> str:
        """Get human-readable buffer summary"""
        with self.lock:
            if not self.buffer:
                return "Buffer: Empty"
            
            summary = f"Buffer: {len(self.buffer)} messages\n"
            for buffered_msg in sorted(self.buffer)[:5]:  # Show first 5 messages
                wait_time = time.time() - buffered_msg.buffer_time
                summary += f"  - P{buffered_msg.sender_id}#{buffered_msg.seq} "
                summary += f"(waiting {wait_time:.1f}s)\n"
            
            if len(self.buffer) > 5:
                summary += f"  ... and {len(self.buffer) - 5} more\n"
            
            return summary
    
    def get_stats(self) -> Dict[str, Any]:
        """Get buffer statistics"""
        with self.lock:
            avg_buffer_time = 0.0
            if self.stats["messages_delivered_from_buffer"] > 0:
                avg_buffer_time = (self.stats["total_buffer_time"] / 
                                 self.stats["messages_delivered_from_buffer"])
            
            return {
                **self.stats,
                "current_buffer_size": len(self.buffer),
                "average_buffer_time": avg_buffer_time,
                "buffer_utilization": len(self.buffer) / self.max_buffer_size
            }
    
    def clear_buffer(self):
        """Clear all buffered messages (for testing/cleanup)"""
        with self.lock:
            cleared_count = len(self.buffer)
            self.buffer.clear()
            self.buffer_dict.clear()
            self.logger.warning(f"Buffer cleared: {cleared_count} messages removed")
    
    def _cleanup_worker(self):
        """Background worker to cleanup old buffered messages"""
        while self.running:
            try:
                time.sleep(self.cleanup_interval)
                if not self.running:
                    break
                
                self._cleanup_old_messages()
                
            except Exception as e:
                self.logger.error(f"Error in cleanup worker: {e}")
    
    def _cleanup_old_messages(self):
        """Remove messages that have been buffered too long"""
        with self.lock:
            current_time = time.time()
            temp_buffer = []
            expired_count = 0
            
            while self.buffer:
                buffered_msg = heapq.heappop(self.buffer)
                age = current_time - buffered_msg.buffer_time
                
                if age > self.max_buffer_time:
                    # Remove expired message
                    msg_id = buffered_msg.get_id()
                    if msg_id in self.buffer_dict:
                        del self.buffer_dict[msg_id]
                    expired_count += 1
                    
                    self.logger.warning(
                        f"Expired message {msg_id} removed from buffer "
                        f"(age: {age:.1f}s)"
                    )
                else:
                    temp_buffer.append(buffered_msg)
            
            # Rebuild heap
            self.buffer = temp_buffer
            heapq.heapify(self.buffer)
            
            if expired_count > 0:
                self.logger.info(f"Cleanup completed: {expired_count} expired messages removed")
    
    def _get_msg_id(self, message: Dict[str, Any]) -> Tuple[int, int]:
        """Get message identifier tuple"""
        return (message['sender_id'], message['seq'])

# Test functions
if __name__ == "__main__":
    # Test buffer manager
    print("Testing Buffer Manager...")
    
    # Mock SES checker
    delivered_messages = set()
    
    def mock_ses_checker(message):
        # Simple mock: deliver messages with seq <= 2
        return message['seq'] <= 2
    
    def on_buffered(message):
        print(f"BUFFERED: P{message['sender_id']}#{message['seq']}")
    
    def on_delivered(message):
        msg_id = (message['sender_id'], message['seq'])
        delivered_messages.add(msg_id)
        print(f"DELIVERED: P{message['sender_id']}#{message['seq']}")
    
    # Create buffer manager
    buffer_mgr = BufferManager(0, mock_ses_checker)
    buffer_mgr.on_message_buffered = on_buffered
    buffer_mgr.on_message_delivered = on_delivered
    buffer_mgr.start()
    
    # Test messages
    test_messages = [
        {"sender_id": 1, "seq": 1, "vector_clock": [0, 1, 0]},
        {"sender_id": 1, "seq": 3, "vector_clock": [0, 3, 0]},  # Should be buffered
        {"sender_id": 2, "seq": 1, "vector_clock": [0, 0, 1]},
        {"sender_id": 2, "seq": 2, "vector_clock": [0, 0, 2]},
        {"sender_id": 1, "seq": 2, "vector_clock": [0, 2, 0]},
    ]
    
    print("\nProcessing messages...")
    for msg in test_messages:
        delivered, cascaded = buffer_mgr.try_deliver_message(msg)
        print(f"Message P{msg['sender_id']}#{msg['seq']}: delivered={delivered}, cascaded={len(cascaded)}")
    
    print(f"\nBuffer state:")
    print(buffer_mgr.get_buffer_summary())
    
    print(f"\nStatistics:")
    stats = buffer_mgr.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    buffer_mgr.stop()
