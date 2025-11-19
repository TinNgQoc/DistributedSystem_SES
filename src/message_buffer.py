"""
Message and Message Buffer implementation for SES Algorithm
Quản lý buffering và ordering của messages theo causal order
"""

import time
from datetime import datetime

class Message:
    """
    Đại diện cho một message trong hệ thống phân tán
    """
    
    def __init__(self, sender_id, receiver_id, content, vector_clock, message_id):
        """
        Khởi tạo message
        
        Args:
            sender_id: ID của process gửi
            receiver_id: ID của process nhận
            content: Nội dung message
            vector_clock: Vector clock tại thời điểm gửi
            message_id: ID duy nhất của message
        """
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.content = content
        self.vector_clock = vector_clock
        self.message_id = message_id
        self.timestamp = datetime.now()
        self.delivered = False
    
    def __str__(self):
        return f"Msg[{self.message_id}] from P{self.sender_id}->P{self.receiver_id}: '{self.content}' VC={self.vector_clock}"
    
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
    
    def add_message(self, message, current_vc):
        """
        Thêm message vào buffer
        
        Args:
            message: Message cần buffer
            current_vc: Vector clock hiện tại
        """
        self.buffer.append(message)
        self.total_buffered += 1
        
        # Xác định lý do cụ thể phải buffer
        sender_id = message.sender_id
        msg_vc = message.vector_clock
        
        reasons = []
        
        # Kiểm tra điều kiện 1: VC_m[sender] = VC_current[sender] + 1
        if msg_vc[sender_id] != current_vc[sender_id] + 1:
            expected = current_vc[sender_id] + 1
            actual = msg_vc[sender_id]
            if actual > expected:
                missing = actual - expected
                reasons.append(f"Missing {missing} message(s) from P{sender_id} (need VC[{sender_id}]={expected}, got {actual})")
            else:
                reasons.append(f"Old message from P{sender_id} (VC[{sender_id}]={actual} < {expected})")
        
        # Kiểm tra điều kiện 2: VC_m[k] <= VC_current[k] với mọi k != sender
        for k in range(len(msg_vc)):
            if k != sender_id and msg_vc[k] > current_vc[k]:
                missing = msg_vc[k] - current_vc[k]
                reasons.append(f"Missing {missing} message(s) from P{k} (need VC[{k}]={msg_vc[k]}, have {current_vc[k]})")
        
        reason_text = "; ".join(reasons) if reasons else "Causal dependencies not satisfied"
        self.logger.log_buffer(message, len(self.buffer), current_vc, reason_text)
    
    def check_deliverable(self, message, current_vc):
        """
        Kiểm tra xem message có thể deliver được không theo điều kiện SES
        
        Điều kiện deliver message m từ Pi đến Pj:
        1. VC_m[i] = VC_j[i] + 1 (message tiếp theo từ sender)
        2. VC_m[k] <= VC_j[k] với mọi k != i (không có message nào bị thiếu)
        
        Args:
            message: Message cần kiểm tra
            current_vc: Vector clock hiện tại của process
            
        Returns:
            True nếu có thể deliver, False nếu không
        """
        sender_id = message.sender_id
        msg_vc = message.vector_clock
        
        # Điều kiện 1: VC_m[sender] = VC_current[sender] + 1
        if msg_vc[sender_id] != current_vc[sender_id] + 1:
            return False
        
        # Điều kiện 2: VC_m[k] <= VC_current[k] với mọi k != sender
        for k in range(len(msg_vc)):
            if k != sender_id:
                if msg_vc[k] > current_vc[k]:
                    return False
        
        return True
    
    def get_deliverable_messages(self, current_vc):
        """
        Lấy danh sách các messages có thể deliver từ buffer
        
        Args:
            current_vc: Vector clock hiện tại
            
        Returns:
            List các messages có thể deliver
        """
        deliverable = []
        remaining = []
        
        for msg in self.buffer:
            if self.check_deliverable(msg, current_vc):
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
