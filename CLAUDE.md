# CLAUDE.md — Sổ ghi nhớ dự án ZaloSender

Ứng dụng desktop (Python + Tkinter + Playwright/Chrome) tự gửi tin nhắn Zalo kèm PDF cho khách hàng, nhóm và bạn bè.
Tác giả / chủ dự án: **Nguyễn Công Trung** — Congtrung127@gmail.com. Kho: https://github.com/NCTNCHQ/ZaloSender

## Quy tắc làm việc với chủ dự án (BẮT BUỘC)
1. **Luôn trả lời bằng tiếng Việt.**
2. **Tư vấn trước, chỉ thực hiện khi chủ dự án trả lời "Ok".** Với mỗi yêu cầu: phân tích, đề xuất cách làm, nêu rủi ro, hỏi những chỗ chưa rõ, rồi CHỜ "Ok".
3. **Mỗi lần bổ sung hoặc sửa phải tăng số phiên bản** và ghi vào `ung_dung/he_thong/NHAT_KY_PHIEN_BAN.md`, ghi rõ thuộc [Cả 2 bản], [Standard] hay [PRO].
   - Sửa lỗi: tăng số cuối (1.10 → 1.10.1). Chức năng mới: tăng số giữa (1.10 → 1.11).
4. **Sau mỗi phiên bản được "Ok" và làm xong: TỰ PHÁT HÀNH lên GitHub** (xem quy trình bên dưới). Chủ dự án đã đồng ý việc này, không cần hỏi lại riêng.
5. Trước khi giao: **kiểm thử** (Zalo giả lập + giao diện chạy thật trên Xvfb), chụp ảnh màn hình khi đổi giao diện, và báo rõ phần nào chưa test được trên Zalo hoặc Windows thật.
6. Không bao giờ gửi tin nhầm người: mọi thay đổi phần gửi phải giữ các chốt an toàn (tên trùng khớp hoàn toàn, kiểm tra tiêu đề khung chat, đối chiếu nội dung ô soạn tin, bộ nhớ đệm chống gửi trùng, thiếu PDF hoặc dữ liệu thì bỏ qua).

## Cấu trúc kho
- `ung_dung/`: nội dung file zip phát hành (v1.11 trở đi).
  - Thư mục gốc chỉ có: `1-CAI DAT (bam dup vao day).bat`, `2-MO UNG DUNG.bat`, `HUONG DAN SU DUNG.html` (tự chứa, ảnh base64; **chỉ dùng ảnh dữ liệu giả, không đưa tên/số tiền khách thật vào kho**). Các file .bat phải là ASCII + CRLF.
  - `he_thong/`: mã nguồn ứng dụng.
    - `app.py`: giao diện (Bước 1/2, Ghép Zalo, thẻ Nhóm/Bạn bè, Nâng cấp PRO, Giới thiệu, Cập nhật).
    - `core.py`: đọc file (`load_table`: file công nợ kế toán, tiêu đề 2 dòng), ghép theo Số Dropbox (`parse_code`, `match_group`), nhóm nội bộ "Xử lý" (`is_internal_group`), bộ nhớ đệm, kho mẫu tin.
    - `zalo_web.py`: điều khiển Zalo Web, nhận diện bằng chữ hiển thị; giao diện Zalo thật khác bản giả lập nên có lưu file chẩn đoán.
    - `license.py`: Key PRO ký Ed25519, gắn Mã máy. `datadir.py`: dữ liệu ở `%APPDATA%\ZaloSender`.
    - `updater.py` + `cap_nhat.py`: cập nhật qua GitHub (kiểm chữ ký + SHA-256, sao lưu, tự quay về bản cũ nếu lỗi). Lưu ý: khi cập nhật, `cap_nhat.py` của **bản đang cài** chạy; máy cũ (cấu trúc phẳng) chỉ nhận nội dung `he_thong/`.
    - `version.py`: `APP_VERSION`, `AUTHOR`, `AUTHOR_EMAIL`. `mau/`: dữ liệu mẫu.
- `cong_cu_tac_gia/`: công cụ Tạo Key (`tao_key.py`), Phát hành (`phat_hanh.py`), Đóng gói (`dong_goi.py`).
- `phat_hanh/v<số>/`: các bản đã phát hành (`ZaloSender_v<số>.zip` + `phien_ban.json`).
- `.github/workflows/phat_hanh.yml`: nhánh main có `phat_hanh/v<số>/` mới thì GitHub Actions tự tạo Release.

## Bản Standard / PRO
- Cài xong là Standard. Nhập Key (gắn Mã máy, vĩnh viễn hoặc có hạn) thì mở PRO.
- Chỉ PRO có: nhiều mẫu tin, thẻ Bạn bè, ghép với bạn bè, lọc Chữ đầu, hiển thị Đã ghép/Chưa ghép/Đã tích, trường {Tên Zalo}.
- Chức năng mới: hỏi chủ dự án thuộc Standard hay PRO.

## ⚠ KHÓA BÍ MẬT `khoa_bi_mat.pem`
- Dùng để ký **Key PRO** và ký **bản cập nhật**. **TUYỆT ĐỐI KHÔNG commit lên GitHub** (đã có trong .gitignore).
- Khi cần phát hành, xin chủ dự án **tải file lên phiên làm việc**, đặt tạm ở `cong_cu_tac_gia/khoa_bi_mat.pem` (không commit). Trước khi commit, chạy `grep -rlE -- "-{5}BEGIN (ED25519 |)PRIVATE KEY-{5}" .` để chắc không có khóa trong kho.
- Khóa công khai tương ứng nằm trong `ung_dung/license.py` (`PUBLIC_KEY_B64`). Không được đổi, nếu đổi thì mọi Key và bản cài cũ hỏng.

## Quy trình phát hành (tự làm sau mỗi phiên bản)
1. Sửa `ung_dung/he_thong/version.py` (APP_VERSION), cập nhật `ung_dung/he_thong/NHAT_KY_PHIEN_BAN.md`, `HUONG_DAN.md` và `ung_dung/HUONG DAN SU DUNG.html` nếu cần.
2. Viết file ghi chú "Có gì mới" ngắn gọn (tiếng Việt, hiện cho người dùng).
3. `python cong_cu_tac_gia/dong_goi.py --notes-file <ghi_chu.txt> [--key <đường dẫn .pem>] [--required]` tạo `phat_hanh/v<số>/ZaloSender_v<số>.zip` và `phien_ban.json` có ký số.
4. Commit (không có .pem) rồi `git push origin main`. **Không cần tag**: GitHub Actions (`phat_hanh.yml`) thấy thư mục `phat_hanh/v<số>/` mới thì tự tạo tag và Release kèm 2 file. Môi trường cloud chặn việc đẩy tag, nên không dùng tag.
5. Theo dõi: `gh run list -R NCTNCHQ/ZaloSender --limit 3`, sau đó `gh release view v<số> -R NCTNCHQ/ZaloSender`.
6. Kiểm tra: tải `https://github.com/NCTNCHQ/ZaloSender/releases/latest/download/phien_ban.json`, chạy `updater.verify_manifest`, tải zip và so SHA-256.
7. Nếu Actions hoặc quyền ghi bị chặn: gửi chủ dự án 2 file và hướng dẫn đăng tay (Releases → Draft a new release → tag v<số> → đính kèm 2 file → Publish).

## Kiểm thử (môi trường cloud)
- Tkinter: `apt-get install python3-tk`, sau đó dùng `/usr/bin/python3.12`; giao diện chạy bằng `xvfb-run`.
- Zalo giả lập: trang HTML mô phỏng bố cục Zalo Web (cột trái tìm kiếm, tiêu đề khung chat, Danh bạ, Danh sách nhóm/bạn bè, ô soạn tin bị mất chữ khi xuống dòng). Ghi đè `ZaloWebSender.start` để mở trang giả lập bằng Chromium `/opt/pw-browsers/chromium`.
- Đặt biến `ZALOSENDER_DATA` để dữ liệu thử không lẫn vào máy thật.
- Thử cập nhật: dùng máy chủ HTTPS cục bộ + Xvfb cố định (`Xvfb :77`, `DISPLAY=:77`); nếu dùng `xvfb-run` thì màn hình tắt khi app cũ đóng và bản mới bị coi là lỗi.
- Dữ liệu thật của chủ dự án (file công nợ, danh sách nhóm) chỉ để trong scratchpad, **không commit**.

## Trạng thái hiện tại và việc còn treo (cập nhật mỗi lần phát hành)
- **Bản mới nhất: v1.11** (06/11/2026), đã phát hành và kiểm tra chữ ký + SHA-256. Nội dung chính: gửi công nợ theo file kế toán, ghép theo Số Dropbox, chặn nhóm "Xử lý", mẫu "AONE – Công nợ", DS cần xử lý, mẫu riêng từng khách (PRO), thư mục cài mới (`he_thong/`).
- **Khóa bí mật và dữ liệu thật KHÔNG còn trong phiên mới**: khi phát hành cần xin chủ dự án tải lại `khoa_bi_mat.pem`. Muốn thử với dữ liệu thật thì xin lại file công nợ và danh sách nhóm Zalo.
- **Chưa thử trên Zalo thật / Windows thật**: các bản v1.7 → v1.11 (gửi vào nhóm thật, cửa sổ cài có màu, biểu tượng Desktop với cấu trúc mới).
- **Chủ dự án chưa báo kết quả** lần cập nhật tự động thật đầu tiên (v1.10.1 → v1.11 bằng nút "Cập nhật ngay").
- **Dữ liệu cần kế toán bổ sung** (theo file công nợ 05/11/2026): 25 khách thiếu Số Dropbox (#N/A), 6 khách không có nhóm mang số đó, khách 155 (Bảo Tín) có thể ghi sai mã.
- **Quyết định đã chốt**: không sửa lỗi thư mục có dấu (chỉ nhắc); không bắt xác nhận lại toàn bộ ghép nhóm lần đầu; gợi ý "tên công ty khác nhiều" chỉ để nhắc, không chặn gửi; máy cập nhật từ bản cũ giữ cách mở cũ (không ép cài lại).

## Lưu ý từ thực tế
- Ứng dụng phải đặt trong **thư mục không dấu** (WScript tạo shortcut lỗi với đường dẫn có dấu); chủ dự án chọn không sửa, chỉ cần nhắc.
- Tên nhóm Zalo theo dạng "mã Dropbox + tên công ty"; Excel có thể khác tên công ty, nên ghép theo mã. Trường hợp không chắc chắn thì người dùng xác nhận và ứng dụng nhớ trong `ghep_nhom.json`.
- Màn hình thường là laptop 1366×768: luôn kiểm tra giao diện ở kích thước này.
