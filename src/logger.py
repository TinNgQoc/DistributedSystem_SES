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
    
    def log_send(self, message, current_vc):
        """
        Ghi log khi gửi message
        
        Args:
            message: Message được gửi
            current_vc: Vector clock hiện tại
        """
        with self.lock:
            # Tạo string giải thích vector clock
            vc_explain = self._format_vc_explanation(current_vc, message.sender_id)
            self.logger.info(
                f"SEND: {message.content} to P{message.receiver_id} | "
                f"MsgVC={message.vector_clock} | {vc_explain}"
            )
    
    def log_receive(self, message, current_vc_before):
        """
        Ghi log khi nhận message
        
        Args:
            message: Message nhận được
            current_vc_before: Vector clock trước khi nhận
        """
        with self.lock:
            vc_explain = self._format_vc_explanation(current_vc_before, self.process_id)
            self.logger.info(
                f"RECEIVE: {message.content} from P{message.sender_id} | "
                f"MsgVC={message.vector_clock} | {vc_explain}"
            )
    
    def log_buffer(self, message, buffer_size, current_vc, reason=""):
        """
        Ghi log khi message bị buffer
        
        Args:
            message: Message bị buffer
            buffer_size: Kích thước buffer hiện tại
            current_vc: Vector clock hiện tại
            reason: Lý do cụ thể phải buffer
        """
        with self.lock:
            self.logger.warning(
                f"BUFFERED: {message.content} from P{message.sender_id} | "
                f"MsgVC={message.vector_clock} | CurrentVC={current_vc} | "
                f"BufferSize={buffer_size} | Reason: {reason}"
            )
    
    def log_delivery(self, message, old_vc, new_vc, from_buffer=False):
        """
        Ghi log khi deliver message
        
        Args:
            message: Message được deliver
            old_vc: Vector clock trước khi deliver
            new_vc: Vector clock sau khi deliver
            from_buffer: True nếu message được deliver từ buffer
        """
        with self.lock:
            source = "BUFFER" if from_buffer else "DIRECT"
            
            # Hiển thị sự thay đổi của vector clock
            changes = []
            for i in range(len(old_vc)):
                if old_vc[i] != new_vc[i]:
                    changes.append(f"P{i}:{old_vc[i]}→{new_vc[i]}")
            
            change_str = ", ".join(changes) if changes else "No change"
            
            self.logger.info(
                f"DELIVERED ({source}): {message.content} from P{message.sender_id} | "
                f"MsgVC={message.vector_clock} | "
                f"VC_Changes=[{change_str}] | "
                f"NewVC={new_vc}"
            )
    
    def log_vc_update(self, old_vc, new_vc, reason=""):
        """
        Ghi log khi vector clock được cập nhật
        
        Args:
            old_vc: Vector clock trước khi cập nhật
            new_vc: Vector clock sau khi cập nhật
            reason: Lý do cập nhật
        """
        with self.lock:
            self.logger.debug(
                f"VC_UPDATE: {old_vc} -> {new_vc} | Reason: {reason}"
            )
    
    def log_buffer_check(self, trigger_message, buffer_size, deliverable_count, deliverable_messages):
        """
        Ghi log khi kiểm tra buffer
        
        Args:
            trigger_message: Message vừa được deliver (trigger việc check buffer)
            buffer_size: Kích thước buffer hiện tại
            deliverable_count: Số messages có thể deliver
            deliverable_messages: List các messages có thể deliver
        """
        if deliverable_count > 0:
            with self.lock:
                msg_list = ", ".join([f"{m.content} from P{m.sender_id}" for m in deliverable_messages])
                self.logger.info(
                    f"BUFFER_RELEASE: After delivering [{trigger_message.content} from P{trigger_message.sender_id}], "
                    f"{deliverable_count} buffered message(s) can now be delivered: [{msg_list}] | "
                    f"Remaining in buffer: {buffer_size}"
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
    
    def _format_vc_explanation(self, vc, highlight_pid):
        """
        Tạo chuỗi giải thích vector clock với highlight
        
        Args:
            vc: Vector clock
            highlight_pid: Process ID cần highlight
            
        Returns:
            String giải thích
        """
        # Chỉ hiển thị các process có giá trị > 0 hoặc process hiện tại
        important = []
        for i in range(min(15, len(vc))):  # Giới hạn 15 processes
            if vc[i] > 0 or i == highlight_pid:
                marker = "*" if i == highlight_pid else ""
                important.append(f"P{i}:{vc[i]}{marker}")
        
        if len(important) <= 5:
            return f"CurrentVC=[{', '.join(important)}]"
        else:
            # Nếu quá nhiều, chỉ hiển thị 3 đầu + highlight + 2 cuối
            shown = important[:3]
            if highlight_pid not in [i for i in range(3)]:
                shown.append(f"P{highlight_pid}:{vc[highlight_pid]}*")
            shown.extend(important[-2:])
            return f"CurrentVC=[{', '.join(shown)}, ...]"
