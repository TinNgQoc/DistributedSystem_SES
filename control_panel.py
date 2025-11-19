"""
Control Panel - Terminal điều khiển tập trung cho SES Algorithm
Cho phép xem thống kê và điều khiển tất cả 15 processes từ 1 terminal
"""

import os
import sys
import time
from datetime import datetime
import re

class ControlPanel:
    """
    Control Panel để giám sát và điều khiển các processes
    """
    
    def __init__(self):
        self.logs_dir = os.path.join(os.path.dirname(__file__), "logs")
        self.running = True
    
    def clear_screen(self):
        """Clear màn hình"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self):
        """In header"""
        print("=" * 80)
        print(" " * 20 + "SES ALGORITHM - CONTROL PANEL")
        print(" " * 30 + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("=" * 80)
    
    def get_process_stats(self, process_id):
        """Lấy thống kê từ log file của process"""
        log_file = os.path.join(self.logs_dir, f"process_{process_id}.log")
        
        if not os.path.exists(log_file):
            return {
                'exists': False,
                'sent': 0,
                'received': 0,
                'delivered': 0,
                'buffered': 0,
                'buffer_size': 0,
                'vector_clock': None
            }
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                sent = len(re.findall(r'- INFO - SEND:', content))
                received = len(re.findall(r'- INFO - RECEIVE:', content))
                delivered = len(re.findall(r'- INFO - DELIVERED', content))
                buffered = len(re.findall(r'- WARNING - BUFFERED:', content))
                
                # Tìm Vector Clock cuối cùng
                vc_matches = re.findall(r'CurrentVC=\[([\d, ]+)\]', content)
                vector_clock = vc_matches[-1] if vc_matches else None
                
                # Tìm buffer size cuối cùng
                buffer_matches = re.findall(r'BufferSize=(\d+)', content)
                buffer_size = int(buffer_matches[-1]) if buffer_matches else 0
                
                return {
                    'exists': True,
                    'sent': sent,
                    'received': received,
                    'delivered': delivered,
                    'buffered': buffered,
                    'buffer_size': buffer_size,
                    'vector_clock': vector_clock
                }
        except Exception as e:
            return {
                'exists': True,
                'error': str(e),
                'sent': 0,
                'received': 0,
                'delivered': 0,
                'buffered': 0,
                'buffer_size': 0,
                'vector_clock': None
            }
    
    def show_all_stats(self):
        """Hiển thị thống kê tất cả processes"""
        self.clear_screen()
        self.print_header()
        print()
        print("THỐNG KÊ TẤT CẢ 15 PROCESSES:")
        print("-" * 80)
        print(f"{'ID':<4} {'Sent':<8} {'Recv':<8} {'Delivered':<10} {'Buffered':<10} {'BufSize':<8}")
        print("-" * 80)
        
        total_sent = 0
        total_received = 0
        total_delivered = 0
        total_buffered = 0
        
        for i in range(15):
            stats = self.get_process_stats(i)
            if stats['exists']:
                print(f"P{i:<3} {stats['sent']:<8} {stats['received']:<8} {stats['delivered']:<10} "
                      f"{stats['buffered']:<10} {stats['buffer_size']:<8}")
                total_sent += stats['sent']
                total_received += stats['received']
                total_delivered += stats['delivered']
                total_buffered += stats['buffered']
            else:
                print(f"P{i:<3} {'--':<8} {'--':<8} {'--':<10} {'--':<10} {'--':<8}")
        
        print("-" * 80)
        print(f"TỔNG {total_sent:<8} {total_received:<8} {total_delivered:<10} {total_buffered:<10}")
        print("-" * 80)
        print()
    
    def show_process_detail(self, process_id):
        """Hiển thị chi tiết 1 process"""
        self.clear_screen()
        self.print_header()
        
        stats = self.get_process_stats(process_id)
        
        print()
        print(f"CHI TIẾT PROCESS {process_id}:")
        print("-" * 80)
        
        if not stats['exists']:
            print(f"❌ Log file không tồn tại cho Process {process_id}")
            print(f"    File: {self.logs_dir}\\process_{process_id}.log")
        elif 'error' in stats:
            print(f"❌ Lỗi đọc log: {stats['error']}")
        else:
            print(f"Messages Sent:        {stats['sent']}")
            print(f"Messages Received:    {stats['received']}")
            print(f"Messages Delivered:   {stats['delivered']}")
            print(f"Messages Buffered:    {stats['buffered']}")
            print(f"Current Buffer Size:  {stats['buffer_size']}")
            
            if stats['vector_clock']:
                print(f"\nVector Clock: [{stats['vector_clock']}]")
        
        print("-" * 80)
        print()
    
    def show_vector_clocks(self):
        """Hiển thị vector clock của tất cả processes"""
        self.clear_screen()
        self.print_header()
        print()
        print("VECTOR CLOCKS:")
        print("-" * 80)
        
        for i in range(15):
            stats = self.get_process_stats(i)
            if stats['exists'] and stats['vector_clock']:
                # Chỉ hiển thị một phần vector clock để không quá dài
                vc = stats['vector_clock'].split(',')[:15]
                vc_str = ', '.join(vc)
                print(f"P{i:<2}: [{vc_str}]")
            else:
                print(f"P{i:<2}: Not available")
        
        print("-" * 80)
        print()
    
    def show_buffer_status(self):
        """Hiển thị trạng thái buffer"""
        self.clear_screen()
        self.print_header()
        print()
        print("BUFFER STATUS:")
        print("-" * 80)
        print(f"{'Process':<10} {'Buffer Size':<15} {'Total Buffered':<15}")
        print("-" * 80)
        
        for i in range(15):
            stats = self.get_process_stats(i)
            if stats['exists']:
                status = "⚠️ " if stats['buffer_size'] > 0 else "✓ "
                print(f"{status}P{i:<8} {stats['buffer_size']:<15} {stats['buffered']:<15}")
            else:
                print(f"  P{i:<8} {'--':<15} {'--':<15}")
        
        print("-" * 80)
        print()
    
    def tail_log(self, process_id, lines=20):
        """Hiển thị n dòng cuối của log"""
        self.clear_screen()
        self.print_header()
        
        log_file = os.path.join(self.logs_dir, f"process_{process_id}.log")
        
        print()
        print(f"LOG TAIL - PROCESS {process_id} (Last {lines} lines):")
        print("-" * 80)
        
        if not os.path.exists(log_file):
            print(f"❌ Log file không tồn tại")
        else:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    all_lines = f.readlines()
                    tail_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                    
                    for line in tail_lines:
                        # Tô màu các loại log
                        if 'ERROR' in line:
                            print(f"\033[91m{line.rstrip()}\033[0m")  # Red
                        elif 'WARNING' in line or 'BUFFERED' in line:
                            print(f"\033[93m{line.rstrip()}\033[0m")  # Yellow
                        elif 'DELIVERED' in line:
                            print(f"\033[92m{line.rstrip()}\033[0m")  # Green
                        elif 'SEND' in line:
                            print(f"\033[94m{line.rstrip()}\033[0m")  # Blue
                        elif 'RECEIVE' in line:
                            print(f"\033[95m{line.rstrip()}\033[0m")  # Magenta
                        else:
                            print(line.rstrip())
            except Exception as e:
                print(f"❌ Lỗi đọc file: {e}")
        
        print("-" * 80)
        print()
    
    def show_help(self):
        """Hiển thị help"""
        self.clear_screen()
        self.print_header()
        print()
        print("HƯỚNG DẪN SỬ DỤNG CONTROL PANEL:")
        print("=" * 80)
        print()
        print("  📊 LỆNH XEM THỐNG KÊ:")
        print("    a, all, stats       - Xem thống kê tất cả 15 processes")
        print("    p <id>              - Xem chi tiết process (vd: p 0, p 1)")
        print("    v, vc               - Xem Vector Clocks của tất cả processes")
        print("    b, buffer           - Xem trạng thái Buffer của tất cả processes")
        print()
        print("  📝 LỆNH XEM LOG:")
        print("    l <id>              - Xem 20 dòng cuối log của process (vd: l 0)")
        print("    l <id> <lines>      - Xem n dòng cuối (vd: l 0 50)")
        print()
        print("  🔧 LỆNH KHÁC:")
        print("    r, refresh          - Làm mới màn hình hiện tại")
        print("    h, help             - Hiển thị hướng dẫn này")
        print("    c, clear            - Xóa màn hình")
        print("    q, quit, exit       - Thoát Control Panel")
        print()
        print("=" * 80)
        print()
    
    def run(self):
        """Chạy Control Panel"""
        self.show_help()
        
        last_command = 'all'
        
        while self.running:
            try:
                command = input("Control Panel> ").strip().lower()
                
                if not command:
                    # Repeat last command nếu nhấn Enter
                    command = last_command
                
                parts = command.split()
                cmd = parts[0] if parts else ''
                
                if cmd in ['q', 'quit', 'exit']:
                    print("\n👋 Thoát Control Panel. Tạm biệt!\n")
                    break
                
                elif cmd in ['h', 'help']:
                    self.show_help()
                
                elif cmd in ['a', 'all', 'stats']:
                    self.show_all_stats()
                    last_command = 'all'
                
                elif cmd in ['v', 'vc', 'vector']:
                    self.show_vector_clocks()
                    last_command = 'v'
                
                elif cmd in ['b', 'buffer']:
                    self.show_buffer_status()
                    last_command = 'b'
                
                elif cmd == 'p' and len(parts) > 1:
                    try:
                        pid = int(parts[1])
                        if 0 <= pid <= 14:
                            self.show_process_detail(pid)
                            last_command = f'p {pid}'
                        else:
                            print("❌ Process ID phải từ 0-14")
                    except ValueError:
                        print("❌ Process ID không hợp lệ")
                
                elif cmd == 'l' and len(parts) > 1:
                    try:
                        pid = int(parts[1])
                        lines = int(parts[2]) if len(parts) > 2 else 20
                        if 0 <= pid <= 14:
                            self.tail_log(pid, lines)
                            last_command = f'l {pid} {lines}'
                        else:
                            print("❌ Process ID phải từ 0-14")
                    except ValueError:
                        print("❌ Tham số không hợp lệ")
                
                elif cmd in ['r', 'refresh']:
                    # Refresh last command
                    if last_command:
                        parts = last_command.split()
                        if parts[0] == 'all':
                            self.show_all_stats()
                        elif parts[0] == 'v':
                            self.show_vector_clocks()
                        elif parts[0] == 'b':
                            self.show_buffer_status()
                        elif parts[0] == 'p' and len(parts) > 1:
                            self.show_process_detail(int(parts[1]))
                        elif parts[0] == 'l' and len(parts) > 1:
                            pid = int(parts[1])
                            lines = int(parts[2]) if len(parts) > 2 else 20
                            self.tail_log(pid, lines)
                
                elif cmd in ['c', 'clear']:
                    self.clear_screen()
                
                else:
                    print(f"❌ Lệnh không hợp lệ: '{command}'. Nhập 'h' để xem hướng dẫn.")
                
            except KeyboardInterrupt:
                print("\n\n👋 Nhận Ctrl+C. Thoát Control Panel.\n")
                break
            except Exception as e:
                print(f"❌ Lỗi: {e}")

def main():
    """Main function"""
    print("\n" + "=" * 80)
    print(" " * 25 + "🎛️  SES ALGORITHM CONTROL PANEL")
    print("=" * 80)
    print()
    print("  Terminal tập trung để giám sát và điều khiển 15 processes")
    print("  Bạn có thể xem thống kê, logs, và trạng thái realtime")
    print()
    print("  💡 TIP: Khởi động processes trước bằng: python demo.py")
    print("           hoặc: python start_all_python.py")
    print()
    print("=" * 80)
    input("\nNhấn Enter để bắt đầu...")
    
    panel = ControlPanel()
    panel.run()

if __name__ == "__main__":
    main()
