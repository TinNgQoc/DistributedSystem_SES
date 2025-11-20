# 🎮 SES ALGORITHM - INTERACTIVE CONTROL PANEL

## 📋 Tổng Quan

Control Panel interactive cho phép bạn:
- ✅ Khởi động và quản lý 15 processes (hoặc tùy chỉnh)
- 📊 Monitor real-time statistics
- 🔍 Xem chi tiết từng process
- 📝 Xem logs và phân tích buffer events
- 🎓 Demo dễ dàng cho giảng viên/trợ giảng

---

## 🚀 Cách Sử Dụng

### Khởi Động Control Panel

```bash
python control_panel_interactive.py
```

### Menu Chính

Khi khởi động, bạn sẽ thấy menu:

```
📋 MAIN MENU

  1. Chạy với config mặc định (15 processes)
  2. Chạy với custom config
  3. Xem hướng dẫn sử dụng
  4. Thoát
```

---

## 🎯 Các Tính Năng

### 1️⃣ Chạy Với Config Mặc Định

**Chọn option 1**

- Khởi động **15 processes**
- Message rate: **10-100 msg/phút**
- Mỗi process mở trong **cửa sổ riêng**
- Cửa sổ chính vẫn để monitor

**Kết quả:**
- 15 cửa sổ console mới (mỗi process một cửa sổ)
- Cửa sổ chính hiển thị monitoring menu

---

### 2️⃣ Chạy Với Custom Config

**Chọn option 2**

Bạn có thể tùy chỉnh:
- **Số processes** (3-30)
- **Message rate min** (msg/phút)
- **Message rate max** (msg/phút)

**Ví dụ:**
```
📊 Số processes (3-30) [mặc định: 15]: 5
⚡ Message rate min (msg/phút) [mặc định: 10]: 20
⚡ Message rate max (msg/phút) [mặc định: 100]: 150
```

Config tùy chỉnh sẽ được lưu vào `config/config_custom.json`

---

### 3️⃣ Monitoring Menu

Sau khi khởi động processes, bạn vào **Monitoring Menu**:

```
📊 MONITORING MENU

  1. Overview - Xem tổng quan
  2. Process Detail - Xem chi tiết process
  3. Refresh - Cập nhật dữ liệu
  4. System Info - Thông tin hệ thống
  5. Help - Hướng dẫn
  6. Stop & Exit - Dừng và thoát
```

---

## 📊 Overview - Tổng Quan Hệ Thống

**Chọn option 1 trong Monitoring Menu**

Hiển thị bảng thống kê toàn hệ thống:

```
┌─────┬────────┬──────────┬───────────┬──────────┬──────────┐
│ PID │  Sent  │ Received │  Direct   │  Buffer  │ Buffered │
├─────┼────────┼──────────┼───────────┼──────────┼──────────┤
│   0 │     69 │       54 │        54 │        0 │        0 │
│   1 │     81 │       48 │        48 │        0 │        0 │
│  11 │     61 │       79 │        78 │        1 │        1 │
│ ... │    ... │      ... │       ... │      ... │      ... │
├─────┼────────┼──────────┼───────────┼──────────┼──────────┤
│ TOT │    919 │      921 │       920 │        1 │        1 │
└─────┴────────┴──────────┴───────────┴──────────┴──────────┘

📊 Vector Times (First 3 processes):
  P0: [123, 127, 114, 126, ...]
  P1: [119, 129, 114, 126, ...]
  P2: [119, 125, 117, 126, ...]

⚠️  Buffer Events: 1 messages buffered
   Recovery Rate: 100.0%
```

### Giải Thích Các Cột

| Cột | Ý Nghĩa |
|-----|---------|
| **PID** | Process ID (0-14) |
| **Sent** | Số messages đã gửi |
| **Received** | Số messages đã nhận |
| **Direct** | Messages delivered trực tiếp (không qua buffer) |
| **Buffer** | Messages delivered từ buffer (sau khi bị buffer) |
| **Buffered** | Số lần message bị buffer vì vi phạm causal order |

### Vector Times

- Hiển thị **vector timestamp** hiện tại của mỗi process
- Cho phép thấy trạng thái logical time của system
- Dùng để kiểm tra causal ordering

---

## 🔍 Process Detail - Chi Tiết Process

**Chọn option 2 trong Monitoring Menu**

Nhập Process ID (0-14) để xem chi tiết:

```
================================================================================
                            PROCESS 11 DETAILS
================================================================================

📊 Statistics:

  Sent:                 61
  Received:             79
  Delivered (Direct):   78
  Delivered (Buffer):    1
  Buffered:              1
  Buffer Checks:         1

⏰ Current Vector Time: [119, 129, 114, 126, 116, 112, 127, 123, 116, 119, 115, 130, 120, 117, 120]

📝 Recent Log Entries (last 15 lines):

  🔶 2025-11-20 16:08:45 - P11 - WARNING - BUFFERED: message 4 from P6...
  🔍 2025-11-20 16:08:45 - P11 - INFO - BUFFER_CHECK: Found 1 deliverable...
  📦 2025-11-20 16:08:45 - P11 - INFO - DELIVERED (BUFFER): message 4 from P6...
     2025-11-20 16:08:46 - P11 - INFO - RECEIVE: message 5 from P7...
     2025-11-20 16:08:46 - P11 - INFO - DELIVERED (DIRECT): message 5 from P7...
```

### Icons Trong Logs

| Icon | Ý Nghĩa |
|------|---------|
| 🔶 | **BUFFERED** - Message bị buffer vì vi phạm causal order |
| ✅ | **DELIVERED (DIRECT)** - Message delivered ngay lập tức |
| 📦 | **DELIVERED (BUFFER)** - Message delivered từ buffer |
| 🔍 | **BUFFER_CHECK** - Kiểm tra buffer sau khi nhận message mới |

---

## 🎓 Giải Thích Cho Giảng Viên

### Causal Message Ordering

**Vấn đề:**
- Trong hệ thống phân tán, messages có thể đến không đúng thứ tự
- Cần đảm bảo: nếu A causally precedes B, thì A phải được deliver trước B

**Giải pháp: SES Algorithm**

1. **Vector Timestamps**: Mỗi process duy trì vector t_P[0..n-1]
2. **V_P Structure**: Dictionary chứa (destination, timestamp) pairs
3. **Delivery Condition**: 
   ```
   Message M có thể deliver tại Process P khi:
   ∀i: V_M[i][i] ≤ t_P[i]
   ```
4. **Buffering**: Nếu vi phạm điều kiện → Buffer cho đến khi thỏa mãn

---

## 📊 Demo Workflow

### Bước 1: Khởi Động

```bash
python control_panel_interactive.py
# Chọn 1 (default config)
```

### Bước 2: Xem Overview

```
Monitoring Menu > Chọn 1 (Overview)
```

**Điểm nhấn:**
- Tổng số messages: ~900-1000
- Buffering rate: ~0.1-0.5% (rất thấp!)
- Recovery rate: 100% (không mất messages)

### Bước 3: Xem Chi Tiết Buffer Event

```
Monitoring Menu > Chọn 2 (Process Detail)
# Nhập process ID có buffer events (xem từ Overview)
```

**Giải thích:**
- Message từ P6 đến P11 bị buffer
- Lý do: V_M[11] > t_P[11] (vi phạm causal order)
- Sau khi nhận message mới, P11 update t_P
- System check buffer, tìm thấy message đã thỏa điều kiện
- Deliver message từ buffer thành công

---

## 💡 Tips Demo

### 1. Highlight Buffering Rate
- Chỉ ~0.1% messages bị buffer
- Chứng minh: Vi phạm causal order rất hiếm

### 2. Emphasize Recovery
- 100% recovery rate
- Không có message loss
- Algorithm đúng đắn

### 3. Show Cascade Delivery
- Một message delivery → trigger buffer check
- Có thể deliver nhiều messages từ buffer (cascade)

### 4. Vector Timestamps
- Xem vector times để thấy logical clock
- Giải thích ý nghĩa từng component

---

## 🔧 Troubleshooting

### Processes không khởi động

**Nguyên nhân:** Ports bị chiếm dụng

**Giải pháp:**
```bash
# Kiểm tra ports
netstat -ano | findstr "5000"

# Hoặc dùng PowerShell
Get-NetTCPConnection -LocalPort 5000
```

### Logs không hiển thị

**Nguyên nhân:** Processes chưa chạy đủ lâu

**Giải pháp:**
- Đợi 10-20 giây trước khi xem Overview
- Chọn option 3 (Refresh) để cập nhật

### Không thấy buffer events

**Nguyên nhân:** Buffering rất hiếm (~0.1%)

**Giải pháp:**
- Chạy lâu hơn (30-60 giây)
- Tăng số processes (option 2)
- Tăng message rate

---

## 📁 File Structure

```
SES_Algorithm/
├── control_panel_interactive.py    # Control panel chính
├── start_all_python.py             # Script khởi động đơn giản
│
├── src/
│   ├── main.py                     # Process entry point
│   ├── ses_process.py              # Process implementation
│   ├── vector_clock.py             # Vector timestamps
│   ├── message_buffer.py           # Buffer management
│   └── logger.py                   # Enhanced logging
│
├── config/
│   ├── config.json                 # Default config
│   └── config_custom.json          # Custom config (tự tạo)
│
└── logs/                            # Log files (tự tạo)
    ├── process_0.log
    ├── process_1.log
    └── ...
```

---

## 🎬 Demo Script Mẫu

### Giới Thiệu (2 phút)

"Hôm nay em sẽ demo **SES Algorithm** - thuật toán đảm bảo **causal ordering** trong hệ thống phân tán.

Em đã tạo một **interactive control panel** để dễ dàng monitor và demo."

### Khởi Động (1 phút)

```bash
python control_panel_interactive.py
# Chọn 1
```

"Control panel sẽ khởi động **15 processes**, mỗi process chạy trong cửa sổ riêng.
Cửa sổ chính vẫn để monitor."

### Overview (2 phút)

```
Monitoring Menu > 1 (Overview)
```

"Đây là tổng quan hệ thống:
- **919 messages** đã gửi
- **921 messages** đã nhận
- Chỉ **1 message (0.1%)** bị buffer
- **100% recovery** - không mất messages

Tỷ lệ buffering thấp chứng minh algorithm hiệu quả!"

### Chi Tiết (2 phút)

```
Monitoring Menu > 2 (Process Detail)
# Nhập 11
```

"Đây là chi tiết Process 11 - process có buffer event:
- Message từ P6 đến P11 bị buffer
- Lý do: **Vector timestamp vi phạm điều kiện**
- Sau đó được **deliver thành công từ buffer**

Đây là cơ chế **cascade delivery**!"

### Kết Luận (1 phút)

"Qua demo, em đã chứng minh:
1. SES algorithm hoạt động đúng
2. Buffering xử lý out-of-order messages hiệu quả
3. Control panel giúp monitor và demo dễ dàng"

---

## ⚡ Keyboard Shortcuts

Trong control panel:
- **1-6**: Chọn menu
- **Enter**: Xác nhận
- **Ctrl+C**: Dừng ngay (nếu cần)

---

## 📧 Support

Nếu có vấn đề:
1. Xem logs trong `logs/`
2. Check ports: `netstat -ano | findstr "5000"`
3. Restart control panel

---

**Chúc demo thành công! 🎉**
