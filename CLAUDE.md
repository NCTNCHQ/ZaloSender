# CLAUDE.md — Sổ ghi nhớ dự án ZaloSender

Ứng dụng desktop (Python + Tkinter + Playwright/Chrome) tự gửi tin nhắn Zalo kèm PDF cho khách hàng, nhóm và bạn bè.
Tác giả / chủ dự án: **Nguyễn Công Trung** — Congtrung127@gmail.com. Kho: https://github.com/NCTNCHQ/ZaloSender

## Quy tắc làm việc với chủ dự án (BẮT BUỘC)
1. **Luôn trả lời bằng tiếng Việt.**
2. **Tư vấn trước, chỉ thực hiện khi chủ dự án trả lời "Ok".** Với mỗi yêu cầu: phân tích, đề xuất cách làm, nêu rủi ro, hỏi những chỗ chưa rõ, rồi CHỜ "Ok".
3. **Mỗi lần bổ sung hoặc sửa phải tăng số phiên bản** và ghi vào `ung_dung/NHAT_KY_PHIEN_BAN.md`, ghi rõ thuộc [Cả 2 bản], [Standard] hay [PRO].
   - Sửa lỗi: tăng số cuối (1.10 → 1.10.1). Chức năng mới: tăng số giữa (1.10 → 1.11).
4. **Sau mỗi phiên bản được "Ok" và làm xong: TỰ PHÁT HÀNH lên GitHub** (xem quy trình bên dưới). Chủ dự án đã đồng ý việc này, không cần hỏi lại riêng.
5. Trước khi giao: **kiểm thử** (Zalo giả lập + giao diện chạy thật trên Xvfb), chụp ảnh màn hình khi đổi giao diện, và báo rõ phần nào chưa test được trên Zalo hoặc Windows thật.
6. Không bao giờ gửi tin nhầm người: mọi thay đổi phần gửi phải giữ các chốt an toàn (tên trùng khớp hoàn toàn, kiểm tra tiêu đề khung chat, đối chiếu nội dung ô soạn tin, bộ nhớ đệm chống gửi trùng, thiếu PDF hoặc dữ liệu thì bỏ qua).

## Cấu trúc kho
- `ung_dung/`: mã nguồn ứng dụng (đây là nội dung file zip phát hành).
  - `app.py`: giao diện (Bước 1/2, Ghép Zalo, thẻ Nhóm/Bạn bè, Nâng cấp PRO, Giới thiệu, Cập nhật).
  - `core.py`: dữ liệu, ghép tên, mã Dropbox, bộ nhớ đệm, kho mẫu tin.
  - `zalo_web.py`: điều khiển Zalo Web, nhận diện bằng chữ hiển thị; giao diện Zalo thật khác bản giả lập nên có lưu file chẩn đoán.
  - `license.py`: Key PRO ký Ed25519, gắn Mã máy. `datadir.py`: dữ liệu ở `%APPDATA%\ZaloSender`.
  - `updater.py` + `cap_nhat.py`: cập nhật qua GitHub (kiểm chữ ký + SHA-256, sao lưu, tự quay về bản cũ nếu lỗi).
  - `version.py`: `APP_VERSION`, `AUTHOR`, `AUTHOR_EMAIL`.
- `cong_cu_tac_gia/`: công cụ Tạo Key (`tao_key.py`), Phát hành (`phat_hanh.py`), Đóng gói (`dong_goi.py`).
- `phat_hanh/v<số>/`: các bản đã phát hành (`ZaloSender_v<số>.zip` + `phien_ban.json`).
- `.github/workflows/phat_hanh.yml`: đẩy tag `v<số>` thì GitHub Actions tự tạo Release.

## Bản Standard / PRO
- Cài xong là Standard. Nhập Key (gắn Mã máy, vĩnh viễn hoặc có hạn) thì mở PRO.
- Chỉ PRO có: nhiều mẫu tin, thẻ Bạn bè, ghép với bạn bè, lọc Chữ đầu, hiển thị Đã ghép/Chưa ghép/Đã tích, trường {Tên Zalo}.
- Chức năng mới: hỏi chủ dự án thuộc Standard hay PRO.

## ⚠ KHÓA BÍ MẬT `khoa_bi_mat.pem`
- Dùng để ký **Key PRO** và ký **bản cập nhật**. **TUYỆT ĐỐI KHÔNG commit lên GitHub** (đã có trong .gitignore).
- Khi cần phát hành, xin chủ dự án **tải file lên phiên làm việc**, đặt tạm ở `cong_cu_tac_gia/khoa_bi_mat.pem` (không commit). Trước khi commit, chạy `grep -rlE -- "-{5}BEGIN (ED25519 |)PRIVATE KEY-{5}" .` để chắc không có khóa trong kho.
- Khóa công khai tương ứng nằm trong `ung_dung/license.py` (`PUBLIC_KEY_B64`). Không được đổi, nếu đổi thì mọi Key và bản cài cũ hỏng.

## Quy trình phát hành (tự làm sau mỗi phiên bản)
1. Sửa `ung_dung/version.py` (APP_VERSION), cập nhật `NHAT_KY_PHIEN_BAN.md` và `HUONG_DAN.md` nếu cần.
2. Viết file ghi chú "Có gì mới" ngắn gọn (tiếng Việt, hiện cho người dùng).
3. `python cong_cu_tac_gia/dong_goi.py --notes-file <ghi_chu.txt> [--required]` tạo `phat_hanh/v<số>/ZaloSender_v<số>.zip` và `phien_ban.json` có ký số.
4. Commit (không có .pem) rồi `git push origin main`.
5. `git tag v<số> && git push origin v<số>`: GitHub Actions tự tạo Release kèm 2 file.
6. Kiểm tra: tải `https://github.com/NCTNCHQ/ZaloSender/releases/latest/download/phien_ban.json`, chạy `updater.verify_manifest`, tải zip và so SHA-256.
7. Nếu Actions hoặc quyền ghi bị chặn: gửi chủ dự án 2 file và hướng dẫn đăng tay (Releases → Draft a new release → tag v<số> → đính kèm 2 file → Publish).

## Kiểm thử (môi trường cloud)
- Tkinter: `apt-get install python3-tk`, sau đó dùng `/usr/bin/python3.12`; giao diện chạy bằng `xvfb-run`.
- Zalo giả lập: trang HTML mô phỏng bố cục Zalo Web (cột trái tìm kiếm, tiêu đề khung chat, Danh bạ, Danh sách nhóm/bạn bè, ô soạn tin bị mất chữ khi xuống dòng). Ghi đè `ZaloWebSender.start` để mở trang giả lập bằng Chromium `/opt/pw-browsers/chromium`.
- Đặt biến `ZALOSENDER_DATA` để dữ liệu thử không lẫn vào máy thật.

## Lưu ý từ thực tế
- Ứng dụng phải đặt trong **thư mục không dấu** (WScript tạo shortcut lỗi với đường dẫn có dấu); chủ dự án chọn không sửa, chỉ cần nhắc.
- Tên nhóm Zalo theo dạng "mã Dropbox + tên công ty"; Excel có thể khác tên công ty, nên ghép theo mã. Trường hợp không chắc chắn thì người dùng xác nhận và ứng dụng nhớ trong `ghep_nhom.json`.
- Màn hình thường là laptop 1366×768: luôn kiểm tra giao diện ở kích thước này.
