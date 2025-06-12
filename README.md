🍕 Pizza Box Tracker – Smart Detection & State Management System
📌 Mục tiêu
Xây dựng hệ thống tự động đếm số lượng pizza được bán ra trong một khoảng thời gian dựa trên:

Trạng thái mở/đóng của hộp pizza.

Vị trí của hộp pizza trong khu vực giao hàng (ROI).

Cơ chế gán ID và quản lý trạng thái của từng hộp.

🎯 Luồng xử lý tổng quan
YOLOv8 nhận diện hộp pizza và trạng thái (open hoặc close).

Tracking (DeepSORT/ByteTrack) gán ID duy nhất cho mỗi hộp.

Xác định xem hộp có nằm trong vùng ROI không.

Ghi nhận trạng thái theo thời gian của từng hộp theo ID.

Áp dụng quy tắc chuyển trạng thái để xác định hộp đã "bán".

🧠 Quy tắc xác định hộp đã bán (sold)
ID hộp	Chuỗi trạng thái quan sát được	Trạng thái cuối cùng
01	["open", "close"]	✅ Sold
02	["close", "open", "close"]	✅ Sold
03	["open"] hoặc ["close"]	⏳ Pending

🗂️ Quản lý dữ liệu hộp
Mỗi hộp pizza sẽ được lưu thành một object:

python
Copy
Edit
{
  "id": 12,
  "status": "pending",      # hoặc "sold"
  "open_state": ["open", "close"],  # lịch sử trạng thái
  "last_seen_frame": 240,   # optional
  "position": (x, y),       # optional, để kiểm tra có nằm trong ROI không
}
🔁 Luồng cập nhật
Khi hộp mới xuất hiện → thêm vào array_pending.

Khi chuỗi trạng thái thỏa quy tắc sold → chuyển từ pending → sold.

🧾 Output (trực tiếp hoặc sau video)
array_pending: danh sách ID hộp đang chờ giao.

array_sold: danh sách ID hộp đã được bán ra.

🔧 Công nghệ đề xuất
Thành phần	Công cụ	Vai trò
Object Detection	YOLOv8	Phát hiện hộp pizza và trạng thái
Object Tracking	DeepSORT / ByteTrack	Gán ID cho mỗi hộp
Vùng ROI	Polygon mask (OpenCV)	Xác định khu vực giao hàng
Logic	Python	Quản lý ID và chuyển trạng thái

📌 Mở rộng tiềm năng
Kết hợp Reinforcement Learning để tối ưu chiến lược nhận diện và gợi ý điều chỉnh vùng ROI.

Giao diện người dùng để feedback trạng thái, kích hoạt active learning.

Gửi cảnh báo nếu phát hiện bất thường (ví dụ mở hộp rồi để lại không đóng).

📂 Thư mục dự kiến
pgsql
Copy
Edit
pizza-tracker/
├── detector/           # YOLO detection wrapper
├── tracker/            # DeepSORT / ByteTrack
├── utils/              # ROI, state management
├── main.py             # Pipeline chính
├── config.py           # Tham số ROI, camera
└── README.md
