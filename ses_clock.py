import threading
import copy
from typing import List, Dict, Any
import logging

class SESClock:
    """
    Simple Event Synchronization Vector Clock implementation
    Maintains vector timestamps for causal ordering in distributed systems
    """
    
    def __init__(self, process_id: int, size: int = 15):
        self.process_id = process_id
        self.size = size
        self.clock = [0] * size
        self.lock = threading.RLock()  # Use RLock for nested locking
        self.logger = logging.getLogger(f"SESClock-{process_id}")
        self.event_count = 0  # Track total events

    def tick(self, pid: int = None):
        """
        Increment clock for local event (sending message)
        """
        if pid is None:
            pid = self.process_id
            
        with self.lock:
            self.clock[pid] += 1
            self.event_count += 1
            self.logger.debug(f"Clock tick for process {pid}: {self.clock}")
            return self.get()

    def merge(self, other_clock: List[int]):
        """
        Merge with another clock (element-wise maximum)
        Used when receiving a message
        """
        with self.lock:
            if len(other_clock) != self.size:
                self.logger.error(f"Clock size mismatch: expected {self.size}, got {len(other_clock)}")
                return self.get()
            
            old_clock = self.clock.copy()
            self.clock = [max(self.clock[i], other_clock[i]) for i in range(self.size)]
            
            self.logger.debug(f"Clock merge: {old_clock} + {other_clock} -> {self.clock}")
            return self.get()

    def get(self) -> List[int]:
        """
        Get current clock state (thread-safe copy)
        """
        with self.lock:
            return copy.deepcopy(self.clock)

    def update_on_receive(self, sender_id: int, other_clock: List[int]):
        """
        Update clock when receiving a message from another process
        1. Merge with received clock
        2. Increment own clock
        """
        with self.lock:
            # First merge with received clock
            self.merge(other_clock)
            
            # Then increment own clock for the receive event
            self.clock[self.process_id] += 1
            self.event_count += 1
            
            self.logger.debug(f"Clock updated on receive from {sender_id}: {self.clock}")
            return self.get()

    def update_on_send(self) -> List[int]:
        """
        Update clock when sending a message
        """
        return self.tick()

    def compare(self, other_clock: List[int]) -> str:
        """
        Compare this clock with another clock
        Returns: 'before', 'after', 'concurrent', 'equal'
        """
        with self.lock:
            if len(other_clock) != self.size:
                return 'incomparable'
            
            if self.clock == other_clock:
                return 'equal'
            
            # Check if this clock is before other clock
            before = True
            strictly_less = False
            for i in range(self.size):
                if self.clock[i] > other_clock[i]:
                    before = False
                    break
                elif self.clock[i] < other_clock[i]:
                    strictly_less = True
            
            if before and strictly_less:
                return 'before'
            
            # Check if this clock is after other clock
            after = True
            strictly_greater = False
            for i in range(self.size):
                if self.clock[i] < other_clock[i]:
                    after = False
                    break
                elif self.clock[i] > other_clock[i]:
                    strictly_greater = True
            
            if after and strictly_greater:
                return 'after'
            
            return 'concurrent'

    def can_deliver_ses(self, message_clock: List[int], sender_id: int) -> bool:
        """
        Check SES delivery condition
        Message from sender j can be delivered to process i if:
        For all k != j: timestamp_msg[k] <= timestamp_i[k]
        """
        with self.lock:
            if len(message_clock) != self.size:
                return False
            
            for k in range(self.size):
                if k != sender_id:  # For all processes except sender
                    if message_clock[k] > self.clock[k]:
                        self.logger.debug(
                            f"SES condition failed: msg_clock[{k}]={message_clock[k]} > local_clock[{k}]={self.clock[k]}"
                        )
                        return False
            
            self.logger.debug(f"SES condition satisfied for message from {sender_id}")
            return True

    def get_causality_gap(self, message_clock: List[int], sender_id: int) -> Dict[int, int]:
        """
        Get the causality gap (how many events we're missing from each process)
        """
        with self.lock:
            gaps = {}
            for k in range(self.size):
                if k != sender_id and message_clock[k] > self.clock[k]:
                    gaps[k] = message_clock[k] - self.clock[k]
            return gaps

    def reset(self):
        """
        Reset clock to all zeros (for testing)
        """
        with self.lock:
            self.clock = [0] * self.size
            self.event_count = 0
            self.logger.info("Clock reset to [0, 0, ..., 0]")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get clock statistics
        """
        with self.lock:
            return {
                "process_id": self.process_id,
                "current_clock": self.clock.copy(),
                "event_count": self.event_count,
                "max_clock_value": max(self.clock),
                "total_events_seen": sum(self.clock)
            }

    def __str__(self) -> str:
        """String representation of clock"""
        with self.lock:
            return f"SESClock(P{self.process_id}): {self.clock}"

    def __repr__(self) -> str:
        return self.__str__()

# Test functions
if __name__ == "__main__":
    # Test SES clock functionality
    print("Testing SES Clock...")
    
    # Create clocks for 3 processes
    clock0 = SESClock(0, 3)
    clock1 = SESClock(1, 3)
    clock2 = SESClock(2, 3)
    
    print(f"Initial clocks:")
    print(f"P0: {clock0}")
    print(f"P1: {clock1}")
    print(f"P2: {clock2}")
    
    # P0 sends to P1
    send_clock = clock0.update_on_send()
    print(f"\nP0 sends message with clock: {send_clock}")
    
    recv_clock = clock1.update_on_receive(0, send_clock)
    print(f"P1 receives, clock becomes: {recv_clock}")
    
    # Test SES condition
    send_clock2 = clock1.update_on_send()
    can_deliver = clock2.can_deliver_ses(send_clock2, 1)
    print(f"\nP1 sends to P2 with clock {send_clock2}")
    print(f"P2 can deliver immediately: {can_deliver}")
    
    if can_deliver:
        clock2.update_on_receive(1, send_clock2)
    
    print(f"\nFinal clocks:")
    print(f"P0: {clock0}")
    print(f"P1: {clock1}")
    print(f"P2: {clock2}")
    
    # Test causality gap
    gap = clock2.get_causality_gap([2, 1, 0], 0)
    print(f"\nCausality gap for message [2,1,0] from P0 to P2: {gap}")
    
    print("\nClock comparison tests:")
    print(f"P0 vs P1: {clock0.compare(clock1.get())}")
    print(f"P1 vs P2: {clock1.compare(clock2.get())}")
    print(f"P0 vs P2: {clock0.compare(clock2.get())}")
    
    print("\nStatistics:")
    print(f"P0 stats: {clock0.get_stats()}")
    print(f"P1 stats: {clock1.get_stats()}")
    print(f"P2 stats: {clock2.get_stats()}")
