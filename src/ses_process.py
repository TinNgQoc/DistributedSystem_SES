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
from vector_clock import SESVector
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
        
        # Khởi tạo SES Vector structure
        self.ses_vector = SESVector(self.num_processes, process_id)
        
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
        Gửi messages đến một process cụ thể theo SES Algorithm
        
        SES Send Protocol:
        1. Increment vector timestamp
        2. Get tm = current vector timestamp
        3. Prepare V_M = V_P excluding (target_pid, t)
        4. Send message with tm and V_M
        5. Add (target_pid, tm) to V_P (not sent in message!)
        
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
            
            # Tạo message theo SES protocol
            content = f"message {i+1}"
            
            with self.vc_lock:
                # Increment vector timestamp before sending
                self.ses_vector.increment_local_time()
                tm = self.ses_vector.get_local_time()  # Get vector copy
                
                # Get V_M = full copy of V_P BEFORE adding destination
                # This is the key: V_M includes all entries in V_P except the one being added now
                v_m = self.ses_vector.get_v_p_copy()
                
                # Add (target_pid, tm) to V_P AFTER preparing V_M (not sent in message)
                self.ses_vector.add_destination(target_pid, tm)
            
            with self.stats_lock:
                self.message_id_counter += 1
                msg_id = f"P{self.process_id}_M{self.message_id_counter}"
            
            message = Message(
                sender_id=self.process_id,
                receiver_id=target_pid,
                content=content,
                tm=tm,
                v_m=v_m,
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
                    current_t = self.ses_vector.get_local_time()
                self.logger.log_send(message, current_t)
                
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
        
        SES Receive/Deliver Protocol:
        1. If V_M does not contain (receiver_id, t): deliver message
        2. If V_M contains (receiver_id, t):
           - If tm > t_receiver: buffer message (don't deliver)
           - If tm <= t_receiver: deliver message
        3. When delivering:
           - Merge V_M with V_P
           - Update local clock
           - Check buffered messages
        
        Args:
            message: Message nhận được
        """
        with self.stats_lock:
            self.received_count += 1
        
        with self.vc_lock:
            current_t = self.ses_vector.get_local_time()
            current_v_p = self.ses_vector.get_v_p_copy()
        
        self.logger.log_receive(message, current_t)
        
        # Kiểm tra xem có thể deliver ngay không theo SES rules
        with self.vc_lock:
            if self.message_buffer.check_deliverable(
                message, 
                self.process_id, 
                self.ses_vector.get_v_p_copy(),
                self.ses_vector.get_local_time()
            ):
                # Deliver ngay
                self._deliver_message(message, from_buffer=False)
                
                # Kiểm tra buffer xem có messages nào có thể deliver không
                self._check_and_deliver_from_buffer()
            else:
                # Phải buffer message
                self.message_buffer.add_message(message)
    
    def _deliver_message(self, message, from_buffer=False):
        """
        Deliver message và cập nhật theo SES algorithm
        
        When delivering:
        1. Merge V_M with V_P (component-wise maximum)
        2. Update vector timestamp (component-wise max + increment)
        3. Check buffered messages for delivery
        
        Args:
            message: Message cần deliver
            from_buffer: True nếu message từ buffer
        """
        # Get old state for logging
        old_t = self.ses_vector.get_local_time()
        old_v_p = self.ses_vector.get_v_p_copy()
        
        # Merge V_M from message with local V_P
        self.ses_vector.merge_v_m(message.v_m)
        
        # Update vector timestamp (standard vector clock update)
        self.ses_vector.update_local_time(message.tm)
        
        new_t = self.ses_vector.get_local_time()
        new_v_p = self.ses_vector.get_v_p_copy()
        
        # Log delivery
        self.logger.log_delivery(message, new_t, from_buffer)
        self.logger.log_vc_update(old_t, new_t, f"Delivered message from P{message.sender_id}")
        
        # Cập nhật thống kê
        with self.stats_lock:
            self.delivered_count += 1
        
        message.delivered = True
    
    def _check_and_deliver_from_buffer(self):
        """
        Kiểm tra buffer và deliver các messages có thể deliver
        Message is not delivered until t in V_M is less than t in V_P
        """
        iteration = 0
        while True:
            iteration += 1
            buffer_size_before = self.message_buffer.get_buffer_size()
            
            # Nếu buffer rỗng, không cần kiểm tra
            if buffer_size_before == 0:
                break
            
            deliverable_messages = self.message_buffer.get_deliverable_messages(
                self.process_id,
                self.ses_vector.get_v_p_copy(),
                self.ses_vector.get_local_time()
            )
            
            if not deliverable_messages:
                # Log khi buffer còn messages nhưng chưa thể deliver
                if buffer_size_before > 0:
                    current_t = self.ses_vector.get_local_time()
                    self.logger.log_buffer_check(buffer_size_before, 0, current_t)
                break
            
            # Log kiểm tra buffer thành công
            current_t = self.ses_vector.get_local_time()
            self.logger.log_buffer_check(
                buffer_size_before, 
                len(deliverable_messages),
                current_t
            )
            
            # Deliver tất cả messages có thể deliver
            for msg in deliverable_messages:
                self._deliver_message(msg, from_buffer=True)
    
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
                'vector_time': self.ses_vector.get_local_time(),
                'v_p_size': len(self.ses_vector.v_p)
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
        print(f"Vector Time:                  {stats['vector_time']}")
        print(f"V_P Size:                     {stats['v_p_size']}")
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
