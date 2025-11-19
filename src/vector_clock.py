"""
Vector Clock implementation for SES Algorithm
Manages logical time for causal ordering of messages
"""

class VectorClock:
    """
    Vector Clock để theo dõi quan hệ nhân quả giữa các sự kiện
    """
    
    def __init__(self, num_processes, process_id):
        """
        Khởi tạo vector clock
        
        Args:
            num_processes: Số lượng processes trong hệ thống
            process_id: ID của process hiện tại
        """
        self.num_processes = num_processes
        self.process_id = process_id
        self.clock = [0] * num_processes
    
    def increment(self):
        """
        Tăng giá trị clock của process hiện tại khi có sự kiện nội bộ hoặc gửi message
        """
        self.clock[self.process_id] += 1
    
    def update(self, received_clock):
        """
        Cập nhật vector clock khi nhận message từ process khác
        Theo quy tắc: VC[i] = max(VC[i], received_VC[i]) cho mọi i
        
        Args:
            received_clock: Vector clock nhận được từ message
        """
        for i in range(self.num_processes):
            self.clock[i] = max(self.clock[i], received_clock[i])
        # Tăng clock của chính mình
        self.increment()
    
    def get_clock(self):
        """
        Lấy bản sao của vector clock hiện tại
        
        Returns:
            List chứa giá trị vector clock
        """
        return self.clock.copy()
    
    def set_clock(self, clock):
        """
        Đặt vector clock về giá trị cụ thể
        
        Args:
            clock: Vector clock mới
        """
        self.clock = clock.copy()
    
    def __str__(self):
        """
        Biểu diễn string của vector clock
        """
        return str(self.clock)
    
    def __repr__(self):
        return f"VectorClock(pid={self.process_id}, clock={self.clock})"
