import threading
import time
from typing import Callable, Dict, Any, List, Optional, Set
from datetime import datetime
import logging
from ses_clock import SESClock
from buffer_manager import BufferManager

class DeliveryEvent:
    """Represents a message delivery event"""
    
    def __init__(self, message: Dict[str, Any], delivery_time: float, 
                 was_buffered: bool = False, buffer_duration: float = 0.0):
        self.message = message
        self.delivery_time = delivery_time
        self.was_buffered = was_buffered
        self.buffer_duration = buffer_duration
        self.sender_id = message['sender_id']
        self.seq = message['seq']
        self.vector_clock = message['vector_clock'].copy()

class DeliverEngine:
    """
    Message delivery engine with SES ordering enforcement
    Coordinates between SES clock, buffer manager, and application callbacks
    """
    
    def __init__(self, process_id: int, process_message: Callable[[Dict[str, Any]], None]):
        self.process_id = process_id
        self.process_message = process_message
        
        # Core components
        self.clock = SESClock(process_id)
        self.buffer_manager = None  # Will be set after initialization
        
        # Delivery tracking
        self.delivered_messages: Set[tuple] = set()  # (sender_id, seq)
        self.delivery_history: List[DeliveryEvent] = []
        self.lock = threading.RLock()
        
        # Statistics
        self.stats = {
            "messages_delivered": 0,
            "messages_delivered_immediate": 0,
            "messages_delivered_buffered": 0,
            "duplicate_messages_rejected": 0,
            "total_delivery_time": 0.0,
            "cascade_deliveries": 0
        }
        
        # Configuration
        self.max_history_size = 10000  # Maximum delivery events to keep
        
        # Logging
        self.logger = logging.getLogger(f"DeliverEngine-{process_id}")
        self.logger.setLevel(logging.INFO)
        
        # Initialize buffer manager with SES checker
        self.buffer_manager = BufferManager(process_id, self._can_deliver_ses)
        self.buffer_manager.on_message_delivered = self._on_buffer_delivered
        
        self.logger.info(f"Delivery engine initialized for process {process_id}")
    
    def start(self):
        """Start the delivery engine"""
        self.buffer_manager.start()
        self.logger.info("Delivery engine started")
    
    def stop(self):
        """Stop the delivery engine"""
        self.buffer_manager.stop()
        self.logger.info("Delivery engine stopped")
    
    def receive_message(self, message: Dict[str, Any]) -> bool:
        """
        Process an incoming message for delivery
        Returns True if message was processed successfully
        """
        with self.lock:
            msg_id = (message['sender_id'], message['seq'])
            
            # Check for duplicates
            if msg_id in self.delivered_messages:
                self.stats["duplicate_messages_rejected"] += 1
                self.logger.warning(f"Duplicate message rejected: {msg_id}")
                return False
            
            # Update our clock with received message
            sender_clock = message['vector_clock']
            self.clock.update_on_receive(message['sender_id'], sender_clock)
            
            # Try to deliver through buffer manager
            delivered_immediately, cascaded_messages = self.buffer_manager.try_deliver_message(message)
            
            if delivered_immediately:
                # Message delivered immediately
                self._record_delivery(message, was_buffered=False)
                self._deliver_to_application(message)
                
                # Handle cascaded deliveries
                for cascaded_msg in cascaded_messages:
                    self._record_delivery(cascaded_msg, was_buffered=True)
                    self._deliver_to_application(cascaded_msg)
                
                self.stats["cascade_deliveries"] += len(cascaded_messages)
                
                self.logger.debug(
                    f"Message {msg_id} delivered immediately "
                    f"(+{len(cascaded_messages)} cascaded)"
                )
            
            else:
                self.logger.debug(f"Message {msg_id} buffered for later delivery")
            
            return True
    
    def _can_deliver_ses(self, message: Dict[str, Any]) -> bool:
        """Check if message satisfies SES delivery condition"""
        return self.clock.can_deliver_ses(
            message['vector_clock'], 
            message['sender_id']
        )
    
    def _on_buffer_delivered(self, message: Dict[str, Any]):
        """Callback when buffer manager delivers a message"""
        # This is called by buffer manager, no need to deliver to app again
        # Just record the delivery event
        pass
    
    def _record_delivery(self, message: Dict[str, Any], was_buffered: bool = False, 
                        buffer_duration: float = 0.0):
        """Record a message delivery event"""
        msg_id = (message['sender_id'], message['seq'])
        
        # Mark as delivered
        self.delivered_messages.add(msg_id)
        
        # Create delivery event
        delivery_event = DeliveryEvent(
            message=message,
            delivery_time=time.time(),
            was_buffered=was_buffered,
            buffer_duration=buffer_duration
        )
        
        # Add to history (with size limit)
        self.delivery_history.append(delivery_event)
        if len(self.delivery_history) > self.max_history_size:
            self.delivery_history = self.delivery_history[-self.max_history_size//2:]
        
        # Update statistics
        self.stats["messages_delivered"] += 1
        if was_buffered:
            self.stats["messages_delivered_buffered"] += 1
            self.stats["total_delivery_time"] += buffer_duration
        else:
            self.stats["messages_delivered_immediate"] += 1
        
        self.logger.debug(
            f"Delivery recorded: {msg_id}, "
            f"buffered={was_buffered}, "
            f"buffer_time={buffer_duration:.3f}s"
        )
    
    def _deliver_to_application(self, message: Dict[str, Any]):
        """Deliver message to the application callback"""
        try:
            self.process_message(message)
            self.logger.debug(f"Message delivered to application: P{message['sender_id']}#{message['seq']}")
        except Exception as e:
            self.logger.error(f"Error delivering message to application: {e}")
    
    def send_message(self, receiver_id: int, seq: int, payload: str) -> Dict[str, Any]:
        """
        Prepare a message for sending (updates local clock)
        Returns the message dict ready for network transmission
        """
        with self.lock:
            # Update clock for send event
            current_clock = self.clock.update_on_send()
            
            # Create message
            message = {
                "sender_id": self.process_id,
                "receiver_id": receiver_id,
                "seq": seq,
                "vector_clock": current_clock,
                "payload": payload,
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.debug(f"Message prepared for sending: P{receiver_id}#{seq}")
            return message
    
    def force_check_buffer(self):
        """Force check buffer for deliverable messages (after clock updates)"""
        with self.lock:
            cascaded_messages = self.buffer_manager.force_check_buffer()
            
            # Process cascaded deliveries
            for msg in cascaded_messages:
                self._record_delivery(msg, was_buffered=True)
                self._deliver_to_application(msg)
            
            if cascaded_messages:
                self.stats["cascade_deliveries"] += len(cascaded_messages)
                self.logger.info(f"Force check delivered {len(cascaded_messages)} buffered messages")
    
    def get_current_clock(self) -> List[int]:
        """Get current vector clock state"""
        return self.clock.get()
    
    def get_delivery_stats(self) -> Dict[str, Any]:
        """Get delivery engine statistics"""
        with self.lock:
            clock_stats = self.clock.get_stats()
            buffer_stats = self.buffer_manager.get_stats()
            
            avg_buffer_time = 0.0
            if self.stats["messages_delivered_buffered"] > 0:
                avg_buffer_time = (self.stats["total_delivery_time"] / 
                                 self.stats["messages_delivered_buffered"])
            
            return {
                "process_id": self.process_id,
                "delivery_stats": self.stats.copy(),
                "clock_stats": clock_stats,
                "buffer_stats": buffer_stats,
                "average_buffer_time": avg_buffer_time,
                "total_delivered": len(self.delivered_messages),
                "delivery_history_size": len(self.delivery_history)
            }
    
    def get_delivery_summary(self) -> str:
        """Get human-readable delivery summary"""
        stats = self.get_delivery_stats()
        
        summary = f"Delivery Engine P{self.process_id} Summary:\n"
        summary += f"  Total delivered: {stats['total_delivered']}\n"
        summary += f"  Immediate: {stats['delivery_stats']['messages_delivered_immediate']}\n"
        summary += f"  From buffer: {stats['delivery_stats']['messages_delivered_buffered']}\n"
        summary += f"  Cascaded: {stats['delivery_stats']['cascade_deliveries']}\n"
        summary += f"  Duplicates rejected: {stats['delivery_stats']['duplicate_messages_rejected']}\n"
        summary += f"  Avg buffer time: {stats['average_buffer_time']:.3f}s\n"
        summary += f"  Current clock: {self.get_current_clock()}\n"
        
        # Buffer state
        buffer_state = self.buffer_manager.get_buffer_state()
        summary += f"  Buffer size: {buffer_state['buffer_size']}\n"
        
        return summary
    
    def get_recent_deliveries(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent delivery events"""
        with self.lock:
            recent = self.delivery_history[-count:] if self.delivery_history else []
            return [
                {
                    "sender_id": event.sender_id,
                    "seq": event.seq,
                    "delivery_time": event.delivery_time,
                    "was_buffered": event.was_buffered,
                    "buffer_duration": event.buffer_duration,
                    "vector_clock": event.vector_clock
                }
                for event in recent
            ]
    
    def reset_stats(self):
        """Reset all statistics (for testing)"""
        with self.lock:
            self.stats = {
                "messages_delivered": 0,
                "messages_delivered_immediate": 0,
                "messages_delivered_buffered": 0,
                "duplicate_messages_rejected": 0,
                "total_delivery_time": 0.0,
                "cascade_deliveries": 0
            }
            self.delivered_messages.clear()
            self.delivery_history.clear()
            self.clock.reset()
            self.logger.info("Statistics reset")

# Test functions
if __name__ == "__main__":
    # Test delivery engine
    print("Testing Delivery Engine...")
    
    delivered_messages = []
    
    def test_process_message(message):
        delivered_messages.append(message)
        print(f"APP RECEIVED: P{message['sender_id']}#{message['seq']} - {message['payload']}")
    
    # Create delivery engine
    engine = DeliverEngine(0, test_process_message)
    engine.start()
    
    print(f"Initial clock: {engine.get_current_clock()}")
    
    # Test messages with different causality
    test_messages = [
        # Message that should be delivered immediately
        {
            "sender_id": 1,
            "seq": 1,
            "vector_clock": [0, 1, 0],
            "payload": "Hello from P1",
            "timestamp": datetime.now().isoformat()
        },
        # Message that might be buffered
        {
            "sender_id": 2,
            "seq": 1,
            "vector_clock": [0, 2, 1],  # Assumes we've seen 2 events from P1
            "payload": "Hello from P2",
            "timestamp": datetime.now().isoformat()
        },
        # Another message from P1
        {
            "sender_id": 1,
            "seq": 2,
            "vector_clock": [0, 2, 0],
            "payload": "Second message from P1",
            "timestamp": datetime.now().isoformat()
        }
    ]
    
    print("\nProcessing messages...")
    for i, msg in enumerate(test_messages):
        print(f"\n--- Processing message {i+1} ---")
        success = engine.receive_message(msg)
        print(f"Message processed: {success}")
        print(f"Current clock: {engine.get_current_clock()}")
        print(engine.buffer_manager.get_buffer_summary())
    
    # Test sending a message
    print("\n--- Testing message sending ---")
    outgoing_msg = engine.send_message(2, 1, "Hello to P2")
    print(f"Outgoing message: {outgoing_msg}")
    print(f"Clock after send: {engine.get_current_clock()}")
    
    # Force check buffer
    print("\n--- Force checking buffer ---")
    engine.force_check_buffer()
    
    # Print final statistics
    print("\n--- Final Statistics ---")
    print(engine.get_delivery_summary())
    
    print("\n--- Recent Deliveries ---")
    recent = engine.get_recent_deliveries(5)
    for delivery in recent:
        print(f"  P{delivery['sender_id']}#{delivery['seq']} "
              f"(buffered={delivery['was_buffered']}, "
              f"time={delivery['buffer_duration']:.3f}s)")
    
    engine.stop()
    print(f"\nTotal messages delivered to application: {len(delivered_messages)}")
