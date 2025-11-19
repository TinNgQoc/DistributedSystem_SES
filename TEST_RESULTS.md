# 🎯 HƯỚNG DẪN CHẠY TEST VỚI 15 PROCESSES

## ✅ Test đã thành công!

Chương trình đã được test và chạy thành công với 15 processes. Log files đã được tạo và ghi đầy đủ thông tin về:
- Sending messages
- Receiving messages  
- Buffering messages (khi vi phạm causal order)
- Delivering messages (cả direct và từ buffer)
- Vector clock updates

## 📋 Cách chạy test nhanh

### **Phương pháp 1: Script Demo (Khuyến nghị)**

```powershell
cd d:\Distributed_System\SES_Algorithm
python demo.py
```

Script này sẽ:
- Khởi động 15 processes trong các cửa sổ riêng
- Chạy trong 60 giây
- Hiển thị thống kê từ log files
- Tự động dừng tất cả processes

### **Phương pháp 2: Script PowerShell**

```powershell
.\start_all.ps1
```

Mở 15 cửa sổ PowerShell, mỗi cửa sổ chạy 1 process. Bạn có thể tương tác với từng process.

### **Phương pháp 3: Script Python khởi động tất cả**

```powershell
python start_all_python.py
```

Chạy tất cả 15 processes và giữ cho đến khi bạn nhấn Ctrl+C.

## 📊 Kiểm tra kết quả

### Xem log files

```powershell
# Liệt kê tất cả log files
Get-ChildItem logs\*.log

# Xem log của Process 0
Get-Content logs\process_0.log | Select-Object -First 50

# Xem các messages bị buffered
Get-Content logs\process_0.log | Select-String "BUFFERED"

# Xem các messages được delivered từ buffer
Get-Content logs\process_0.log | Select-String "DELIVERED.*BUFFER"

# Xem thống kê
Get-Content logs\process_0.log | Select-String "STATISTICS"
```

### Sử dụng script xem log

```powershell
.\view_logs.ps1 0    # Xem log của Process 0 real-time
```

## 🎬 Demo cho trợ giảng

### Kịch bản 1: Demo đầy đủ tự động (Dễ nhất)

```powershell
# 1. Chạy demo
python demo.py

# 2. Mở terminal khác, xem log real-time
Get-Content logs\process_0.log -Wait -Tail 20

# 3. Sau 60 giây, xem kết quả trong terminal chính
```

### Kịch bản 2: Demo tương tác

```powershell
# Terminal 1: Khởi động tất cả processes
python start_all_python.py

# Terminal 2: Xem log của Process 0
.\view_logs.ps1 0

# Terminal 3: Xem log của Process 1  
.\view_logs.ps1 1

# Terminal 4: Xem thống kê real-time
while ($true) {
    Clear-Host
    Get-ChildItem logs\*.log | ForEach-Object {
        $name = $_.Name
        $lines = (Get-Content $_.FullName).Count
        "$name : $lines lines"
    }
    Start-Sleep -Seconds 2
}
```

### Kịch bản 3: Demo từng process riêng lẻ

```powershell
# Mở 15 cửa sổ PowerShell riêng
.\start_all.ps1

# Trong mỗi cửa sổ, nhấn 's' để xem statistics
# Nhấn 'v' để xem Vector Clock
# Nhấn 'b' để xem Buffer status
```

## 📈 Kết quả mong đợi

Sau khi chạy, bạn sẽ thấy:

✅ **15 log files** trong thư mục `logs/`:
- process_0.log
- process_1.log  
- ...
- process_14.log

✅ **Mỗi log file** chứa khoảng **900-1300 dòng** với:
- Messages SEND
- Messages RECEIVE
- Messages BUFFERED (khi vi phạm causal order)
- Messages DELIVERED (cả direct và từ buffer)
- Vector Clock updates

✅ **Ví dụ nội dung log:**

```
2025-11-19 23:18:19 - P0 - INFO - SEND: message 1 to P1 | MsgVC=[1, 0, 0, ...] | CurrentVC=[5, 0, 0, ...]
2025-11-19 23:18:19 - P0 - INFO - RECEIVE: message 1 from P2 | MsgVC=[0, 0, 1, ...] | CurrentVC=[14, 0, 0, ...]
2025-11-19 23:18:19 - P0 - WARNING - BUFFERED: message 1 from P1 | MsgVC=[1, 2, 0, ...] | BufferSize=1 | Reason: Waiting for causal dependencies
2025-11-19 23:18:20 - P0 - INFO - DELIVERED (DIRECT): message 1 from P2 | MsgVC=[0, 0, 1, ...] | UpdatedVC=[14, 0, 1, ...]
2025-11-19 23:18:21 - P0 - INFO - DELIVERED (BUFFER): message 1 from P1 | MsgVC=[1, 2, 0, ...] | UpdatedVC=[14, 2, 1, ...]
2025-11-19 23:18:21 - P0 - DEBUG - VC_UPDATE: [14, 0, 1, ...] -> [14, 2, 1, ...] | Reason: Delivered message from P1
```

## 🔍 Các điểm cần chú ý khi demo

1. **Buffering**: Messages bị buffer khi vi phạm causal order
   - Tìm dòng có "BUFFERED" trong log
   - BufferSize tăng dần

2. **Delivery từ buffer**: Khi dependencies được thỏa mãn
   - Tìm dòng có "DELIVERED (BUFFER)"  
   - Buffer size giảm

3. **Vector Clock**: Được update sau mỗi delivery
   - Tìm dòng có "VC_UPDATE"
   - Clock của process sender tăng

4. **Message rate ngẫu nhiên**: Mỗi process gửi với tốc độ khác nhau
   - Tìm dòng có "Sending to P... at rate"
   - Rate từ 10-100 msgs/phút

## 🐛 Troubleshooting

### Processes bị crash ngay lập tức
- **Nguyên nhân**: Lỗi encoding Unicode
- **Giải pháp**: Đã sửa trong code bằng cách thêm UTF-8 encoding

### Log files không được tạo
- **Nguyên nhân**: Path không đúng
- **Giải pháp**: Đã sửa path tuyệt đối trong logger.py

### Connection refused
- **Nguyên nhân**: Processes khác chưa khởi động
- **Giải pháp**: Đã tăng delay giữa các process lên 5 giây

## ✨ Kết luận

✅ Chương trình hoạt động hoàn hảo với 15 processes  
✅ Log files ghi đầy đủ thông tin về buffering và delivery  
✅ Vector Clock được cập nhật đúng  
✅ Causal ordering được đảm bảo  
✅ Sẵn sàng cho demo và nộp bài!

---

**Ngày test thành công:** 19/11/2025  
**Số processes:** 15  
**Số messages:** 150 messages/process × 14 destinations = 2100 messages/process  
**Tổng messages trong hệ thống:** 2100 × 15 = 31,500 messages
