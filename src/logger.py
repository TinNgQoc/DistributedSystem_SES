"""
Logger module for SES Algorithm
Ghi log chi tiết về các hoạt động của process
"""

import logging
import os
from datetime import datetime
from threading import Lock

class SESLogger:
    """
    Logger chuyên dụng cho SES Algorithm
    Ghi log chi tiết về buffer, delivery, và vector clock updates
    """
    
    def __init__(self, process_id, log_dir=None):
        """
        Khởi tạo logger
        
        Args:
            process_id: ID của process
            log_dir: Thư mục chứa log files
        """
        self.process_id = process_id
        
        # Tạo đường dẫn tuyệt đối cho log_dir
        if log_dir is None:
            # Lên 1 cấp từ src/ để đến thư mục gốc, rồi vào logs/
            current_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(current_dir)
            log_dir = os.path.join(parent_dir, "logs")
        
        self.log_dir = log_dir
        self.lock = Lock()
        
        # Tạo thư mục logs nếu chưa tồn tại
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Tạo log file cho process
        log_filename = os.path.join(log_dir, f"process_{process_id}.log")
        
        # Cấu hình logger
        self.logger = logging.getLogger(f"Process_{process_id}")
        self.logger.setLevel(logging.DEBUG)
        
        # Xóa các handlers cũ nếu có
        self.logger.handlers = []
        
        # File handler
        fh = logging.FileHandler(log_filename, mode='w', encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - P%(process_id)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)
        
        # Lưu process_id vào logger
        self.logger = logging.LoggerAdapter(self.logger, {'process_id': process_id})
        
        self.log_event(f"Logger initialized for Process {process_id}")
    
    def log_event(self, message):
        """
        Ghi log sự kiện chung
        """
        with self.lock:
            self.logger.info(message)
    
    def log_send(self, message, current_t):
        """
        Ghi log khi gửi message theo SES
        
        Args:
            message: Message được gửi
            current_t: Local time hiện tại
        """
        with self.lock:
            self.logger.info(
                f"SEND: {message.content} to P{message.receiver_id} | "
                f"tm={message.tm} | V_M={message.v_m} | t_P={current_t}"
            )
    
    def log_receive(self, message, current_t):
        """
        Ghi log khi nhận message theo SES
        
        Args:
            message: Message nhận được
            current_t: Local time hiện tại
        """
        with self.lock:
            self.logger.info(
                f"RECEIVE: {message.content} from P{message.sender_id} | "
                f"tm={message.tm} | V_M={message.v_m} | t_P={current_t}"
            )
    
    def log_buffer(self, message, buffer_size, current_t_p=None):
        """
        Ghi log khi message bị buffer theo SES
        
        Args:
            message: Message bị buffer
            buffer_size: Kích thước buffer hiện tại
            current_t_p: Vector timestamp hiện tại của receiver (optional)
        """
        with self.lock:
            # Check if V_M contains receiver_id to explain why buffered
            if message.receiver_id in message.v_m:
                t_in_vm = message.v_m[message.receiver_id]
                reason_parts = [f"V_M contains (P{message.receiver_id}, {t_in_vm})"]
                
                # If we have current_t_p, show the comparison
                if current_t_p is not None:
                    # Find which component(s) caused buffering
                    greater_components = []
                    for i in range(len(t_in_vm)):
                        if t_in_vm[i] > current_t_p[i]:
                            greater_components.append(f"t[{i}]={t_in_vm[i]} > t_P[{i}]={current_t_p[i]}")
                    
                    if greater_components:
                        reason_parts.append(f"Condition: {' AND '.join(greater_components)}")
                        reason_parts.append(f"Current t_P={current_t_p}")
                
                reason = " | ".join(reason_parts)
            else:
                reason = "No causal dependency on receiver in V_M"
            
            self.logger.warning(
                f"🔶 BUFFERED: {message.content} from P{message.sender_id} | "
                f"MsgID={message.message_id} | tm={message.tm} | V_M={message.v_m} | "
                f"BufferSize={buffer_size} | Reason: {reason}"
            )
    
    def log_delivery(self, message, current_t, from_buffer=False):
        """
        Ghi log khi deliver message theo SES
        
        Args:
            message: Message được deliver
            current_t: Local time sau khi deliver
            from_buffer: True nếu message được deliver từ buffer
        """
        with self.lock:
            if from_buffer:
                icon = "📦➡️✅"
                source = "BUFFER"
            else:
                icon = "✅"
                source = "DIRECT"
            
            self.logger.info(
                f"{icon} DELIVERED ({source}): {message.content} from P{message.sender_id} | "
                f"MsgID={message.message_id} | tm={message.tm} | V_M={message.v_m} | "
                f"New t_P={current_t}"
            )
    
    def log_vc_update(self, old_t, new_t, reason=""):
        """
        Ghi log khi local time được cập nhật theo SES
        
        Args:
            old_t: Local time trước khi cập nhật
            new_t: Local time sau khi cập nhật
            reason: Lý do cập nhật
        """
        with self.lock:
            self.logger.debug(
                f"TIME_UPDATE: t_P: {old_t} -> {new_t} | Reason: {reason}"
            )
    
    def log_buffer_check(self, buffer_size_before, deliverable_count, current_t_p=None):
        """
        Ghi log khi kiểm tra buffer
        
        Args:
            buffer_size_before: Kích thước buffer trước khi check
            deliverable_count: Số messages có thể deliver
            current_t_p: Vector timestamp hiện tại của process (optional)
        """
        with self.lock:
            if deliverable_count > 0:
                t_p_str = f" | t_P={current_t_p}" if current_t_p else ""
                self.logger.info(
                    f"🔍 BUFFER_CHECK: Found {deliverable_count} deliverable message(s) | "
                    f"Buffer before: {buffer_size_before} | "
                    f"After delivery: {buffer_size_before - deliverable_count}{t_p_str}"
                )
            elif buffer_size_before > 0:
                t_p_str = f" | t_P={current_t_p}" if current_t_p else ""
                self.logger.debug(
                    f"🔍 BUFFER_CHECK: No deliverable messages yet | "
                    f"Buffer size: {buffer_size_before}{t_p_str}"
                )
    
    def log_statistics(self, stats):
        """
        Ghi log thống kê
        
        Args:
            stats: Dictionary chứa thống kê
        """
        with self.lock:
            self.logger.info(
                f"STATISTICS: Sent={stats.get('sent', 0)}, "
                f"Received={stats.get('received', 0)}, "
                f"Delivered={stats.get('delivered', 0)}, "
                f"Buffered={stats.get('buffered', 0)}, "
                f"BufferSize={stats.get('buffer_size', 0)}"
            )
    
    def log_error(self, error_message):
        """
        Ghi log lỗi
        
        Args:
            error_message: Thông báo lỗi
        """
        with self.lock:
            self.logger.error(error_message)
    
    def log_debug(self, message):
        """
        Ghi log debug
        
        Args:
            message: Thông báo debug
        """
        with self.lock:
            self.logger.debug(message)
