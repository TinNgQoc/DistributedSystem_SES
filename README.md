# SES Algorithm - Causal Ordering of Messages

Đồ án triển khai thuật toán **SES (Schiper-Eggli-Sandoz)** để đảm bảo thứ tự nhân quả (causal ordering) của messages trong hệ thống phân tán.

## 📋 Mô tả đồ án

Chương trình minh họa cài đặt thuật toán SES với các đặc điểm:
- **15 processes** có thể chạy trên 1 hoặc nhiều máy tính
- Mỗi process tự động gửi **150 messages** đến mỗi process còn lại
- Thời gian phát sinh messages là **ngẫu nhiên** (10-100 messages/phút)
- **Buffering và delivery** messages được hiển thị rõ ràng trên màn hình và log file
- Sử dụng **Vector Clock** để theo dõi quan hệ nhân quả

## 🏗️ Cấu trúc dự án

```
SES_Algorithm/
│
├── config/
│   └── config.json          # Cấu hình 15 processes (IP, port)
│
├── src/
│   ├── main.py             # Chương trình chính
│   ├── ses_process.py      # Logic chính của SES Process
│   ├── vector_clock.py     # Vector Clock implementation
│   ├── message_buffer.py   # Message buffering và ordering
│   └── logger.py           # Logging system
│
├── logs/                   # Thư mục chứa log files (tự động tạo)
│   ├── process_0.log
│   ├── process_1.log
│   └── ...
│
├── start_all.ps1          # Script khởi động tất cả 15 processes
├── start_single.ps1       # Script khởi động 1 process
├── view_logs.ps1          # Script xem log của process
└── README.md              # File này
```

## 🔧 Cài đặt

### Yêu cầu hệ thống
- **Python 3.7+** (đã test với Python 3.8, 3.9, 3.10)
- **Windows** với PowerShell 5.1+
- **RAM**: Tối thiểu 2GB (khuyến nghị 4GB khi chạy 15 processes)

### Cài đặt Python
1. Download Python từ [python.org](https://www.python.org/downloads/)
2. Cài đặt và đảm bảo chọn "Add Python to PATH"
3. Kiểm tra cài đặt:
```powershell
python --version
```

### Không cần cài đặt thêm packages
Chương trình chỉ sử dụng các thư viện có sẵn trong Python standard library:
- `socket` - Network communication
- `threading` - Multi-threading
- `pickle` - Serialization
- `json` - Configuration
- `logging` - Logging system

## 🚀 Cách chạy chương trình

### Phương pháp 1: Chạy tất cả 15 processes cùng lúc (Khuyến nghị cho demo)

```powershell
.\start_all.ps1
```

Script này sẽ:
- Khởi động 15 processes, mỗi process trong một cửa sổ PowerShell riêng
- Tự động xóa log files cũ
- Mỗi process sẽ có màu sắc và vị trí riêng trên màn hình

**Để dừng tất cả processes:**
- Quay lại cửa sổ PowerShell chính và nhấn Enter
- Hoặc đóng từng cửa sổ process

### Phương pháp 2: Chạy từng process riêng lẻ

```powershell
.\start_single.ps1 0    # Chạy process 0
.\start_single.ps1 1    # Chạy process 1
...
.\start_single.ps1 14   # Chạy process 14
```

Hoặc chạy trực tiếp:
```powershell
cd src
python main.py 0
```

### Phương pháp 3: Xem log real-time

```powershell
.\view_logs.ps1 0    # Xem log của process 0
```

Log sẽ hiển thị với màu sắc:
- 🔴 **Đỏ**: Errors
- 🟡 **Vàng**: Buffered messages
- 🟢 **Xanh lá**: Delivered messages
- 🔵 **Xanh dương**: Send messages
- 🟣 **Tím**: Receive messages

## 📊 Tương tác với chương trình

### 🎛️ **Control Panel (Khuyến nghị)** - Terminal điều khiển tập trung

Vì mỗi process liên tục in log ra màn hình, nên khó nhập lệnh trực tiếp. Sử dụng **Control Panel** để giám sát tất cả processes từ 1 terminal:

```powershell
# Terminal 1: Khởi động processes
python demo.py

# Terminal 2: Mở Control Panel
python control_panel.py
```

**Lệnh trong Control Panel:**

| Lệnh | Mô tả |
|------|-------|
| `a` hoặc `all` | Xem thống kê tất cả 15 processes |
| `p <id>` | Xem chi tiết process (vd: `p 0`, `p 1`) |
| `v` hoặc `vc` | Xem Vector Clocks của tất cả processes |
| `b` hoặc `buffer` | Xem trạng thái Buffer |
| `l <id>` | Xem 20 dòng cuối log (vd: `l 0`) |
| `l <id> <lines>` | Xem n dòng cuối (vd: `l 0 50`) |
| `r` hoặc `refresh` | Làm mới màn hình |
| `h` hoặc `help` | Hiển thị hướng dẫn |
| `q` hoặc `quit` | Thoát |

### 💻 Nhập lệnh trực tiếp vào process (Không khuyến nghị)

Nếu chạy process riêng lẻ, bạn có thể nhập lệnh trực tiếp:

| Lệnh | Mô tả |
|------|-------|
| `s` hoặc `stats` | Hiển thị thống kê chi tiết |
| `v` hoặc `vc` | Hiển thị Vector Clock hiện tại |
| `b` hoặc `buffer` | Hiển thị trạng thái Buffer |
| `h` hoặc `help` | Hiển thị hướng dẫn |
| `q` hoặc `quit` | Thoát chương trình |

### Ví dụ output thống kê:

```
============================================================
Statistics for Process 0
============================================================
Messages Sent:                2100
Messages Received:            1850
Messages Delivered:           1820
Current Buffer Size:          30
Total Messages Buffered:      245
Delivered from Buffer:        215
Vector Clock:                 [150, 142, 138, 145, ...]
============================================================
```

## 🔍 Cách hoạt động của thuật toán SES

### 1. Vector Clock
Mỗi process duy trì một vector clock `VC[0..n-1]`:
- `VC[i]` = số lượng events đã xảy ra tại process `i`
- Khi gửi message: `VC[self] += 1`
- Khi nhận message: `VC[i] = max(VC[i], msg_VC[i])` cho mọi `i`

### 2. Điều kiện Delivery

Message `m` từ process `Pi` có thể được deliver tại process `Pj` khi:

```
1. VC_m[i] = VC_j[i] + 1    (message tiếp theo từ sender)
2. VC_m[k] ≤ VC_j[k]        (với mọi k ≠ i)
```

Nếu điều kiện **không thỏa** → Message bị **BUFFERED**

### 3. Ví dụ về Buffering

```
Process P1 gửi:
- Message A với VC=[5, 10, 8]
- Message B với VC=[6, 10, 8]

Process P2 nhận:
- Message B trước (VC_current=[4, 9, 7])
  → Không thể deliver (chờ message A)
  → BUFFERED

- Message A đến (VC_current=[4, 9, 7])
  → Có thể deliver
  → DELIVERED
  → Kiểm tra buffer
  → Message B cũng có thể deliver
  → DELIVERED từ buffer
```

## 📝 Log File Format

Mỗi process có một log file riêng (`logs/process_X.log`) với format:

```
2025-11-19 10:30:45.123456 - P0 - INFO - SEND: message 1 to P1 | MsgVC=[1,0,0,...] | CurrentVC=[1,0,0,...]
2025-11-19 10:30:45.234567 - P0 - INFO - RECEIVE: message 1 from P2 | MsgVC=[0,0,1,...] | CurrentVC=[1,0,0,...]
2025-11-19 10:30:45.345678 - P0 - WARNING - BUFFERED: message 3 from P2 | MsgVC=[0,0,3,...] | BufferSize=1
2025-11-19 10:30:45.456789 - P0 - INFO - DELIVERED (DIRECT): message 1 from P2 | MsgVC=[0,0,1,...] | UpdatedVC=[1,0,1,...]
2025-11-19 10:30:45.567890 - P0 - INFO - DELIVERED (BUFFER): message 3 from P2 | MsgVC=[0,0,3,...] | UpdatedVC=[1,0,3,...]
```

## ⚙️ Cấu hình

File `config/config.json` chứa cấu hình hệ thống:

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

### Chạy trên nhiều máy tính

Để chạy trên nhiều máy:

1. Sửa `host` trong config cho mỗi process:
```json
{"id": 0, "host": "192.168.1.100", "port": 5000},
{"id": 1, "host": "192.168.1.101", "port": 5000},
```

2. Đảm bảo firewall cho phép kết nối qua các port 5000-5014

3. Copy toàn bộ project sang các máy khác

4. Chạy process tương ứng trên mỗi máy:
```powershell
# Máy 1
.\start_single.ps1 0

# Máy 2
.\start_single.ps1 1
```

## 🎯 Demo cho trợ giảng

### Kịch bản demo đầy đủ:

1. **Khởi động tất cả processes:**
```powershell
.\start_all.ps1
```

2. **Chọn một process để theo dõi** (ví dụ Process 0)
   - Trong cửa sổ Process 0, nhấn `s` để xem thống kê

3. **Mở log file trong cửa sổ khác:**
```powershell
.\view_logs.ps1 0
```

4. **Quan sát các hiện tượng:**
   - Messages được SEND
   - Messages được RECEIVE
   - Messages bị BUFFERED (màu vàng trong log)
   - Messages được DELIVERED từ buffer (khi dependencies đã satisfy)
   - Vector Clock được update

5. **Kiểm tra Buffer:**
   - Nhấn `b` để xem trạng thái buffer
   - Thấy số messages đang chờ trong buffer

6. **Kiểm tra Vector Clock:**
   - Nhấn `v` để xem vector clock hiện tại
   - Thấy giá trị clock tăng dần

7. **Xem thống kê cuối cùng:**
   - Chờ một vài phút để processes gửi hết messages
   - Nhấn `s` để xem thống kê
   - Verify: Sent = 14 × 150 = 2100 messages

## 🐛 Troubleshooting

### Lỗi "Address already in use"
- Có process khác đang dùng port 5000-5014
- Giải pháp: Đổi `base_port` trong config hoặc kill process cũ

### Process không kết nối được với nhau
- Kiểm tra firewall
- Kiểm tra IP/port trong config
- Đảm bảo các process đã khởi động đủ

### Messages bị buffer mãi không delivery
- Đây là hành vi bình thường nếu có message bị mất
- Kiểm tra log xem message nào đang chờ
- Verify network connection giữa các processes

### Process bị crash
- Kiểm tra log file để xem error
- Đảm bảo đủ RAM
- Giảm `messages_per_process` hoặc `message_rate` trong config

## 📚 Tài liệu tham khảo

- Schiper, A., Eggli, J., & Sandoz, A. (1989). "A new algorithm to implement causal ordering"
- "Distributed Systems: Principles and Paradigms" - Andrew S. Tanenbaum
- Vector Clocks: https://en.wikipedia.org/wiki/Vector_clock

## 👨‍💻 Thông tin

**Đồ án:** Thuật toán SES - Causal Ordering of Messages  
**Môn học:** Hệ thống phân tán  
**Ngày:** November 2025

## 📞 Hỗ trợ

Nếu có vấn đề khi chạy chương trình:
1. Kiểm tra log files trong thư mục `logs/`
2. Đảm bảo Python 3.7+ đã được cài đặt
3. Kiểm tra firewall và network settings
4. Xem phần Troubleshooting ở trên

---

**Chúc bạn demo thành công! 🎉**
