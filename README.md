# README

# Aronaldo Discord Bot

> Developed by caophihung

Bot Discord này hỗ trợ:

* Slash command `/thongbao` để gửi thông báo có embed
* Slash command `/edit` để chỉnh sửa thông báo đã gửi
* Prefix command `>batchuoc` để gửi lại nội dung và file đính kèm sang kênh khác

## 1) Cài đặt Python

Cài Python 3.10+ (khuyến nghị 3.11 hoặc mới hơn).

Kiểm tra đã cài thành công:

```bash
python --version
```

hoặc

```bash
py --version
```

## 2) Cài thư viện

Mở terminal tại thư mục chứa `main.py` và `requirements.txt`, rồi chạy:

```bash
pip install -r requirements.txt
```

## 3) Thiết lập biến môi trường TOKEN

Bot cần token Discord được lưu trong biến môi trường `TOKEN`.

### Windows (PowerShell)

```powershell
$env:TOKEN="your_bot_token"
```

### Windows (CMD)

```cmd
set TOKEN=your_bot_token
```

### Linux / macOS

```bash
export TOKEN="your_bot_token"
```

## 4) Chạy bot

```bash
python main.py
```

hoặc

```bash
py main.py
```

## 5) Slash command `/thongbao`

Dùng để tạo và gửi thông báo vào kênh thông báo.

### Cú pháp

```text
/thongbao
```

### Ghi chú

* Nếu không chọn `channel`, bot sẽ tự gửi vào kênh ếch nhà làm.
* `cover` là ảnh bìa đính kèm.
* `archive_file` là file archive đính kèm.
* `links` nhận nhiều link, ngăn cách bằng dấu cách.
* `mention` sẽ tự thêm mention @Sếch thủ.

## 6) Slash command `/edit`

Dùng để chỉnh sửa một thông báo đã gửi trước đó.

### Cú pháp

```text
/edit
```

### Cách hoạt động

* `message_link` là link đến thông báo cần chỉnh sửa.
* Nếu không chọn tham số, bot sẽ giữ nguyên giá trị cũ và không chỉnh sửa trường đó.
* Nếu nhập `.` cho một tham số, bot sẽ xóa nội dung của trường đó.

### Ví dụ

* Chỉ sửa tiêu đề:

  ```text
  /edit message_link:<link> title:Tiêu đề mới
  ```

* Xóa caption:

  ```text
  /edit message_link:<link> caption:.
  ```

## 7) Prefix command `>batchuoc`

Dùng để gửi lại nội dung và toàn bộ file đính kèm sang một kênh khác.

### Cú pháp

```text
>batchuoc #channel content
```

### Cách hoạt động

* Bot sẽ gửi lại `content` vào kênh được chỉ định.
* Bot cũng gửi các file đính kèm đi kèm theo tin nhắn gốc.
* Nếu trong các file đính kèm có file tên `message.txt`, bot sẽ đọc nội dung của file đó và dùng nội dung này làm `content`.

### Ví dụ

```text
>batchuoc #spam idk
```

## 8) Lưu ý

* Bot cần được cấp quyền gửi tin nhắn, gửi file và đọc lịch sử tin nhắn ở các kênh sử dụng.
* Slash command có thể cần đồng bộ lại sau khi cập nhật code(F5 ở web hoặc restart ở app).

## License

This project is licensed under the MIT License.