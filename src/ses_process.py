"""
SES Process implementation
Process chính thực thi thuật toán SES cho causal ordering
"""

import socket
import threading
import json
import pickle
import time
import random
from vector_clock import VectorClock
from message_buffer import Message, MessageBuffer
from logger import SESLogger

class SESProcess:
    """
    Process trong hệ thống phân tán sử dụng thuật toán SES
    """
    
    def __init__(self, process_id, config):
        """
        Khởi tạo SES Process
        
        Args:
            process_id: ID của process
            config: Configuration dictionary
        """
        self.process_id = process_id
        self.config = config
        self.num_processes = config['num_processes']
        self.messages_per_process = config['messages_per_process']
        
        # Lấy thông tin process từ config
        self.host = config['processes'][process_id]['host']
        self.port = config['processes'][process_id]['port']
        
        # Khởi tạo vector clock
        self.vector_clock = VectorClock(self.num_processes, process_id)
        
        # Khởi tạo logger
        self.logger = SESLogger(process_id)
        
        # Khởi tạo message buffer
        self.message_buffer = MessageBuffer(process_id, self.logger)
        
        # Socket server
        self.server_socket = None
        self.running = False
        
        # Thống kê
        self.sent_count = 0
        self.received_count = 0
        self.delivered_count = 0
        self.message_id_counter = 0
        
        # Lock cho thread safety
        self.vc_lock = threading.Lock()
        self.stats_lock = threading.Lock()
        
        # Lưu trữ các sending threads
        self.sending_threads = []
        
        self.logger.log_event(f"Process {process_id} initialized on {self.host}:{self.port}")
    
    def start(self):
        """
        Khởi động process: bắt đầu server và gửi messages
        """
        self.running = True
        
        # Khởi động server thread để nhận messages
        server_thread = threading.Thread(target=self._start_server, daemon=True)
        server_thread.start()
        
        # Đợi một chút để server khởi động và các process khác cũng ready
        time.sleep(5)
        
        # Khởi động các sender threads cho mỗi process khác
        for target_pid in range(self.num_processes):
            if target_pid != self.process_id:
                sender_thread = threading.Thread(
                    target=self._send_messages_to_process,
                    args=(target_pid,),
                    daemon=True
                )
                sender_thread.start()
                self.sending_threads.append(sender_thread)
        
        self.logger.log_event(f"Process {self.process_id} started with {len(self.sending_threads)} sender threads")
    
    def _start_server(self):
        """
        Khởi động server socket để nhận messages
        """
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(20)
            
            self.logger.log_event(f"Server listening on {self.host}:{self.port}")
            
            while self.running:
                try:
                    self.server_socket.settimeout(1.0)
                    client_socket, address = self.server_socket.accept()
                    # Xử lý mỗi connection trong thread riêng
                    handler_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket,),
                        daemon=True
                    )
                    handler_thread.start()
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        self.logger.log_error(f"Server error: {e}")
                    
        except Exception as e:
            self.logger.log_error(f"Failed to start server: {e}")
    
    def _handle_client(self, client_socket):
        """
        Xử lý connection từ client (nhận message)
        
        Args:
            client_socket: Socket của client
        """
        try:
            # Nhận data
            data = b""
            while True:
                chunk = client_socket.recv(4096)
                if not chunk:
                    break
                data += chunk
                if len(chunk) < 4096:
                    break
            
            if data:
                # Deserialize message
                message = pickle.loads(data)
                self._receive_message(message)
                
        except Exception as e:
            self.logger.log_error(f"Error handling client: {e}")
        finally:
            client_socket.close()
    
    def _send_messages_to_process(self, target_pid):
        """
        Gửi messages đến một process cụ thể
        
        Args:
            target_pid: ID của process đích
        """
        target_host = self.config['processes'][target_pid]['host']
        target_port = self.config['processes'][target_pid]['port']
        
        message_rate = random.randint(
            self.config['message_rate_min'],
            self.config['message_rate_max']
        )
        
        # Tính delay giữa các messages
        delay = 60.0 / message_rate  # seconds per message
        
        self.logger.log_debug(
            f"Sending to P{target_pid} at rate {message_rate} msgs/min (delay={delay:.3f}s)"
        )
        
        for i in range(self.messages_per_process):
            if not self.running:
                break
            
            # Tạo message
            content = f"message {i+1}"
            
            with self.vc_lock:
                # Tăng vector clock trước khi gửi
                self.vector_clock.increment()
                current_vc = self.vector_clock.get_clock()
            
            with self.stats_lock:
                self.message_id_counter += 1
                msg_id = f"P{self.process_id}_M{self.message_id_counter}"
            
            message = Message(
                sender_id=self.process_id,
                receiver_id=target_pid,
                content=content,
                vector_clock=current_vc,
                message_id=msg_id
            )
            
            # Gửi message
            self._send_message(message, target_host, target_port)
            
            # Đợi trước khi gửi message tiếp theo
            time.sleep(delay)
        
        self.logger.log_debug(f"Finished sending {self.messages_per_process} messages to P{target_pid}")
    
    def _send_message(self, message, target_host, target_port):
        """
        Gửi một message qua socket
        
        Args:
            message: Message object cần gửi
            target_host: Host của process đích
            target_port: Port của process đích
        """
        max_retries = 5
        retry_delay = 0.5
        
        for attempt in range(max_retries):
            try:
                # Tạo socket connection
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.settimeout(5.0)
                client_socket.connect((target_host, target_port))
                
                # Serialize và gửi message
                data = pickle.dumps(message)
                client_socket.sendall(data)
                client_socket.close()
                
                # Log và cập nhật thống kê
                with self.vc_lock:
                    current_vc = self.vector_clock.get_clock()
                self.logger.log_send(message, current_vc)
                
                with self.stats_lock:
                    self.sent_count += 1
                
                return True
                
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    # Chỉ log error đầu tiên, sau đó im lặng để tránh spam
                    if attempt == max_retries - 1:
                        pass  # Không log nữa để tránh lỗi logging
                    return False
    
    def _receive_message(self, message):
        """
        Nhận và xử lý message theo thuật toán SES
        
        Args:
            message: Message nhận được
        """
        with self.stats_lock:
            self.received_count += 1
        
        with self.vc_lock:
            current_vc = self.vector_clock.get_clock()
        
        self.logger.log_receive(message, current_vc)
        
        # Kiểm tra xem có thể deliver ngay không
        with self.vc_lock:
            if self.message_buffer.check_deliverable(message, self.vector_clock.get_clock()):
                # Deliver ngay
                self._deliver_message(message, from_buffer=False)
                
                # Kiểm tra buffer xem có messages nào có thể deliver không
                self._check_and_deliver_from_buffer(message)
            else:
                # Phải buffer message
                current_vc = self.vector_clock.get_clock()
                self.message_buffer.add_message(message, current_vc)
    
    def _deliver_message(self, message, from_buffer=False):
        """
        Deliver message và cập nhật vector clock
        
        Args:
            message: Message cần deliver
            from_buffer: True nếu message từ buffer
        """
        # Lưu vector clock cũ
        old_vc = self.vector_clock.get_clock()
        
        # Cập nhật vector clock
        self.vector_clock.update(message.vector_clock)
        new_vc = self.vector_clock.get_clock()
        
        # Log delivery với cả old và new VC
        self.logger.log_delivery(message, old_vc, new_vc, from_buffer)
        
        # Cập nhật thống kê
        with self.stats_lock:
            self.delivered_count += 1
        
        message.delivered = True
    
    def _check_and_deliver_from_buffer(self, trigger_message):
        """
        Kiểm tra buffer và deliver các messages có thể deliver
        
        Args:
            trigger_message: Message vừa được deliver (trigger việc check buffer)
        """
        while True:
            deliverable_messages = self.message_buffer.get_deliverable_messages(
                self.vector_clock.get_clock()
            )
            
            if not deliverable_messages:
                break
            
            self.logger.log_buffer_check(
                trigger_message,
                self.message_buffer.get_buffer_size(),
                len(deliverable_messages),
                deliverable_messages
            )
            
            for msg in deliverable_messages:
                self._deliver_message(msg, from_buffer=True)
                # Update trigger message for next iteration
                trigger_message = msg
    
    def get_statistics(self):
        """
        Lấy thống kê của process
        
        Returns:
            Dictionary chứa thống kê
        """
        with self.stats_lock:
            buffer_stats = self.message_buffer.get_statistics()
            return {
                'process_id': self.process_id,
                'sent': self.sent_count,
                'received': self.received_count,
                'delivered': self.delivered_count,
                'buffer_size': buffer_stats['current_buffer_size'],
                'total_buffered': buffer_stats['total_buffered'],
                'total_delivered_from_buffer': buffer_stats['total_delivered'],
                'vector_clock': self.vector_clock.get_clock()
            }
    
    def print_statistics(self):
        """
        In thống kê ra console
        """
        stats = self.get_statistics()
        print(f"\n{'='*60}")
        print(f"Statistics for Process {self.process_id}")
        print(f"{'='*60}")
        print(f"Messages Sent:                {stats['sent']}")
        print(f"Messages Received:            {stats['received']}")
        print(f"Messages Delivered:           {stats['delivered']}")
        print(f"Current Buffer Size:          {stats['buffer_size']}")
        print(f"Total Messages Buffered:      {stats['total_buffered']}")
        print(f"Delivered from Buffer:        {stats['total_delivered_from_buffer']}")
        print(f"Vector Clock:                 {stats['vector_clock']}")
        print(f"{'='*60}\n")
        
        self.logger.log_statistics(stats)
    
    def stop(self):
        """
        Dừng process
        """
        self.running = False
        
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        self.logger.log_event(f"Process {self.process_id} stopped")
