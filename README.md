# Hướng dẫn cài đặt và sử dụng — Quản lý lịch cá nhân (VN)

## 1. Yêu cầu hệ thống

- **Python**: 3.8 trở lên (khuyến nghị 3.10+)
- **Hệ điều hành**: Windows / macOS / Linux
- **Trình duyệt**: Chrome, Firefox, Edge, Safari (hỗ trợ ES6 + Fetch API)

## 2. Cài đặt

### 2.1 Clone hoặc tải dự án

Nếu chưa có, tải/clone dự án vào máy:
```bash
git clone https://github.com/Mthanh1501/NPL_DACN.git

```


### 2.2 Tạo và kích hoạt virtualenv (khuyến nghị)

**Trên Windows (PowerShell):**
```powershell
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
```

**Trên macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Sau khi kích hoạt, dòng lệnh sẽ có dấu `(.venv)` ở đầu.

### 2.3 Cài đặt dependencies

```powershell
pip install -r requirements.txt
```

Dòng lệnh này sẽ cài:
- `Flask` — framework web
- `dateparser` — phân tích chuỗi thời gian

## 3. Cấu trúc thư mục

```
TODO/
├── app.py                      # Backend (Flask server)
├── requirements.txt            # Danh sách thư viện cần cài
├── .gitignore                  # Quy tắc bỏ qua file/thư mục khi push git
├── GUIDE.md                    # File hướng dẫn này
├── test_events.py              # Script kiểm thử nhanh
│
├── nlp/                        # Package xử lý ngôn ngữ tự nhiên
│   ├── __init__.py
│   └── parser.py               # Hàm chính: parse_event()
│
├── templates/
│   └── index.html              # Giao diện web (HTML + CSS + JS)
│
├── data/
│   └── events.json             # File lưu dữ liệu events (runtime)
│
└── __pycache__/                # Cache bytecode Python (tự động tạo)
```

## 4. Chạy ứng dụng

### 4.1 Khởi động server

Từ thư mục dự án (với virtualenv kích hoạt):
```powershell
python app.py
```

Bạn sẽ thấy output tương tự:
```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

### 4.2 Mở giao diện web

Mở trình duyệt (Chrome, Firefox, v.v.) và truy cập:
```
http://127.0.0.1:5000/
```

Giao diện sẽ hiện:
- Ô nhập văn bản (textarea)
- Nút "Phân tích & Thêm sự kiện"
- Bảng danh sách sự kiện
- Các nút hành động (Xóa, Xuất, Nhập file)

### 4.3 Dừng server

Nhấn **Ctrl+C** trong terminal để dừng Flask.

## 5. Hướng dẫn sử dụng

### 5.1 Thêm sự kiện mới

1. **Nhập câu tiếng Việt** vào ô textarea. Ví dụ:
   ```
   Lên lịch phỏng vấn thực tập lúc 15h ngày 12/12 tại phòng nhân sự, nhắc trước 20 phút.
   ```

2. Nhấn nút **"Phân tích & Thêm sự kiện"**.

3. Hệ thống sẽ:
   - Phân tích câu → trích thời gian, địa điểm, tên sự kiện, nhắc trước.
   - Hiển thị kết quả phân tích.
   - Thêm vào bảng danh sách.
   - Xóa ô nhập.

### 5.2 Định dạng câu nhập (ví dụ)

Hệ thống hỗ trợ các mẫu câu linh hoạt (tiếng Việt tự do):

| Loại sự kiện | Ví dụ |
|---|---|
| **Thời gian tuyệt đối** | "Họp lúc 10h ngày 8/12" → `2025-12-08T10:00:00` |
| **Thời gian tương đối** | "Lúc 5 phút nữa", "3 giờ nữa" → `now + duration` |
| **Ngày trong tuần** | "Thứ Năm tuần này", "Chủ nhật", "Thứ Sáu tuần tới" |
| **Bộ phận ngày** | "Sáng", "Trưa", "Chiều", "Tối" → mặc định giờ |
| **Địa điểm: Phòng** | "Tại phòng nhân sự", "ở phòng 302" → `Phòng Nhân Sự` |
| **Địa điểm: Địa chỉ** | "Tại 123 Nguyễn Huệ, TP HCM" → `123 Nguyễn Huệ...` |
| **Địa điểm: Tỉnh/Thành phố** | "Ở Hà Nội", "Đà Nẵng" → tên tỉnh |
| **Nhắc trước** | "Nhắc trước 20 phút" → `reminder_minutes: 20` |

**Mẹo**: Bạn có thể kết hợp các thành phần trên trong một câu tự do:
```
Nhắc tôi họp báo cáo tiến độ lúc 10h thứ Sáu tuần sau tại phòng họp lớn (nhắc 15 phút).
```

### 5.3 Xem, sửa, xóa sự kiện

- **Xem danh sách**: bảng hiển thị tự động từ `GET /events` khi tải hoặc thêm sự kiện.
- **Xóa sự kiện**: nhấn nút **"Xóa"** trên hàng sự kiện.
- **Sửa sự kiện**: hiện tại không hỗ trợ UI sửa trực tiếp (có thể xóa + thêm lại).

### 5.4 Tìm kiếm

Ô "Tìm kiếm..." trên bảng cho phép lọc theo tên sự kiện (tính năng gợi ý cho phiên bản sau).

### 5.5 Xuất / Nhập file JSON

- **Xuất**: nhấn **"Xuất file JSON"** → tải file `events.json` chứa danh sách events hiện tại.
- **Nhập**: chọn file JSON bằng input file → hệ thống sẽ tải danh sách events từ file đó (ghi đè dữ liệu cũ).

## 6. Nhắc nhở (Reminder)

- Hệ thống **polling** mỗi 60 giây để kiểm tra reminder có nhắc không (`GET /due_reminders`).
- Nếu thời gian hiện tại ≥ (`start_time - reminder_minutes`), sẽ tạo **Browser Notification** (yêu cầu quyền hệ thống lần đầu).
- Bạn sẽ nhìn thấy thông báo pop-up ở góc màn hình (tuỳ theo hệ điều hành).

