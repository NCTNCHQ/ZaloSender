# Hướng dẫn: Gửi tin nhắn Zalo tự động – v1.10.1

Tác giả: **Nguyễn Công Trung** — Congtrung127@gmail.com

## 🔄 Cập nhật phiên bản mới
- Có bản mới, phía trên cửa sổ hiện thanh **"🔔 Có phiên bản mới"**. Bấm **⬇ Cập nhật ngay**: ứng dụng tự tải, tự cài rồi tự mở lại.
- Kiểm tra bằng tay: **ℹ Giới thiệu & Hỗ trợ → 🔄 Kiểm tra cập nhật**.
- Dữ liệu và Key PRO được giữ nguyên. Nếu bản mới lỗi, ứng dụng tự quay về bản cũ.
- Các bản phát hành: https://github.com/NCTNCHQ/ZaloSender/releases

## 🔑 Bản Standard và bản PRO
- Cài đặt xong, ứng dụng chạy ở bản **Standard**. Tiêu đề cửa sổ ghi "Standard v1.9".
- **Nâng cấp PRO:**
  1. Bấm nút vàng **"⭐ Nâng cấp PRO"** ở góc trên.
  2. Bấm **"📋 Sao chép mã máy"** và gửi **Mã máy** (dạng `ZS-XXXX-XXXX-XXXX`) cho nhà cung cấp.
  3. Nhận **Key**, dán vào ô, bấm **"🔑 Kích hoạt"**. Ứng dụng tự khởi động lại thành **PRO**.
- Key chỉ dùng được trên **đúng máy** đã gửi Mã máy. Đổi máy hoặc cài lại Windows thì cần Key mới.
- Xem bản đang dùng và hạn dùng: nút **"ℹ Giới thiệu"**.
- Chức năng **chỉ có ở PRO** (bản Standard hiện 🔒):
  - Nhiều mẫu tin nhắn
  - Thẻ Bạn bè Zalo
  - Ghép khách với bạn bè
  - Lọc theo Chữ đầu
  - Hiển thị Chỉ đã ghép / Chưa ghép / Đã tích
  - Trường {Tên Zalo}

## 💾 Dữ liệu được lưu ở đâu
- Mọi dữ liệu nằm ở **`%APPDATA%\ZaloSender`**. Bấm **ℹ Giới thiệu → 📂 Mở thư mục dữ liệu** để mở.
  - Dữ liệu gồm: Key PRO, mẫu tin, ghép nhóm, bộ nhớ đệm "đã gửi", báo cáo `ket_qua\`, file chẩn đoán, đăng nhập Zalo.
- **Cài lại hoặc cập nhật** ứng dụng **không mất** dữ liệu. Xóa thư mục ứng dụng cũng **không xóa** dữ liệu.
- **Muốn xóa hẳn**: mở thư mục dữ liệu rồi xóa thư mục `ZaloSender`.
- **Chuyển sang máy khác**: chép thư mục `ZaloSender` sang `%APPDATA%` của máy mới. Riêng Key PRO thì cần **Key mới**, vì Mã máy thay đổi.

## 🖱 Sắp xếp và lọc ở thẻ Nhóm / Bạn bè
Bấm **chuột phải** vào bảng, hoặc bấm nút **"☰ Sắp xếp / Lọc"**. Khi đang lọc, phía trên bảng hiện dòng **"Đang xem: …"**; bấm **"✖ Bỏ lọc"** để xem lại tất cả.


## ⭐ Quy trình gửi đề nghị thanh toán hằng tháng

**Chuẩn bị:**
- **File Excel** có 2 cột: `Tên khách hàng` (trùng **đúng** tên nhóm Zalo) và `Số tiền` (gõ số thường, ví dụ `5000000`).
- **Một thư mục PDF**, mỗi khách một file đặt **tên giống tên khách hàng**, ví dụ `Nhóm F4.pdf`.
  - Một khách nhiều file: `Nhóm F4_HD01.pdf`, `Nhóm F4 - Phụ lục.pdf`.
  - Tên có ký tự `/ \ : * ? " < > |` thì thay bằng `_`. Ví dụ "Cửa hàng A/B" thành `Cửa hàng A_B.pdf`.

**Lần đầu (thiết lập một lần):**
1. Thẻ **Nhóm Zalo**: bấm **"Lấy danh sách nhóm từ Zalo"**. Không cần tích gì ở thẻ này.
2. Thẻ **Khách hàng**:
   - Bấm **"📂 Chọn file Excel"**.
   - Bấm **"📁 Chọn thư mục PDF"**.
3. Bảng hiện ngay **Số tiền, File PDF, Nhóm Zalo, Trạng thái** của từng khách. Bấm vào tên khách để xem trước tin nhắn; chữ **đỏ** là phần thay đổi theo khách.

**Khi tên trong Excel KHÁC tên nhóm Zalo** (ví dụ Excel "99rs. công ty TNN 1 thành viên", Zalo "99rs. công ty Anh TRUNG"):
- Ứng dụng tự ghép theo **mã Dropbox** ở đầu tên (99rs), hoặc theo **tên công ty**.
- Trường hợp không chắc chắn (nhiều nhóm cùng mã, tên chỉ gần giống), Bước 1 hiện **"⚠ N khách cần xác nhận"**:
  - Bấm **"🔗 Ghép Zalo"**, chọn đúng nhóm hoặc bạn bè (có nhãn [Nhóm] / [Bạn bè]), rồi bấm **Xác nhận**.
  - Ứng dụng **ghi nhớ**, lần sau không hỏi lại.
- File PDF có thể đặt theo **mã Dropbox**, ví dụ `99rs.pdf`.

**Thẻ Nhóm Zalo:**
- **Bấm chuột phải** vào bảng (hoặc nút **☰ Sắp xếp / Lọc**) để chọn Sắp xếp (Số đầu tên / Thành viên / A → Z) và Hiển thị.
- **"📤 Xuất ra Excel"** để lưu danh sách nhóm đang hiển thị.

**Mẫu tin nhắn (Bước 2):**
- Chọn mẫu ở ô **"Mẫu tin nhắn"**. Có thể **Tạo mới**, **Lưu**, **Đổi tên**, **Xóa**, **Đặt mặc định ⭐**.
- **"↺ Khôi phục mẫu '…'"**: bỏ phần sửa chưa lưu, trả về nội dung đã lưu của mẫu đang chọn.
- Mẫu thông báo chung (không có số tiền) nên dùng trường **{Tên Zalo}**, ví dụ: `Kính gửi {Tên Zalo}, công ty nghỉ lễ 2/9.`

**Thẻ Bạn bè Zalo:**
- Bấm **"Lấy danh sách bạn bè từ Zalo"** (lần đầu có thể mất vài phút nếu nhiều bạn).
- Tích bạn bè để gửi **thông báo chung**. Sắp xếp, Hiển thị, **Chữ đầu**: bấm chuột phải vào bảng. Có Xuất Excel.
- Khách trong Excel là bạn bè (chat riêng) thì ghép ở **"🔗 Ghép Zalo"**.
- Người **trùng tên** trên Zalo sẽ không được gửi. Hãy đặt **tên gợi nhớ** khác nhau cho họ trên Zalo, rồi lấy lại danh sách.

**Mỗi tháng:**
1. Cập nhật số tiền trong file Excel và đặt các file PDF mới vào thư mục PDF.
2. Mở ứng dụng. File Excel lần trước **tự mở lại**, tất cả khách **tự được tích chọn**.
   - Xem cột **Trạng thái**.
   - Bấm vào vài khách để kiểm tra tin nhắn.
   - Bấm **Tiếp tục**.
3. Kiểm tra ô **Tháng**: ứng dụng tự điền tháng trước, ví dụ `10/2026`.
4. Bấm **"🔎 Kiểm tra & gửi"** để mở **bảng kiểm tra**:
   - Dòng **đỏ** sẽ bị bỏ qua, kèm lý do: thiếu PDF, thiếu số tiền, không thấy nhóm…
   - Dòng **xanh** sẵn sàng gửi.
   - Ứng dụng cũng cảnh báo các file PDF **không khớp với ai**.
5. Bấm **"🚀 Bắt đầu gửi"**. Mỗi khách nhận **tin nhắn trước, PDF sau**.
   - Ứng dụng **dán** tin nhắn vào Zalo và **đối chiếu từng dòng** trước khi gửi. Thiếu dòng thì không gửi.
   - Cột **"Gửi"** ở Bước 1 ghi **✅ Đã gửi + giờ gửi**. Bấm gửi lại thì những khách đã gửi **tự bỏ qua**, không gửi trùng.
   - Muốn gửi lại cho một khách: bấm vào tên khách, rồi bấm **"↺ Đặt lại: Chưa gửi"**.
   - Trong lúc gửi, nội dung bạn đã sao chép (Ctrl+C) trước đó sẽ bị thay.
6. Xem kết quả: ℹ Giới thiệu → 📂 Mở thư mục dữ liệu → `ket_qua\`.

> Nếu tham gia thêm nhóm mới, hãy bấm lại **"Lấy danh sách nhóm từ Zalo"** trước khi gửi.


## 1. Cài đặt (làm 1 lần)
1. Giải nén `ZaloSender_v1.3.zip` vào một thư mục cố định, ví dụ `D:\ZaloSender`.
   **Đừng để trong thư mục Downloads rồi xóa**: biểu tượng trên Desktop trỏ vào thư mục này.
2. Bấm đúp **`CAI_DAT.bat`**:
   - **Chưa có Python**: trang https://www.python.org/downloads/ sẽ tự mở. Tải và cài Python, **nhớ tích ô "Add Python to PATH"** ở cửa sổ cài đặt đầu tiên. Cài xong, bấm đúp lại `CAI_DAT.bat`.
   - **Chưa có Google Chrome**: trang https://www.google.com/chrome/ sẽ tự mở. Cài Chrome xong, quay lại cửa sổ cài đặt và nhấn Enter.
   - Trình cài đặt tự cài thư viện và tạo biểu tượng **"Gửi tin Zalo"** trên Desktop.
3. Từ đó về sau, chỉ cần bấm biểu tượng **"Gửi tin Zalo"** trên Desktop. Nếu biểu tượng không mở được, dùng file `chay_ung_dung.bat`: file này hiện cửa sổ đen kèm thông báo lỗi để dễ kiểm tra.

## 2. Bước 1 – Chọn người nhận
Có 2 thẻ. Bạn chọn người nhận ở một thẻ hoặc cả hai.

### Thẻ "👤 Khách hàng (file Excel/CSV)"
- Bấm **"Mở file khách hàng"**. Dòng đầu tiên của file phải là tên cột.
- Ứng dụng tự đoán các cột. Nếu đoán sai, chọn lại:

| Ô chọn | Ý nghĩa |
|---|---|
| Cột SĐT | Số điện thoại. Viết kiểu nào cũng được: `0912…`, `+84 912…`, `912…` |
| Cột tên khách | Tên hiển thị trong nhật ký và báo cáo |
| Cột tên Zalo / tên nhóm | Dùng cho dòng **không có SĐT**: ứng dụng tìm theo tên này, và tên phải **trùng khớp hoàn toàn** |
| Cột file PDF riêng | Tên file PDF riêng của khách, ví dụ `HD001.pdf`. Nhiều file thì cách nhau bằng `;` |

- Bấm vào từng dòng để tích ☑. Có ô **Lọc** và nút **Chọn tất cả**.

### Thẻ "👥 Nhóm Zalo"
- Bấm **"Lấy danh sách nhóm từ Zalo"**. Chrome sẽ mở Zalo Web (lần đầu cần quét QR), ứng dụng tự đọc các nhóm bạn đang tham gia rồi đóng Chrome.
- Danh sách được lưu lại. Lần sau chỉ cần bấm lấy lại khi bạn tham gia thêm nhóm mới.
- Tích chọn các nhóm cần gửi.

Bấm **"Tiếp tục ➜ Bước 2"**.

## 3. Bước 2 – Soạn tin và gửi
1. **Nội dung tin nhắn**:
   - Dùng ô **"Chèn trường"** để chèn `{Họ tên}`, `{Sản phẩm}`…
   - Tin gửi nhóm chỉ dùng được trường `{Tên nhóm}`.
   - Ô **Xem trước** cho phép chọn bất kỳ người nhận nào để xem tin nhắn thật của người đó.
2. **File PDF** (luôn gửi **sau** tin nhắn):
   - **File PDF chung**: bấm "Thêm file", gửi cho tất cả người nhận, kể cả nhóm.
   - **File PDF riêng**: chọn **thư mục** chứa các file. Chỉ dùng cho khách hàng, không gửi vào nhóm.
3. **Thời gian nghỉ** giữa 2 lượt gửi: mặc định từ 20 đến 45 giây, ngẫu nhiên.
4. **Lần đầu, hãy tích "Chạy thử"**: ứng dụng mở từng cuộc trò chuyện và kiểm tra file, nhưng **không gửi**.
5. Bấm **"Bắt đầu gửi"**. Bảng xác nhận sẽ cho biết bao nhiêu người sẽ được gửi, bao nhiêu bị bỏ qua và vì sao.
6. Kết quả được lưu ở thư mục `ket_qua\`, dạng file CSV, mở được bằng Excel.

## 4. Thử nghiệm với dữ liệu mẫu
- `mau_thanh_toan.xlsx`: 3 khách mẫu.
- `pdf_mau\`: PDF của khách mẫu A và B. Khách C **cố ý không có PDF** để bạn thấy ứng dụng bỏ qua.
- Muốn thử gửi thật: đổi tên khách trong file mẫu thành **tên một nhóm thử** của bạn, và đổi tên file PDF cho khớp.

**Thứ tự thử nghiệm nên làm:**
1. Chạy thử (không gửi).
2. Gửi thật đến số của chính bạn.
3. Gửi đến một nhóm thử chỉ có bạn và 1–2 người quen.
4. Gửi thật cho vài khách đầu tiên (bỏ tích các khách còn lại ở Bước 1), rồi mới gửi cả danh sách.

## 5. Kết quả trong báo cáo
| Kết quả | Ý nghĩa |
|---|---|
| ĐÃ GỬI | Gửi xong tin nhắn và toàn bộ PDF |
| CHẠY THỬ OK | Chế độ chạy thử: mở được cuộc trò chuyện, đủ file |
| GỬI THIẾU PDF | Đã gửi tin nhắn nhưng gửi PDF bị lỗi (xem cột Ghi chú) |
| THẤT BẠI | Không gửi được gì (xem cột Ghi chú) |

## 6. Lưu ý quan trọng
- **Không dùng chuột hay bàn phím trong cửa sổ Chrome** khi ứng dụng đang chạy.
- **Nguy cơ bị khóa tài khoản:** Zalo hạn chế việc gửi hàng loạt, nhất là gửi cho người **chưa kết bạn** và gửi file. Nên gửi từng đợt nhỏ và để thời gian nghỉ dài.
- **Tin gửi vào nhóm thì mọi thành viên đều thấy.** Hãy chắc chắn nhóm riêng của khách chỉ có khách và người của công ty.
- Nhóm chỉ cho trưởng nhóm nhắn tin sẽ báo lỗi "Không mở được ô soạn tin".
- Có 2 nhóm trùng tên thì ứng dụng **bỏ qua cả hai** để tránh gửi nhầm.
- Chỉ gửi cho khách **đã đồng ý nhận tin**, theo quy định về tin nhắn quảng cáo và bảo vệ dữ liệu cá nhân.

## 7. Khi gặp lỗi – thư mục `chan_doan\`
Khi **lấy danh sách nhóm** hoặc **tìm / mở nhóm để gửi** bị lỗi, ứng dụng tự lưu file vào thư mục `chan_doan\`. Mỗi lần lỗi lưu 2 file:
- **Ảnh chụp màn hình** (`.png`)
- **Cấu trúc trang** (`.html`): đã bỏ bớt ảnh và mã chạy, chỉ còn chữ hiển thị như tên nhóm

Hãy gửi 2 file này cho người hỗ trợ để sửa chính xác. Các file **không chứa** mật khẩu hay nội dung tin nhắn riêng, nhưng có thể có tên nhóm và tên bạn bè đang hiện trên màn hình. Bạn nên mở xem trước khi gửi.

## 8. Cập nhật lên phiên bản mới
1. Giải nén bản mới (đè lên thư mục cũ hoặc thư mục mới đều được). Từ v1.9.1 dữ liệu nằm ở `%APPDATA%\ZaloSender` nên luôn được giữ. Với bản cũ hơn, những thứ sau vẫn được giữ: thông tin đăng nhập Zalo (`zalo_profile\`), danh sách nhóm, cài đặt (`cai_dat_ung_dung.json`: file Excel, thư mục PDF, mẫu tin nhắn), **bộ nhớ đệm** (`bo_nho_dem\`: trạng thái đã gửi của từng tháng), **ghép nhóm đã xác nhận** (`ghep_nhom.json`), **mẫu tin nhắn** (`mau_tin_nhan.json`), danh sách bạn bè (`ban_be_zalo.json`), **Key PRO đã kích hoạt** (`ban_quyen.json`) và báo cáo cũ.
2. Chạy lại `CAI_DAT.bat` để cập nhật biểu tượng.

## 9. Khi Zalo đổi giao diện (dành cho người kỹ thuật)
Nếu ứng dụng báo không tìm thấy nút hoặc ô nào đó, hãy thêm bộ chọn CSS mới vào `config.json`, mục `"selectors"`. Ví dụ:
```json
{ "selectors": { "search_input": "#contact-search-input", "message_input": "#richInput" } }
```
Các khóa có thể sửa:
- `search_input`: ô tìm kiếm
- `search_result`: kết quả tìm kiếm (danh sách)
- `message_input`: ô soạn tin
- `chat_title`: tiêu đề cuộc trò chuyện (danh sách)
- `attach_button`: nút đính kèm (danh sách)
- `attach_menu_text`: chữ của mục chọn file trong menu đính kèm
- `file_needs_enter`: đặt `true` nếu sau khi chọn file phải nhấn Enter mới gửi
- `contacts_tab`: nút Danh bạ (danh sách)
- `group_list_text`: chữ của mục danh sách nhóm
- `group_member_regex`: mẫu nhận diện dòng "số thành viên"
- `group_total_regex`: mẫu đọc tổng số nhóm, ví dụ "Nhóm và cộng đồng (51)"
- `no_result_text`: các câu báo không tìm thấy (danh sách)

Hoặc gửi file `ket_qua\...csv` và nội dung nhật ký cho người hỗ trợ.
