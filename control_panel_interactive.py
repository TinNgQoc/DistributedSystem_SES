"""
SES Algorithm - Interactive CLI Control Panel
Quản lý và monitor hệ thống phân tán với giao diện interactive
"""

import subprocess
import sys
import os
import time
import json
import threading
import re
from datetime import datetime
from pathlib import Path

class SESControlPanel:
    """CLI Control Panel cho SES Algorithm"""
    
    def __init__(self):
        self.processes = []
        self.running = False
        self.config = None
        self.num_processes = 0
        self.logs_dir = Path(__file__).parent / "logs"
        self.config_dir = Path(__file__).parent / "config"
        self.src_dir = Path(__file__).parent / "src"
        
        # Stats cache
        self.stats_cache = {}
        self.last_update = None
        
    def clear_screen(self):
        """Xóa màn hình"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self, title):
        """In header đẹp"""
        width = 80
        print("\n" + "=" * width)
        print(f"{title:^{width}}")
        print("=" * width + "\n")
    
    def print_box(self, title, content, width=78):
        """In box có border"""
        print("┌" + "─" * (width - 2) + "┐")
        print(f"│ {title:<{width - 4}} │")
        print("├" + "─" * (width - 2) + "┤")
        for line in content:
            print(f"│ {line:<{width - 4}} │")
        print("└" + "─" * (width - 2) + "┘")
    
    def load_config(self):
        """Load configuration"""
        config_file = self.config_dir / "config.json"
        try:
            with open(config_file, 'r') as f:
                self.config = json.load(f)
            return True
        except Exception as e:
            print(f"❌ Lỗi load config: {e}")
            return False
    
    def save_custom_config(self, num_processes, rate_min, rate_max, max_messages):
        """Tạo config tùy chỉnh"""
        config = {
            "num_processes": num_processes,
            "messages_per_process": max_messages,
            "base_port": 5000,
            "host": "127.0.0.1",
            "message_rate_min": rate_min,
            "message_rate_max": rate_max,
            "processes": []
        }
        
        for i in range(num_processes):
            config["processes"].append({
                "id": i,
                "host": "127.0.0.1",
                "port": 5000 + i
            })
        
        # Save to file
        custom_config = self.config_dir / "config_custom.json"
        with open(custom_config, 'w') as f:
            json.dump(config, f, indent=2)
        
        return config
    
    def show_main_menu(self):
        """Hiển thị menu chính"""
        self.clear_screen()
        self.print_header("SES ALGORITHM - CONTROL PANEL")
        
        print("📋 MAIN MENU\n")
        print("  1. Chạy với config mặc định (15 processes)")
        print("  2. Chạy với custom config")
        print("  3. Xem hướng dẫn sử dụng")
        print("  4. Thoát\n")
        
        choice = input("👉 Chọn (1-4): ").strip()
        return choice
    
    def show_custom_config_menu(self):
        """Menu config tùy chỉnh"""
        self.clear_screen()
        self.print_header("CUSTOM CONFIGURATION")
        
        print("⚙️  Cấu hình hệ thống\n")
        
        # Số processes
        while True:
            try:
                num = input("📊 Số processes (2-30) [mặc định: 15]: ").strip()
                if not num:
                    num_processes = 15
                    break
                num_processes = int(num)
                if 2 <= num_processes <= 30:
                    break
                print("   ⚠️  Phải từ 3 đến 30 processes!")
            except ValueError:
                print("   ⚠️  Vui lòng nhập số!")
        
        # Message rate min
        while True:
            try:
                rate = input("⚡ Message rate min (msg/phút) [mặc định: 10]: ").strip()
                if not rate:
                    rate_min = 10
                    break
                rate_min = int(rate)
                if rate_min > 0:
                    break
                print("   ⚠️  Phải lớn hơn 0!")
            except ValueError:
                print("   ⚠️  Vui lòng nhập số!")
        
        # Message rate max
        while True:
            try:
                rate = input("⚡ Message rate max (msg/phút) [mặc định: 100]: ").strip()
                if not rate:
                    rate_max = 100
                    break
                rate_max = int(rate)
                if rate_max >= rate_min:
                    break
                print(f"   ⚠️  Phải >= {rate_min}!")
            except ValueError:
                print("   ⚠️  Vui lòng nhập số!")
        
        # Max messages per process
        while True:
            try:
                msgs = input("📨 Số message tối đa mỗi process (10-1000) [mặc định: 150]: ").strip()
                if not msgs:
                    max_messages = 150
                    break
                max_messages = int(msgs)
                if 10 <= max_messages <= 1000:
                    break
                print("   ⚠️  Phải từ 10 đến 1000 messages!")
            except ValueError:
                print("   ⚠️  Vui lòng nhập số!")
        
        print(f"\n✅ Config: {num_processes} processes, {max_messages} msgs/process, rate {rate_min}-{rate_max} msg/phút\n")
        
        confirm = input("Xác nhận? (y/n): ").strip().lower()
        if confirm == 'y':
            return num_processes, rate_min, rate_max, max_messages
        return None
    
    def start_processes(self, use_custom=False, custom_params=None):
        """Khởi động các processes"""
        self.clear_screen()
        self.print_header("STARTING PROCESSES")
        
        # Load hoặc tạo config
        if use_custom and custom_params:
            num_processes, rate_min, rate_max, max_messages = custom_params
            self.config = self.save_custom_config(num_processes, rate_min, rate_max, max_messages)
            config_file = "config_custom.json"
        else:
            if not self.load_config():
                return False
            config_file = "config.json"
        
        self.num_processes = self.config['num_processes']
        
        # Tạo logs directory
        self.logs_dir.mkdir(exist_ok=True)
        
        # Xóa logs cũ
        print("🧹 Đang xóa logs cũ...")
        for i in range(self.num_processes):
            log_file = self.logs_dir / f"process_{i}.log"
            if log_file.exists():
                log_file.unlink()
        
        print(f"🚀 Đang khởi động {self.num_processes} processes...\n")
        
        # Khởi động processes
        for i in range(self.num_processes):
            try:
                if sys.platform == 'win32':
                    CREATE_NEW_CONSOLE = 0x00000010
                    proc = subprocess.Popen(
                        [sys.executable, "main.py", str(i), config_file],
                        cwd=str(self.src_dir),
                        creationflags=CREATE_NEW_CONSOLE
                    )
                else:
                    proc = subprocess.Popen(
                        [sys.executable, "main.py", str(i), config_file],
                        cwd=str(self.src_dir)
                    )
                
                self.processes.append(proc)
                print(f"  ✅ Process {i:2d} started (PID: {proc.pid})")
                time.sleep(0.2)
                
            except Exception as e:
                print(f"  ❌ Process {i} failed: {e}")
        
        self.running = True
        print(f"\n✅ Đã khởi động {len(self.processes)}/{self.num_processes} processes!")
        print("\n⏳ Đang chờ processes khởi tạo...")
        time.sleep(3)
        
        return True
    
    def stop_processes(self):
        """Dừng tất cả processes"""
        print("\n🛑 Đang dừng processes...")
        
        for i, proc in enumerate(self.processes):
            if proc.poll() is None:
                try:
                    proc.terminate()
                    print(f"  ⏹️  Process {i} stopped")
                except:
                    pass
        
        time.sleep(2)
        
        # Force kill nếu cần
        for proc in self.processes:
            if proc.poll() is None:
                try:
                    proc.kill()
                except:
                    pass
        
        self.processes.clear()
        self.running = False
        print("✅ Tất cả processes đã dừng!\n")
    
    def parse_log_stats(self, log_content):
        """Parse thống kê từ log"""
        stats = {
            'sent': 0,
            'received': 0,
            'delivered_direct': 0,
            'delivered_buffer': 0,
            'buffered': 0,
            'buffer_checks': 0,
            'vector_time': None
        }
        
        # Count messages
        stats['delivered_direct'] = log_content.count('DELIVERED (DIRECT)')
        stats['delivered_buffer'] = log_content.count('DELIVERED (BUFFER)')
        stats['buffered'] = log_content.count('BUFFERED')
        stats['buffer_checks'] = log_content.count('BUFFER_CHECK')
        stats['sent'] = log_content.count('SEND:')
        stats['received'] = log_content.count('RECEIVE:')
        
        # Get latest vector time
        vector_matches = re.findall(r'New t_P=\[([\d,\s]+)\]', log_content)
        if vector_matches:
            last_vector = vector_matches[-1]
            stats['vector_time'] = [int(x.strip()) for x in last_vector.split(',')]
        
        return stats
    
    def update_stats(self):
        """Cập nhật thống kê từ logs"""
        stats = {}
        
        for i in range(self.num_processes):
            log_file = self.logs_dir / f"process_{i}.log"
            if log_file.exists():
                try:
                    content = log_file.read_text(encoding='utf-8', errors='ignore')
                    stats[i] = self.parse_log_stats(content)
                except Exception as e:
                    stats[i] = None
            else:
                stats[i] = None
        
        self.stats_cache = stats
        self.last_update = datetime.now()
    
    def show_overview(self):
        """Hiển thị overview"""
        self.clear_screen()
        self.print_header("SYSTEM OVERVIEW")
        
        # Update stats
        self.update_stats()
        
        print(f"⏰ Last update: {self.last_update.strftime('%H:%M:%S')}\n")
        
        # Summary table
        print("┌─────┬────────┬──────────┬───────────┬──────────┬──────────┐")
        print("│ PID │  Sent  │ Received │ D.Direct  │ D.Buffer │ Buffered │")
        print("├─────┼────────┼──────────┼───────────┼──────────┼──────────┤")
        
        total_sent = 0
        total_received = 0
        total_direct = 0
        total_buffer = 0
        total_buffered = 0
        
        for i in range(self.num_processes):
            stats = self.stats_cache.get(i)
            if stats:
                sent = stats['sent']
                received = stats['received']
                direct = stats['delivered_direct']
                buffer = stats['delivered_buffer']
                buffered = stats['buffered']
                
                total_sent += sent
                total_received += received
                total_direct += direct
                total_buffer += buffer
                total_buffered += buffered
                
                print(f"│ {i:3d} │ {sent:6d} │ {received:8d} │ {direct:9d} │ {buffer:8d} │ {buffered:8d} │")
            else:
                print(f"│ {i:3d} │    N/A │      N/A │       N/A │      N/A │      N/A │")
        
        print("├─────┼────────┼──────────┼───────────┼──────────┼──────────┤")
        print(f"│ TOT │{total_sent:7d} │{total_received:9d} │{total_direct:10d} │{total_buffer:9d} │{total_buffered:9d} │")
        print("└─────┴────────┴──────────┴───────────┴──────────┴──────────┘")
        
        # Vector times (sample first 3 processes)
        print("\n📊 Vector Times (First 3 processes):\n")
        for i in range(min(3, self.num_processes)):
            stats = self.stats_cache.get(i)
            if stats and stats['vector_time']:
                vt = stats['vector_time']
                vt_str = str(vt[:8]) + "..." if len(vt) > 8 else str(vt)
                print(f"  P{i}: {vt_str}")
        
        # Buffer statistics
        if total_buffered > 0:
            print(f"\n⚠️  Buffer Events: {total_buffered} messages buffered")
            print(f"   Recovery Rate: {100*total_buffer/total_buffered:.1f}%")
        else:
            print("\n✅ No buffering (perfect causal ordering!)")
        
        print("\n" + "─" * 80)
    
    def show_process_detail(self, pid):
        """Hiển thị chi tiết một process"""
        self.clear_screen()
        self.print_header(f"PROCESS {pid} DETAILS")
        
        log_file = self.logs_dir / f"process_{pid}.log"
        
        if not log_file.exists():
            print(f"❌ Log file không tồn tại cho Process {pid}\n")
            return
        
        try:
            content = log_file.read_text(encoding='utf-8', errors='ignore')
            stats = self.parse_log_stats(content)
            
            # Statistics
            print(f"📊 Statistics:\n")
            print(f"  Sent:              {stats['sent']:>6d}")
            print(f"  Received:          {stats['received']:>6d}")
            print(f"  Delivered (Direct):{stats['delivered_direct']:>6d}")
            print(f"  Delivered (Buffer):{stats['delivered_buffer']:>6d}")
            print(f"  Buffered:          {stats['buffered']:>6d}")
            print(f"  Buffer Checks:     {stats['buffer_checks']:>6d}")
            
            if stats['vector_time']:
                print(f"\n⏰ Current Vector Time: {stats['vector_time']}")
            
            # Recent log entries
            print(f"\n📝 Recent Log Entries (last 15 lines):\n")
            lines = content.split('\n')
            recent = lines[-15:] if len(lines) > 15 else lines
            
            for line in recent:
                if line.strip():
                    # Colorize important keywords
                    if 'BUFFERED' in line:
                        print(f"  🔶 {line[:120]}")
                    elif 'BUFFER_CHECK' in line:
                        print(f"  🔍 {line[:120]}")
                    elif 'DELIVERED (BUFFER)' in line:
                        print(f"  📦 {line[:120]}")
                    elif 'ERROR' in line:
                        print(f"  ❌ {line[:120]}")
                    else:
                        print(f"     {line[:120]}")
            
        except Exception as e:
            print(f"❌ Lỗi đọc log: {e}\n")
        
        print("\n" + "─" * 80)
    
    def show_help(self):
        """Hiển thị hướng dẫn"""
        self.clear_screen()
        self.print_header("HƯỚNG DẪN SỬ DỤNG")
        
        help_text = [
            "",
            "🎯 MỤC ĐÍCH:",
            "  Demo thuật toán SES (Schiper-Eggli-Sandoz) cho causal message ordering",
            "  trong hệ thống phân tán.",
            "",
            "🔧 CÁC THÀNH PHẦN:",
            "  • Process: Mỗi process là một node trong hệ thống phân tán",
            "  • Vector Timestamp: Đảm bảo causal ordering",
            "  • Message Buffer: Lưu messages vi phạm causal order",
            "  • Enhanced Logging: Ghi lại chi tiết các events",
            "",
            "📊 GIẢI THÍCH CHỈ SỐ:",
            "  • Sent: Số messages đã gửi",
            "  • Received: Số messages đã nhận",
            "  • Direct: Messages delivered ngay lập tức",
            "  • Buffer: Messages delivered từ buffer (sau khi buffered)",
            "  • Buffered: Messages bị buffer vì vi phạm causal order",
            "",
            "🔍 ICONS TRONG LOG:",
            "  🔶 BUFFERED - Message bị buffer",
            "  ✅ DELIVERED (DIRECT) - Delivery trực tiếp",
            "  📦 DELIVERED (BUFFER) - Delivery từ buffer",
            "  🔍 BUFFER_CHECK - Kiểm tra buffer",
            "",
            "⚙️  ĐIỀU KIỆN DELIVERY:",
            "  Message M có thể deliver tại Process P khi:",
            "  ∀i: V_M[i][i] ≤ t_P[i]",
            "  ",
            "  Nếu vi phạm → Buffer cho đến khi điều kiện thỏa mãn",
            "",
            "💡 TIPS DEMO:",
            "  1. Chạy với default config trước để làm quen",
            "  2. Xem Overview để thấy tổng quan hệ thống",
            "  3. Xem Process Detail để thấy chi tiết buffering",
            "  4. Tỷ lệ buffering thấp (~0.01%) là bình thường",
            "  5. 100% recovery rate chứng minh algorithm đúng",
            "",
        ]
        
        for line in help_text:
            print(line)
        
        print("─" * 80)
    
    def show_system_info(self):
        """Hiển thị thông tin hệ thống"""
        info = [
            f"Config: {self.num_processes} processes",
            f"Ports: {5000} - {5000 + self.num_processes - 1}",
            f"Logs: {self.logs_dir}",
            f"Running: {len([p for p in self.processes if p.poll() is None])} active"
        ]
        self.print_box("System Info", info)
    
    def monitor_menu(self):
        """Menu monitoring sau khi start processes"""
        while self.running:
            print("\n📊 MONITORING MENU\n")
            print("  1. Overview - Xem tổng quan")
            print("  2. Process Detail - Xem chi tiết process")
            print("  3. Refresh - Cập nhật dữ liệu")
            print("  4. System Info - Thông tin hệ thống")
            print("  5. Help - Hướng dẫn")
            print("  6. Stop & Exit - Dừng và thoát\n")
            
            choice = input("👉 Chọn (1-6): ").strip()
            
            if choice == '1':
                self.show_overview()
                input("\n⏸️  Press Enter to continue...")
            
            elif choice == '2':
                pid = input("Enter Process ID (0-{}): ".format(self.num_processes - 1))
                try:
                    pid = int(pid)
                    if 0 <= pid < self.num_processes:
                        self.show_process_detail(pid)
                        input("\n⏸️  Press Enter to continue...")
                    else:
                        print("❌ Invalid Process ID!")
                        time.sleep(1)
                except ValueError:
                    print("❌ Invalid input!")
                    time.sleep(1)
            
            elif choice == '3':
                print("\n♻️  Refreshing...")
                self.update_stats()
                time.sleep(1)
            
            elif choice == '4':
                self.clear_screen()
                self.print_header("SYSTEM INFORMATION")
                self.show_system_info()
                input("\n⏸️  Press Enter to continue...")
            
            elif choice == '5':
                self.show_help()
                input("\n⏸️  Press Enter to continue...")
            
            elif choice == '6':
                self.stop_processes()
                break
            
            else:
                print("❌ Lựa chọn không hợp lệ!")
                time.sleep(1)
    
    def run(self):
        """Chạy control panel"""
        try:
            while True:
                choice = self.show_main_menu()
                
                if choice == '1':
                    # Default config
                    if self.start_processes(use_custom=False):
                        self.monitor_menu()
                
                elif choice == '2':
                    # Custom config
                    params = self.show_custom_config_menu()
                    if params:
                        if self.start_processes(use_custom=True, custom_params=params):
                            self.monitor_menu()
                
                elif choice == '3':
                    # Help
                    self.show_help()
                    input("\n⏸️  Press Enter to continue...")
                
                elif choice == '4':
                    # Exit
                    if self.running:
                        self.stop_processes()
                    print("\n👋 Goodbye!\n")
                    break
                
                else:
                    print("\n❌ Lựa chọn không hợp lệ!")
                    time.sleep(1)
        
        except KeyboardInterrupt:
            print("\n\n⚠️  Keyboard interrupt detected!")
            if self.running:
                self.stop_processes()
            print("\n👋 Goodbye!\n")
        
        except Exception as e:
            print(f"\n❌ Lỗi: {e}")
            if self.running:
                self.stop_processes()


def main():
    """Entry point"""
    panel = SESControlPanel()
    panel.run()


if __name__ == "__main__":
    main()
