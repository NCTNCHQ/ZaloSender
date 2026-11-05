# Công cụ của tác giả – Gửi tin Zalo

> ⚠ **CHỈ BẠN (tác giả) GIỮ. KHÔNG gửi thư mục này cho khách hàng.**

## Các file trong thư mục
- `khoa_bi_mat.pem`: **KHÓA BÍ MẬT**, dùng chung cho Key PRO và cho bản cập nhật.
  - Ai có file này đều tạo được Key và phát hành được bản cập nhật. **Không chia sẻ.**
  - **Sao lưu** ra USB hoặc ổ khác. Mất file này thì không tạo được Key mới và không phát hành được bản cập nhật mà các máy chấp nhận.
- `CHAY_TAO_KEY.bat`: **cấp Key PRO** (xem mục bên dưới).
- `CHAY_PHAT_HANH.bat`: **phát hành bản cập nhật** (xem mục bên dưới).
- `so_key_da_cap.csv`: sổ các Key đã cấp.

## Cấp Key PRO
1. Khách bấm **⭐ Nâng cấp PRO → ✉ Gửi email xin Key** (hoặc Sao chép mã máy) và gửi bạn Mã máy dạng `ZS-XXXX-XXXX-XXXX`.
2. Mở `CHAY_TAO_KEY.bat`, dán Mã máy, chọn **Thời hạn**, bấm **Tạo Key**, rồi **Sao chép Key** gửi cho khách.

## Phát hành bản cập nhật lên GitHub (NCTNCHQ/ZaloSender)
1. Có file zip bản mới, tên dạng `ZaloSender_v1.11.zip`.
2. Mở `CHAY_PHAT_HANH.bat`, chọn file zip, ghi **"Có gì mới"**. Tích **BẮT BUỘC** nếu bản cũ có lỗi nghiêm trọng. Bấm **Tạo phien_ban.json**.
3. Vào https://github.com/NCTNCHQ/ZaloSender/releases → **Draft a new release**:
   - **Choose a tag**: gõ `v1.11`, chọn **Create new tag**.
   - **Release title**: `v1.11`. Ô mô tả: dán phần "Có gì mới".
   - Kéo thả **2 file** vào ô đính kèm: `ZaloSender_v1.11.zip` và `phien_ban.json`.
   - Bấm **Publish release**.
4. Xong. Các máy đang dùng sẽ thấy thông báo bản mới khi mở ứng dụng.

> Tên file trên GitHub phải **giữ nguyên** là `phien_ban.json` và `ZaloSender_v<số>.zip`, và tag phải là `v<số>`, vì link tải được ký sẵn trong phien_ban.json.
