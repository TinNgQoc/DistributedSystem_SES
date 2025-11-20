"""
Message and Message Buffer implementation for SES Algorithm
Quản lý buffering và ordering của messages theo causal order
"""

import time
from datetime import datetime

class Message:
    """
    Message structure for SES Algorithm
    Contains: sender, receiver, content, tm (send timestamp vector), V_M
    """
    
    def __init__(self, sender_id, receiver_id, content, tm, v_m, message_id):
        """
        Initialize SES message
        
        Args:
            sender_id: ID of sending process
            receiver_id: ID of receiving process
            content: Message content
            tm: Vector timestamp when message was sent (list of N integers)
            v_m: V_P structure from sender (dictionary {pid: vector})
            message_id: Unique message identifier
        """
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.content = content
        self.tm = tm.copy() if isinstance(tm, list) else tm  # Vector timestamp at send time
        self.v_m = v_m  # V_P from sender
        self.message_id = message_id
        self.timestamp = datetime.now()  # Physical timestamp
        self.delivered = False
    
    def __str__(self):
        return f"Msg[{self.message_id}] from P{self.sender_id}->P{self.receiver_id}: '{self.content}' tm={self.tm} V_M={self.v_m}"
    
    def __repr__(self):
        return self.__str__()


class MessageBuffer:
    """
    Buffer để lưu trữ các messages chưa thể deliver do vi phạm causal order
    """
    
    def __init__(self, process_id, logger):
        """
        Khởi tạo message buffer
        
        Args:
            process_id: ID của process sở hữu buffer này
            logger: Logger để ghi log
        """
        self.process_id = process_id
        self.buffer = []  # Danh sách messages đang chờ
        self.logger = logger
        self.total_buffered = 0
        self.total_delivered = 0
    
    def add_message(self, message, current_t_p=None):
        """
        Thêm message vào buffer
        
        Args:
            message: Message cần buffer
            current_t_p: Vector timestamp hiện tại của receiver (optional, for logging)
        """
        self.buffer.append(message)
        self.total_buffered += 1
        self.logger.log_buffer(message, len(self.buffer), current_t_p)
    
    def check_deliverable(self, message, receiver_id, v_p_receiver, t_p_receiver):
        """
        Check if message can be delivered according to SES algorithm
        
        SES Delivery Conditions:
        1. If V_M does not contain (receiver_id, t), message can be delivered
        2. If (receiver_id, t) exists in V_M:
           - If t > t_receiver: buffer the message (don't deliver)
           - If t <= t_receiver: deliver it
        
        Where t > t_receiver means: EXISTS i such that t[i] > t_receiver[i]
        (There exists an event in another process that receiver hasn't updated)
        
        Args:
            message: Message to check
            receiver_id: ID of receiving process
            v_p_receiver: V_P structure of receiver
            t_p_receiver: Vector timestamp of receiver (list)
            
        Returns:
            True if deliverable, False if should be buffered
        """
        # Check if V_M contains entry for receiver
        if receiver_id not in message.v_m:
            # V_M does not contain (receiver_id, t) -> can deliver
            return True
        
        # V_M contains (receiver_id, t)
        t_in_v_m = message.v_m[receiver_id]
        
        # Check if t > t_receiver: EXISTS i such that t[i] > t_receiver[i]
        # If so, buffer (return False)
        # Otherwise (t <= t_receiver for all i), deliver (return True)
        t_greater = any(t_in_v_m[i] > t_p_receiver[i] for i in range(len(t_in_v_m)))
        
        # If t > t_receiver (any component greater): buffer (return False)
        # If t <= t_receiver (all components <=): deliver (return True)
        return not t_greater
    
    def get_deliverable_messages(self, receiver_id, v_p_receiver, t_p_receiver):
        """
        Get list of deliverable messages from buffer
        
        Args:
            receiver_id: ID of receiving process
            v_p_receiver: V_P structure of receiver
            t_p_receiver: Local time of receiver
            
        Returns:
            List of deliverable messages
        """
        deliverable = []
        remaining = []
        
        for msg in self.buffer:
            if self.check_deliverable(msg, receiver_id, v_p_receiver, t_p_receiver):
                deliverable.append(msg)
                self.total_delivered += 1
            else:
                remaining.append(msg)
        
        self.buffer = remaining
        return deliverable
    
    def remove_message(self, message):
        """
        Xóa message khỏi buffer
        
        Args:
            message: Message cần xóa
        """
        if message in self.buffer:
            self.buffer.remove(message)
    
    def get_buffer_size(self):
        """
        Lấy số lượng messages trong buffer
        
        Returns:
            Số lượng messages
        """
        return len(self.buffer)
    
    def get_statistics(self):
        """
        Lấy thống kê về buffer
        
        Returns:
            Dict chứa thông tin thống kê
        """
        return {
            'current_buffer_size': len(self.buffer),
            'total_buffered': self.total_buffered,
            'total_delivered': self.total_delivered
        }
    
    def __str__(self):
        return f"Buffer[P{self.process_id}]: {len(self.buffer)} messages waiting"
