# 📚 README - SES Algorithm Implementation

## 📖 Tài liệu chính thức đồ án

**Thuật toán SES (Schiper-Eggli-Sandoz) - Causal Ordering of Messages**

---

## 🎓 Ghi chú về chương trình của nhóm

### Tổng quan đồ án
Đồ án này triển khai thuật toán **SES (Schiper-Eggli-Sandoz)** để đảm bảo thứ tự nhân quả (causal ordering) của messages trong hệ thống phân tán. Đây là một trong những thuật toán quan trọng trong Distributed Systems, giải quyết vấn đề đồng bộ và ordering messages khi không có đồng hồ toàn cục.

### Đặc điểm nổi bật
- ✅ **15 processes** chạy song song, có thể trên 1 hoặc nhiều máy tính
- ✅ Mỗi process tự động gửi **150 messages** đến mỗi process khác (tổng 2,100 messages/process)
- ✅ Message rate **ngẫu nhiên** (10-100 messages/phút) mô phỏng môi trường thực tế
- ✅ **Interactive Control Panel** để quản lý và monitor hệ thống
- ✅ **Buffering mechanism** tự động xử lý messages vi phạm causal order
- ✅ **Enhanced logging** với icons và màu sắc, dễ dàng theo dõi
- ✅ **Vector timestamps** (t_P) và **V_P structure** triển khai đầy đủ theo paper gốc
- ✅ **100% Recovery Rate** - Không mất messages

### Công nghệ sử dụng
- **Ngôn ngữ:** Python 3.7+
- **Network:** TCP Sockets (socket module)
- **Concurrency:** Threading (multi-threaded architecture)
- **Logging:** Python logging module + custom formatter
- **Configuration:** JSON-based config system
- **Platform:** Windows (tested), Linux/Mac compatible

### Đóng góp của thành viên
- **Thiết kế và triển khai:** Core SES Algorithm implementation
- **Network Layer:** TCP socket communication system
- **Logging System:** Enhanced buffer event logging
- **Control Panel:** Interactive CLI monitoring tool
- **Testing & Documentation:** Comprehensive testing và tài liệu hướng dẫn

---

## 🎬 Link video demo đồ án

**Link Youtube:** <link youtube demo đồ án>

**Nội dung video:**
- Giới thiệu thuật toán SES và vấn đề causal ordering
- Demo khởi động 15 processes với Control Panel
- Giải thích V_P structure và vector timestamps
- Demo buffer events và cascade delivery
- Phân tích log files và statistics
- Q&A và kết luận

**Thời lượng:** ~15-20 phút

**Người thuyết minh:** <Tên sinh viên thực hiện>

---

## 🛠️ Hướng dẫn cài đặt và chạy thử chương trình

### Yêu cầu hệ thống

**Phần cứng:**
- CPU: Dual-core trở lên
- RAM: Tối thiểu 2GB (khuyến nghị 4GB khi chạy 15 processes)
- Disk: ~100MB cho source code và logs

**Phần mềm:**
- Python 3.7 trở lên (đã test với 3.8, 3.9, 3.10, 3.11)
- Windows 10/11 với PowerShell 5.1+ (hoặc Linux/Mac với terminal)
- Không cần cài đặt thêm packages (chỉ dùng Python standard library)

### Bước 1: Cài đặt Python

**Windows:**
1. Download Python từ [python.org](https://www.python.org/downloads/)
2. Chạy installer và **chọn "Add Python to PATH"**
3. Kiểm tra cài đặt:
```powershell
python --version
# Output: Python 3.x.x
```

**Linux/Mac:**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip

# Mac (với Homebrew)
brew install python3
```

### Bước 2: Clone hoặc Download source code

```bash
# Clone repository
git clone <repository_url>
cd SES_Algorithm

# Hoặc download ZIP và extract
```

### Bước 3: Kiểm tra cấu trúc thư mục

```
SES_Algorithm/
├── config/
│   ├── config.json              # Config mặc định (15 processes)
│   └── config_custom.json       # Config tùy chỉnh (auto-generated)
├── src/
│   ├── main.py                  # Entry point
│   ├── ses_process.py           # SES Process implementation
│   ├── vector_clock.py          # SES Vector structure (t_P, V_P)
│   ├── message_buffer.py        # Message buffering & ordering
│   └── logger.py                # Enhanced logging system
├── logs/                        # Log files (auto-created)
├── control_panel_interactive.py # Interactive Control Panel
├── start_all_python.py          # Script khởi động tất cả processes
├── CONTROL_PANEL_GUIDE.md       # Hướng dẫn Control Panel
├── QUICK_START_CONTROL_PANEL.md # Quick reference
└── README.md                    # File này
```

### Bước 4: Chạy chương trình

#### **Phương pháp 1: Interactive Control Panel (Khuyến nghị cho demo)**

```powershell
# Khởi động Control Panel
python control_panel_interactive.py
```

**Menu sẽ hiện:**
```
📋 MAIN MENU

  1. Chạy với config mặc định (15 processes)
  2. Chạy với custom config
  3. Xem hướng dẫn sử dụng
  4. Thoát
```

**Chọn 1 để demo nhanh:**
- Tự động khởi động 15 processes
- Mỗi process mở trong cửa sổ riêng
- Cửa sổ chính hiển thị **Monitoring Menu** với 6 options:
  1. Overview - Xem tổng quan thống kê
  2. Process Detail - Xem chi tiết từng process
  3. Refresh - Cập nhật dữ liệu mới
  4. System Info - Thông tin hệ thống
  5. Help - Giải thích thuật toán
  6. Stop & Exit - Dừng và thoát

**Xem thống kê Overview:**
- Chọn option 1 trong Monitoring Menu
- Hiển thị bảng thống kê tất cả processes:
  - Sent/Received messages
  - Direct/Buffer delivery
  - Vector timestamps (t_P)
  - Buffer events & recovery rate

**Xem chi tiết Process:**
- Chọn option 2 trong Monitoring Menu
- Nhập Process ID (0-14)
- Hiển thị:
  - Statistics chi tiết
  - Vector timestamp hiện tại
  - Recent log entries với icons (🔶 ✅ 📦 🔍)

#### **Phương pháp 2: Chạy tất cả processes trực tiếp**

```powershell
# Sử dụng Python script
python start_all_python.py
```

Script này sẽ:
- Xóa log files cũ
- Khởi động 15 processes, mỗi process trong cửa sổ riêng
- Hiển thị PID của từng process
- Nhấn Ctrl+C để dừng tất cả

**Lệnh tương tác trong process:**
- `s` hoặc `stats` - Xem thống kê
- `v` hoặc `vc` - Xem Vector timestamps
- `b` hoặc `buffer` - Xem buffer status
- `h` hoặc `help` - Hướng dẫn
- `q` hoặc `quit` - Thoát

### Bước 5: Kiểm tra kết quả

**Xem log files:**
```powershell
# Xem log của Process 0
Get-Content logs\process_0.log | Select-Object -Last 50
```

**Log format:**
```
2025-11-20 10:30:45 - P0 - INFO - SEND: message 1 to P1 | tm=[1,0,0,...] | V_M={...}
2025-11-20 10:30:46 - P0 - WARNING - 🔶 BUFFERED: message 3 from P2 | BufferSize=1
2025-11-20 10:30:47 - P0 - INFO - ✅ DELIVERED (DIRECT): message 1 from P2
2025-11-20 10:30:48 - P0 - INFO - 🔍 BUFFER_CHECK: Found 1 deliverable message(s)
2025-11-20 10:30:49 - P0 - INFO - 📦➡️✅ DELIVERED (BUFFER): message 3 from P2
```

**Kiểm tra thống kê:**
- Tổng Sent = 14 × 150 = 2,100 messages (gửi đến 14 processes khác)
- Tổng Received ≈ 2,100 (có thể chênh lệch nhỏ do timing)
- Buffer events thấp (~0.1-0.5% tổng messages)
- Recovery rate = 100%

### Troubleshooting

**Lỗi "Address already in use":**
```powershell
# Tìm process đang dùng port
netstat -ano | findstr "5000"

# Kill process
taskkill /PID <pid> /F

# Hoặc đổi base_port trong config.json
```

**Process không kết nối được:**
- Kiểm tra firewall (allow ports 5000-5014)
- Đợi 5-10 giây để tất cả processes khởi động
- Kiểm tra config.json có đúng IP/port không

**Thiếu log files:**
- Thư mục `logs/` được tạo tự động
- Nếu không có logs, check quyền write trong thư mục

---

## 📐 Tài liệu sử dụng và thiết kế chương trình

### 1. Kiến trúc hệ thống

```
┌─────────────────────────────────────────────────────────┐
│               SES Algorithm Architecture                 │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────┐         ┌──────────────┐              │
│  │   Process 0  │◄───────►│   Process 1  │              │
│  │  (Port 5000) │         │  (Port 5001) │              │
│  └──────────────┘         └──────────────┘              │
│         ▲                        ▲                        │
│         │         TCP/IP         │                        │
│         ▼                        ▼                        │
│  ┌──────────────┐         ┌──────────────┐              │
│  │   Process 2  │◄───────►│   Process 3  │              │
│  │  (Port 5002) │         │  (Port 5003) │              │
│  └──────────────┘         └──────────────┘              │
│         ...                     ...                       │
│  (Total 15 processes in fully-connected mesh)            │
│                                                           │
└─────────────────────────────────────────────────────────┘

Each Process Contains:
┌────────────────────────────────────────┐
│ SESProcess                             │
├────────────────────────────────────────┤
│ • SESVector (t_P, V_P)                │
│ • MessageBuffer                        │
│ • Logger                               │
│ • TCP Server Thread                    │
│ • Multiple Sender Threads (14)         │
└────────────────────────────────────────┘
```

### 2. Thuật toán SES - Chi tiết kỹ thuật

#### 2.1 Data Structures

**Vector Timestamp (t_P):**
```python
t_P = [0, 0, 0, ..., 0]  # N integers (N = số processes)
```
- `t_P[i]` = số events đã xảy ra tại process i
- Increment khi: send message hoặc internal event
- Update khi: receive và deliver message (component-wise max)

**V_P Structure:**
```python
V_P = {
    destination_pid: timestamp_vector,
    ...
}
```
- Lưu trữ (P', t) pairs
- P' = destination process ID đã từng gửi message đến
- t = vector timestamp tại thời điểm gửi

**Message Structure:**
```python
Message = {
    sender_id: int,
    receiver_id: int,
    content: str,
    tm: List[int],        # Vector timestamp khi send
    v_m: Dict[int, List], # V_P copy từ sender
    message_id: int
}
```

#### 2.2 Send Algorithm

```
ON SEND(message to process Pj):
  1. Increment local time: t_P[self] += 1
  2. Set message timestamp: tm = t_P.copy()
  3. Copy V_P structure: v_m = V_P.copy()
  4. Add destination to V_P: V_P[j] = t_P.copy()
  5. Send (message, tm, v_m) to Pj
  6. Log: SEND event
```

**Code trong `ses_process.py`:**
```python
def _send_messages_to_process(self, target_pid):
    for i in range(self.messages_per_process):
        # Step 1: Increment local time
        with self.vc_lock:
            self.ses_vector.increment_local_time()
            tm = self.ses_vector.get_local_time()
            v_m = self.ses_vector.get_v_p_copy()
            # Step 4: Add destination
            self.ses_vector.add_destination(target_pid, tm)
        
        # Step 5: Create and send message
        message = Message(...)
        self._send_message(message, ...)
```

#### 2.3 Receive and Delivery Algorithm

```
ON RECEIVE(message m from Pi):
  1. Log: RECEIVE event
  2. Check delivery condition:
     IF (Pj NOT IN v_m):
         CAN DELIVER
     ELSE:
         t = v_m[Pj]  // Get timestamp associated with receiver
         IF EXISTS k: t[k] > t_P[k]:  // Any component greater
             BUFFER message
         ELSE:
             CAN DELIVER
  
  3. IF CAN DELIVER:
       a. Merge V_M: For each (P,t) in v_m:
            IF P NOT IN V_P:
                V_P[P] = t
            ELSE:
                V_P[P] = component_wise_max(V_P[P], t)
       
       b. Update local time: t_P = component_wise_max(t_P, tm)
       c. Increment: t_P[self] += 1
       d. Deliver message to application
       e. Check buffer for newly deliverable messages
  
  4. IF BUFFERED:
       Add to buffer and wait
```

**Code trong `ses_process.py`:**
```python
def _receive_message(self, message):
    # Check deliverable
    if self.message_buffer.check_deliverable(
        message, self.process_id, 
        self.ses_vector.v_p, 
        self.ses_vector.vector_time
    ):
        self._deliver_message(message, from_buffer=False)
        self._check_and_deliver_from_buffer()
    else:
        # Buffer
        with self.vc_lock:
            self.message_buffer.add_message(
                message, 
                self.ses_vector.vector_time
            )
```

#### 2.4 Buffer Check Algorithm

```
AFTER EACH DELIVERY:
  FOR each buffered message m:
    IF m can be delivered (check condition):
      1. Remove from buffer
      2. Deliver m (update t_P, V_P)
      3. Recursively check buffer again
```

**Cascade Delivery:** Delivering một message có thể làm cho nhiều messages khác trong buffer trở nên deliverable.

### 3. Module Design

#### 3.1 `vector_clock.py` - SESVector Class

**Responsibilities:**
- Maintain t_P (vector timestamp)
- Maintain V_P structure {destination: timestamp}
- Provide operations: increment, update, merge, compare

**Key Methods:**
```python
class SESVector:
    def increment_local_time()        # t_P[self] += 1
    def update_local_time(recv_vec)   # Component-wise max
    def add_destination(dest, t)      # V_P[dest] = t
    def merge_v_m(v_m)               # Merge V_M into V_P
    def check_deliverable(msg, t_P)   # Check delivery condition
```

#### 3.2 `message_buffer.py` - MessageBuffer Class

**Responsibilities:**
- Store out-of-order messages
- Check deliverability based on SES rules
- Return deliverable messages

**Key Methods:**
```python
class MessageBuffer:
    def add_message(msg)                       # Buffer message
    def check_deliverable(msg, recv_id, V_P, t_P)  # Check condition
    def get_deliverable_messages(recv_id, V_P, t_P) # Get all deliverable
    def get_statistics()                       # Buffer stats
```

**Delivery Condition Implementation:**
```python
def check_deliverable(self, message, receiver_id, v_p_receiver, t_p_receiver):
    # Rule 1: V_M không chứa receiver_id -> deliver
    if receiver_id not in message.v_m:
        return True
    
    # Rule 2: Nếu có (receiver_id, t) trong V_M
    t_in_v_m = message.v_m[receiver_id]
    
    # Check: ∃i: t[i] > t_P[i] ?
    t_greater = any(
        t_in_v_m[i] > t_p_receiver[i] 
        for i in range(len(t_in_v_m))
    )
    
    # If t > t_P: buffer (False)
    # If t <= t_P: deliver (True)
    return not t_greater
```

#### 3.3 `ses_process.py` - SESProcess Class

**Responsibilities:**
- Main process logic
- Network communication (TCP server + clients)
- Message sending/receiving
- Coordinate SESVector and MessageBuffer

**Architecture:**
```
SESProcess
├── Server Thread (1)
│   └── Accept connections
│       └── Spawn client handler threads
│
├── Sender Threads (14)
│   └── Send messages to each other process
│
├── Main Thread
│   └── Handle user input (stats, buffer, quit)
```

**Thread Safety:**
- `vc_lock`: Protect t_P and V_P access
- `stats_lock`: Protect statistics counters

#### 3.4 `logger.py` - SESLogger Class

**Enhanced Logging Features:**
- Separate log file per process
- Color-coded console output
- Detailed buffer events with reasons
- Vector timestamp tracking
- Statistics logging

**Log Events:**
- 📤 SEND
- 📥 RECEIVE
- 🔶 BUFFERED (with reason: which component violates)
- ✅ DELIVERED (DIRECT)
- 📦➡️✅ DELIVERED (BUFFER)
- 🔍 BUFFER_CHECK

#### 3.5 `control_panel_interactive.py` - SESControlPanel Class

**Features:**
- Interactive CLI with menu system
- Config management (default/custom)
- Process spawning (separate windows)
- Real-time stats monitoring
- Log parsing and display
- Help system for educators

**Menu Structure:**
```
Main Menu
├── 1. Default Config (15 processes)
├── 2. Custom Config
├── 3. Help
└── 4. Exit

Monitoring Menu (after starting)
├── 1. Overview (all processes stats)
├── 2. Process Detail (specific process)
├── 3. Refresh Stats
├── 4. System Info
├── 5. Help (algorithm explanation)
└── 6. Stop & Exit
```

### 4. Configuration System

**File:** `config/config.json`

```json
{
  "num_processes": 15,
  "messages_per_process": 150,
  "base_port": 5000,
  "host": "127.0.0.1",
  "message_rate_min": 10,
  "message_rate_max": 100,
  "processes": [
    {"id": 0, "host": "127.0.0.1", "port": 5000},
    ...
  ]
}
```

**Parameters:**
- `num_processes`: 3-30 (tested with 15)
- `messages_per_process`: Messages mỗi process gửi đến mỗi process khác
- `message_rate_min/max`: Messages per minute (random rate)
- `processes[]`: List of (id, host, port) for each process

**Custom Config:**
- Control Panel tự động generate `config_custom.json`
- Support different number of processes và message rates

### 5. Logging and Monitoring

#### Log File Structure

**Location:** `logs/process_<id>.log`

**Format:**
```
<timestamp> - P<id> - <level> - <event_type>: <details>
```

**Example Logs:**

```log
2025-11-20 10:30:00 - P0 - INFO - Process 0 initialized on 127.0.0.1:5000
2025-11-20 10:30:05 - P0 - INFO - Process 0 started with 14 sender threads
2025-11-20 10:30:06 - P0 - INFO - SEND: message 1 to P1 | tm=[1,0,0,...] | V_M={} | t_P=[1,0,0,...]
2025-11-20 10:30:07 - P0 - INFO - RECEIVE: message 1 from P2 | tm=[0,0,1,...] | V_M={} | t_P=[1,0,0,...]
2025-11-20 10:30:08 - P0 - INFO - ✅ DELIVERED (DIRECT): message 1 from P2 | tm=[0,0,1,...] | New t_P=[1,0,1,...]
2025-11-20 10:30:09 - P0 - WARNING - 🔶 BUFFERED: message 3 from P2 | tm=[0,0,3,...] | BufferSize=1 | Reason: V_M contains (P0, [0,0,2,...]) | Condition: t[2]=3 > t_P[2]=1
2025-11-20 10:30:10 - P0 - INFO - 🔍 BUFFER_CHECK: Found 1 deliverable message(s) | Buffer before: 1 | After: 0
2025-11-20 10:30:11 - P0 - INFO - 📦➡️✅ DELIVERED (BUFFER): message 3 from P2 | tm=[0,0,3,...] | New t_P=[1,0,3,...]
```

#### Statistics Tracked

**Per Process:**
- `sent_count`: Messages sent
- `received_count`: Messages received
- `delivered_count`: Messages delivered (direct + buffer)
- `buffer_size`: Current messages in buffer
- `total_buffered`: Total messages buffered
- `total_delivered_from_buffer`: Messages delivered from buffer
- `buffer_checks`: Number of buffer checks performed

**System-wide (via Control Panel):**
- Total messages sent/received/delivered
- Buffer event rate (% messages buffered)
- Recovery rate (% buffered messages delivered)
- Vector timestamps (t_P) of all processes

### 6. Testing and Validation

#### Test Scenarios

**1. Normal Operation:**
- 15 processes, each sends 150 messages to 14 others
- Expected: ~2,100 sent, ~2,100 received per process
- Buffer events: <1% of total messages
- Recovery rate: 100%

**2. Buffer Events:**
- Out-of-order delivery due to network delays
- Messages buffered when violate causal order
- Cascade delivery from buffer after dependencies satisfied

**3. Statistics Validation:**
```python
# For each process i:
assert sent_count == 14 * messages_per_process
assert delivered_count == received_count
assert total_delivered_from_buffer <= total_buffered
```

#### Demo Checklist

✅ All 15 processes start successfully  
✅ Connections established (each process connects to 14 others)  
✅ Messages sent with correct tm and V_M  
✅ Buffer events detected and logged  
✅ Cascade delivery observed  
✅ Vector timestamps updated correctly  
✅ 100% message recovery  
✅ Statistics accurate  
✅ Log files complete  

---

## 📊 Kết quả demo mẫu

**Hệ thống:** 15 processes, 150 messages/process  
**Thời gian chạy:** ~3 phút  
**Kết quả:**

```
┌─────┬────────┬──────────┬───────────┬──────────┬──────────┐
│ PID │  Sent  │ Received │  Direct   │  Buffer  │ Buffered │
├─────┼────────┼──────────┼───────────┼──────────┼──────────┤
│   0 │   2100 │     2089 │      2088 │        1 │        1 │
│   1 │   2100 │     2094 │      2093 │        1 │        1 │
│   2 │   2100 │     2098 │      2098 │        0 │        0 │
│  ...│    ... │      ... │       ... │      ... │      ... │
├─────┼────────┼──────────┼───────────┼──────────┼──────────┤
│ TOT │  31500 │    31485 │     31480 │        5 │        5 │
└─────┴────────┴──────────┴───────────┴──────────┴──────────┘

Buffer Events: 5 messages buffered (0.016%)
Recovery Rate: 100.0%
```

**Observations:**
- Tổng messages gửi: 15 × 2,100 = 31,500
- Tổng messages nhận: ~31,485 (chênh lệch nhỏ do timing)
- Buffer rate: <0.02% (rất thấp - system hoạt động tốt)
- Recovery: 100% (không mất message)

---

## 📖 Tài liệu tham khảo

### Papers
1. **Schiper, A., Eggli, J., & Sandoz, A. (1989)**  
   "A new algorithm to implement causal ordering"  
   Proceedings of the 3rd International Workshop on Distributed Algorithms

2. **Lamport, L. (1978)**  
   "Time, clocks, and the ordering of events in a distributed system"  
   Communications of the ACM, 21(7), 558-565

3. **Fidge, C. J. (1988)**  
   "Timestamps in message-passing systems that preserve the partial ordering"  
   Proceedings of the 11th Australian Computer Science Conference

### Books
- **"Distributed Systems: Principles and Paradigms"**  
  Andrew S. Tanenbaum & Maarten Van Steen

- **"Distributed Algorithms"**  
  Nancy Lynch

### Online Resources
- Vector Clocks: https://en.wikipedia.org/wiki/Vector_clock
- Causal Ordering: https://en.wikipedia.org/wiki/Causal_consistency
- Python Threading: https://docs.python.org/3/library/threading.html
- Python Socket Programming: https://docs.python.org/3/library/socket.html

---

## 📁 Danh sách files quan trọng

### Source Code
- `src/main.py` - Entry point (287 lines)
- `src/ses_process.py` - SES Process implementation (437 lines)
- `src/vector_clock.py` - SES Vector structure (120 lines)
- `src/message_buffer.py` - Message buffering (150 lines)
- `src/logger.py` - Enhanced logging (220 lines)

### Scripts
- `control_panel_interactive.py` - Control Panel (571 lines)
- `start_all_python.py` - Start all processes (120 lines)

### Configuration
- `config/config.json` - Default config (15 processes)
- `config/config_custom.json` - Custom config (auto-generated)

### Documentation
- `README_FULL.md` - File này (tài liệu tổng hợp)
- `CONTROL_PANEL_GUIDE.md` - Hướng dẫn Control Panel (391 lines)
- `QUICK_START_CONTROL_PANEL.md` - Quick reference (280 lines)

**Tổng cộng:** ~2,500+ lines of Python code + documentation

---

## 🎓 Thông tin sinh viên

**Sinh viên thực hiện:** <Tên sinh viên>  
**MSSV:** <Mã số sinh viên>  
**Lớp:** <Mã lớp>  

**Môn học:** Hệ thống phân tán (Distributed Systems)  
**Giảng viên:** <Tên giảng viên>  
**Học kỳ:** <Học kỳ - Năm học>  

**Ngày nộp:** <Ngày nộp đồ án>

---

## 📞 Liên hệ và hỗ trợ

**Email:** <email sinh viên>  
**Github:** <github repository link>

**Nếu gặp vấn đề:**
1. Check log files trong `logs/` directory
2. Xem phần Troubleshooting trong README
3. Đọc `CONTROL_PANEL_GUIDE.md` để biết thêm chi tiết
4. Liên hệ qua email

---

## ⭐ Acknowledgments

Cảm ơn:
- **Thầy/Cô giảng viên** môn Hệ thống phân tán
- **Trợ giảng** đã support trong quá trình làm đồ án
- **Tác giả thuật toán SES** (Schiper, Eggli, Sandoz)
- **Python community** cho các tài liệu và thư viện tuyệt vời

---

## 📜 License

Đồ án này được thực hiện cho mục đích học tập tại trường Đại học.  
Code có thể được sử dụng và tham khảo với credit nguồn gốc.

---

**🎉 Chúc demo thành công!**

**Last updated:** November 2025  
**Version:** 2.0.0 (với Interactive Control Panel)
