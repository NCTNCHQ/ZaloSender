# Nhật ký phiên bản

Từ v1.9, ứng dụng có **2 bản**:
- **Standard** (mặc định khi cài): các chức năng đến v1.7.
- **PRO** (mở khóa bằng Key): thêm các chức năng của v1.8.

Mỗi thay đổi được ghi rõ thuộc **[Cả 2 bản]**, **[Standard]** hay **[PRO]**.

## v1.10.1 — 05/11/2026
**[Cả 2 bản]** Bản thử nghiệm **quy trình phát hành tự động** qua GitHub Actions. Không thay đổi chức năng.
- Mã nguồn và quy trình phát hành được lưu trên kho GitHub NCTNCHQ/ZaloSender.
- Máy đang dùng v1.10 sẽ thấy thông báo "Có phiên bản mới v1.10.1". Đây là dịp thử **cập nhật tự động thật** lần đầu.

## v1.10 — 05/11/2026
**[Cả 2 bản] Cập nhật phiên bản mới qua GitHub**
- Mỗi lần mở (tối đa 1 lần/ngày), ứng dụng tự kiểm tra bản mới tại **github.com/NCTNCHQ/ZaloSender** (mục Releases). Mất mạng thì bỏ qua, không báo lỗi.
- Có bản mới thì hiện thanh **"🔔 Có phiên bản mới vX"** với các nút **Xem có gì mới / ⬇ Cập nhật ngay / Để sau**.
- **An toàn:**
  - Bản cập nhật phải có **chữ ký số của tác giả**, và file tải về phải đúng mã **SHA-256**. Sai thì từ chối.
  - Bản cũ được **sao lưu** (`ban_cu\v<bản cũ>` trong thư mục dữ liệu).
  - Bản mới không mở được thì **tự quay về bản cũ**. Diễn biến được ghi vào `cap_nhat.log`.
- Tự cài thêm thư viện nếu bản mới cần.
- **Bắt buộc cập nhật**: tác giả có thể đánh dấu một bản là bắt buộc (khi bản cũ có lỗi nghiêm trọng). Khi đó thanh thông báo màu đỏ và phải cập nhật mới dùng tiếp được.
- Nút **"🔄 Kiểm tra cập nhật"** trong cửa sổ Giới thiệu.
- Dữ liệu (Key PRO, mẫu tin, ghép nhóm, đã gửi…) **không bị ảnh hưởng** khi cập nhật.

**[Cả 2 bản] Giao diện và thông tin tác giả**
- Nút **"ℹ Giới thiệu & Hỗ trợ"** nổi bật hơn: chữ xanh đậm, viền xanh.
- Cửa sổ Giới thiệu có mục **Tác giả & hỗ trợ**: Nguyễn Công Trung, Congtrung127@gmail.com, kèm nút **Sao chép email** và **Gửi email hỗ trợ** (thư soạn sẵn có bản đang dùng và Mã máy).
- Cửa sổ Nâng cấp PRO có nút **"✉ Gửi email xin Key"** (thư soạn sẵn có Mã máy).

## v1.9.1 — 05/11/2026
**[Cả 2 bản] Sửa lỗi**
- **Cài lại thì mất Key PRO và dữ liệu.** Từ bản này, mọi dữ liệu được lưu ở thư mục cố định của Windows: `%APPDATA%\ZaloSender`, tức `C:\Users\<tên>\AppData\Roaming\ZaloSender`.
  - Dữ liệu gồm: Key PRO, cài đặt, mẫu tin nhắn, ghép nhóm, danh sách nhóm và bạn bè, bộ nhớ đệm "đã gửi", báo cáo, file chẩn đoán, đăng nhập Zalo.
  - Cài lại, chuyển thư mục hay cập nhật bản mới đều **giữ nguyên dữ liệu**.
  - Lần đầu mở v1.9.1, ứng dụng **tự chép dữ liệu cũ** từ thư mục ứng dụng sang (file `DU_LIEU_DA_CHUYEN.txt` ghi lại những gì đã chép).
- **Đã kích hoạt PRO mà vẫn hiện nút vàng "Nâng cấp PRO".**
  - Sau khi nhập Key, giao diện **cập nhật ngay**: tiêu đề, icon, và nút vàng **biến mất**, thay bằng nhãn mờ **"✅ PRO — …"**.
  - Key có hạn **còn ≤ 15 ngày** thì hiện nút cam **"⚠ PRO còn N ngày — Gia hạn"**.
  - Khởi động lại an toàn: chỉ đóng cửa sổ cũ khi bản mới đã mở được. Nếu không tự mở lại được thì báo "Hãy tắt rồi mở lại ứng dụng".

**[Cả 2 bản] Thêm**
- Cửa sổ **ℹ Giới thiệu**:
  - Nút **"📂 Mở thư mục dữ liệu"** và đường dẫn thư mục dữ liệu.
  - Bản PRO có thêm nút **"🔑 Gia hạn / Quản lý Key"**.

## v1.9 — 05/11/2026
**[Cả 2 bản] Hệ thống bản quyền Standard / PRO**
- Cài đặt xong là bản **Standard**. Nút **"⭐ Nâng cấp PRO"** cho thấy **Mã máy**; nhập **Key** thì mở khóa PRO và ứng dụng tự khởi động lại.
- Key được **ký số**, **gắn với từng máy**, có thể **vĩnh viễn** hoặc **có hạn**. Kiểm tra offline, không cần Internet.
- Hết hạn hoặc **Hủy kích hoạt** thì quay về Standard. Dữ liệu vẫn được giữ.
- Nút **"ℹ Giới thiệu"**: bản đang dùng, phiên bản, Mã máy, hạn dùng, danh sách chức năng.
- **Icon PRO** có nhãn vàng (cửa sổ và biểu tượng Desktop).
- **[PRO]** Các chức năng chỉ có ở bản PRO:
  - Quản lý nhiều mẫu tin nhắn
  - Thẻ Bạn bè Zalo, cùng việc ghép khách với bạn bè
  - Lọc theo Chữ đầu
  - Hiển thị Chỉ đã ghép / Chưa ghép / Đã tích
  - Trường {Tên Zalo}
- **[Standard]** Bản Standard vẫn sửa, lưu và khôi phục được 1 mẫu tin nhắn ("AONE"). Các chức năng PRO hiện 🔒.

**[Cả 2 bản] Giao diện mới**
- Giao diện phẳng hiện đại.
- **Thẻ làm việc to, rõ**: thẻ đang mở nền xanh chữ trắng, các thẻ khác có viền rõ.
- **Nút bấm to hơn, viền rõ, đổi màu khi rê chuột**. Các nút chính màu xanh: Chọn file Excel, Chọn thư mục PDF, Tiếp tục, Kiểm tra & gửi, Bắt đầu gửi.
- Thẻ Nhóm / Bạn bè: **bỏ 3 hàng** Sắp xếp / Hiển thị / Chữ đầu.
  - Các lựa chọn chuyển vào **menu chuột phải** (có menu con) và nút **"☰ Sắp xếp / Lọc"**.
  - Dòng **"Đang xem: …"** kèm nút **"✖ Bỏ lọc"** chỉ hiện khi đang sắp xếp hoặc lọc.
- **Cảnh báo chọn nhầm cột SĐT**: cột đã chọn không có số điện thoại hợp lệ nào thì ứng dụng nhắc chọn "(không dùng)".
- Cửa sổ Nâng cấp / Giới thiệu tự co giãn, không bị cắt chữ.

**[Standard] Sửa lỗi** (đã sửa trong v1.8, nay có ở cả bản Standard)
- Gợi ý ghép chấm điểm quá cao ("NHÓM A" bị gợi ý "Nhóm Mây" 86%).
- Nhóm tích trực tiếp (thông báo chung) bị đòi file PDF riêng.

## v1.8 — 05/11/2026
**Thêm mới: Quản lý mẫu tin nhắn** (Bước 2)
- Thanh **"Mẫu tin nhắn"** với các nút:
  - Chọn mẫu ▾
  - **➕ Tạo mới**: tạo từ nội dung đang soạn
  - **💾 Lưu**, **✏ Đổi tên**, **🗑 Xóa** (luôn còn ít nhất 1 mẫu)
  - **⭐ Đặt mặc định**: mẫu mặc định được mở sẵn mỗi lần dùng
- Nút **"↺ Khôi phục mẫu 'tên mẫu'"** tự đổi tên theo mẫu đang chọn. Mặc định ban đầu là **AONE**.
- Có sửa đổi chưa lưu thì hiện **"✱ có sửa đổi chưa lưu"**, và khi đổi sang mẫu khác ứng dụng hỏi có lưu không.
- Mẫu được lưu ở `mau_tin_nhan.json`, không mất khi cập nhật phiên bản.
- Trường mới **{Tên Zalo}**: tên nhóm / bạn bè trên Zalo, dùng được cho mọi người nhận. Thích hợp cho mẫu thông báo chung.

**Thêm mới: Thẻ "🧑‍🤝‍🧑 Bạn bè Zalo"**
- **Lấy danh sách bạn bè từ Zalo** (Danh bạ → Danh sách bạn bè):
  - Tự cuộn đọc hết, kiểm tra với tổng "Bạn bè (N)".
  - Bỏ mục "Bạn mới" (bị lặp lại).
  - **Phát hiện người trùng tên**: người trùng tên **không gửi được** (không phân biệt được).
- **Sắp xếp** (chọn 1): Số đầu tên / A → Z / Z → A / Đã ghép Excel lên trước / Gửi gần nhất lên trước.
- **Hiển thị** (chọn 1): Chỉ tên có số / Chỉ đã ghép Excel / Chỉ chưa ghép / Chỉ đã tích / Mặc định.
- **Thanh chữ cái đầu** (A Ă Â … Y, 0-9), **menu chuột phải**, **📤 Xuất ra Excel**.
- Thêm cột: Mã Dropbox, Trùng tên, Khách hàng đã ghép, Gửi gần nhất.
- **Gửi thông báo chung**: tích bạn bè → chọn mẫu → gửi (chat 1-1). Gửi cho bạn bè đi qua **danh sách bạn bè** trước để chặn người trùng tên.

**Thẻ Nhóm Zalo**: thêm các ô hiển thị *Chỉ đã ghép Excel / Chỉ chưa ghép / Chỉ đã tích*, thanh chữ cái đầu và cột "Gửi gần nhất".

**Ghép Zalo (trước là "Ghép nhóm Zalo")**
- Khách trong Excel ghép được với **nhóm hoặc bạn bè**. Ứng viên có nhãn **[Nhóm]** / **[Bạn bè]**.
- Tên trùng giữa nhóm và bạn bè, hoặc bạn bè trùng tên, thì không cho xác nhận (không phân biệt được khi gửi).

**Sửa lỗi**
- Gợi ý ghép chấm điểm quá cao: "NHÓM A" từng được gợi ý "Nhóm Mây" 86%, nay chỉ còn 25%. Khi so, ứng dụng bỏ các chữ chung như "Nhóm", "Group"; tên ngắn phải trùng hẳn.
- Nhóm / bạn bè **tích trực tiếp** không bị bắt buộc có PDF riêng (chỉ nhận PDF chung).

## v1.7 — 05/11/2026
**Thêm mới: Ghép khách hàng (Excel) với nhóm Zalo khi tên KHÔNG giống nhau**
- Tự tách **mã Dropbox** ở đầu tên:
  - Mã bắt đầu bằng chữ số, có thể kèm chữ, ví dụ `99rs.` → **99rs**, `33-` → **33**.
- Thứ tự ghép:
  1. **Lựa chọn bạn đã xác nhận** (ghi nhớ vĩnh viễn).
  2. Trùng **toàn bộ tên**.
  3. Trùng **mã Dropbox** với **đúng 1** nhóm, ví dụ Excel "99rs. công ty TNN 1 thành viên" ghép với Zalo "99rs. công ty Anh TRUNG".
  4. Trùng **tên công ty** (đã bỏ mã) với đúng 1 nhóm, ví dụ Excel "45. Công ty TNHH Minh Long" ghép với Zalo "Công ty TNHH Minh Long".
  5. **Tên gần giống**: chỉ là **gợi ý**, khi so đã bỏ các chữ chung như Công ty, Cty, TNHH, CP, MTV, 1 thành viên…
- **Chỉ tự ghép khi chắc chắn.** Các trường hợp không rõ ràng phải **chờ bạn xác nhận**, chưa xác nhận thì **không gửi**:
  - Nhiều nhóm cùng mã (ví dụ 3 nhóm mã 33)
  - Gợi ý theo tên gần giống
  - Không tìm thấy nhóm
- Cửa sổ **"🔗 Ghép nhóm Zalo"** ở Bước 1, cạnh ô Tháng, có báo "⚠ N khách cần xác nhận":
  - Ô chọn nhóm xếp theo độ giống, **gõ để tìm**.
  - Các nút **Xác nhận nhóm này**, **Xác nhận tất cả gợi ý**, **Xóa xác nhận**.
  - Lựa chọn được **ghi nhớ vĩnh viễn** (`ghep_nhom.json`), **lần sau không hỏi lại**.
- Cột **"Nhóm Zalo"** ở Bước 1 hiện **tên nhóm thật trên Zalo** đã ghép. Khi gửi, ứng dụng tìm theo tên nhóm thật này.
- Phát hiện **nhiều khách cùng ghép vào 1 nhóm** → không gửi, chờ xử lý.
- **File PDF** ghép được theo **tên Excel**, **mã Dropbox** (`99rs.pdf`) hoặc **tên nhóm Zalo**. Một file khớp nhiều khách → không gửi.
- Bộ nhớ đệm giữ trạng thái "đã gửi" theo **tên trong Excel**, nên không mất khi ghép lại nhóm.

**Thêm mới: Thẻ Nhóm Zalo**
- **Sắp xếp** (chỉ chọn 1): 1. Số đầu tên / 2. Thành viên (nhiều → ít) / 3. A → Z (bảng chữ cái tiếng Việt: A Ă Â … D Đ …). Bỏ tích thì trở về thứ tự như Zalo.
- **Hiển thị**: 1. Chỉ nhóm có số / 2. Mặc định (tất cả).
- **Bấm chuột phải** vào bảng cũng có menu với các mục trên. Ứng dụng ghi nhớ lựa chọn.
- Thêm cột **Mã Dropbox** và **Khách hàng đã ghép (Excel)**.
- Nút **"📤 Xuất ra Excel"**: xuất đúng danh sách đang hiển thị, gồm các cột STT, Tên nhóm, Số thành viên (dạng số), Mã Dropbox, Có số đầu tên, Khách đã ghép. File có dòng tiêu đề cố định và nút lọc.

**An toàn**
- Tin nhắn có chữ "kèm theo" / "đính kèm" mà **chưa chọn thư mục PDF** thì **không gửi**, kèm lý do.
- Thư mục PDF được lưu ngay khi chọn.

## v1.6 — 05/11/2026
**Sửa lỗi: tin nhắn gửi đi bị thiếu dòng** (NHÓM A chỉ còn dòng đầu, NHÓM B/C mất nhiều dòng)

Nguyên nhân: ứng dụng gõ từng dòng rồi nhấn Shift+Enter quá nhanh. Ô soạn tin của Zalo cần một chút thời gian để tạo dòng mới, nên chữ gõ vào trong lúc đó bị mất. Cách sửa:
- **Dán cả tin nhắn một lần** (Ctrl+V qua bộ nhớ tạm) thay vì gõ từng dòng.
- **Đọc lại ô soạn tin, đối chiếu từng dòng** với tin đã soạn, khớp mới nhấn gửi.
  - Không khớp thì xóa và thử **gõ chậm** (chờ Zalo xử lý mỗi lần xuống dòng).
  - Vẫn không khớp thì **xóa, KHÔNG gửi** (cả PDF), ghi lỗi vào báo cáo.
- Sau khi nhấn gửi, kiểm tra ô soạn tin đã trống (tin đã thực sự được gửi).
- **Chạy thử** cũng dán và kiểm tra nội dung như thật, rồi xóa, không gửi.

**Thêm mới: Bộ nhớ đệm tin nhắn** (`bo_nho_dem\<năm-tháng>.json`)
- **Tự động soạn sẵn** tin nhắn cho từng khách ngay khi chọn file Excel, theo mẫu cố định + Tháng + Số tiền. Không cần chỉnh tay.
- Bảng Bước 1 có thêm:
  - Ô **Tháng**
  - Cột **"Gửi"**: ⏳ Chưa gửi / ✅ Đã gửi + giờ gửi / ⚠ Đã gửi tin, thiếu PDF
- Gửi **đúng nguyên văn** nội dung trong bộ nhớ đệm.
- Ghi **"Đã gửi"** ngay sau mỗi khách, nên **không bao giờ gửi trùng**. Bị dừng giữa chừng thì lần sau chỉ gửi những khách chưa gửi.
- Khách đã gửi: xem trước hiện đúng nội dung **đã gửi**. Nếu Excel đổi sau khi gửi, cột Gửi ghi chú *(Excel đã đổi sau khi gửi)*.
- Nút **"↺ Đặt lại: Chưa gửi"** để gửi lại cho một khách (ví dụ sau khi đã thu hồi tin).
- Đổi số tiền trong Excel: khách **chưa gửi** tự được soạn lại theo số mới.
- Mỗi tháng một bộ nhớ đệm riêng.

**Lưu ý:** trong lúc gửi, nội dung đã sao chép (Ctrl+C) trước đó trên máy sẽ bị thay bằng tin nhắn.

## v1.5 — 05/11/2026
**Sửa lỗi: "Không tìm thấy cuộc trò chuyện có tên trùng khớp hoàn toàn"**

Ứng dụng gõ tên nhóm vào ô tìm kiếm Zalo nhưng không nhận ra dòng kết quả, nên không bấm vào nhóm. Nguyên nhân: v1.1–v1.4 nhận diện kết quả theo cấu trúc trang **phỏng đoán**, khác với Zalo thật. Cách sửa:
- **Nhận diện bằng chữ hiển thị**, không phụ thuộc cấu trúc trang:
  - Tìm trong cột kết quả bên trái dòng có tên **trùng khớp hoàn toàn**.
  - Ghép lại tên bị tách do Zalo tô đậm phần chữ khớp (ví dụ "**NHÓM** A").
  - Không phân biệt kiểu mã hóa chữ tiếng Việt.
- **Cách dự phòng**: nếu ô tìm kiếm không ra, ứng dụng vào **Danh bạ → Danh sách nhóm và cộng đồng**, gõ tên vào ô "Tìm kiếm..." của danh sách rồi bấm vào nhóm.
- **Kiểm tra trước khi gửi**: sau khi bấm, tiêu đề khung chat phải đúng tên nhóm. Không đúng hoặc không xác minh được thì **không gửi**.
- **Tự lưu file chẩn đoán** (ảnh + cấu trúc trang, tối đa 3 lần mỗi đợt) vào `chan_doan\` khi không tìm được.

**Sửa lỗi khác**
- File PDF chung (cùng một file) gửi cho nhiều khách liên tiếp: từ khách thứ 2 trở đi trình duyệt không tải file lên. Đã sửa.
- Không còn chờ "nghỉ 45s" sau khách **bị lỗi / chưa gửi được gì**.

## v1.4 — 05/11/2026
**Thay đổi theo góp ý: "chỉ cần chọn file Excel là tin nhắn tự soạn theo tên khách và số tiền"**
- **Nút "Chọn thư mục PDF" chuyển lên Bước 1**, ngay cạnh nút "Chọn file Excel" (ứng dụng ghi nhớ thư mục).
- **Bảng ở Bước 1 hiện đủ thông tin của từng khách** ngay sau khi chọn file:
  - Số tiền đã định dạng (5.000.000)
  - **File PDF** tự ghép
  - **Nhóm Zalo** (có / không thấy / trùng tên)
  - **Trạng thái** (Sẵn sàng / lý do bị bỏ qua)
- **Xem trước tin nhắn ngay ở Bước 1**: bấm vào tên khách là thấy toàn bộ tin nhắn của khách đó.
- **Chữ thay đổi theo khách được tô đỏ** trong ô xem trước (Tháng, Số tiền…), giống ảnh mẫu.
- **Ô xem trước hiện đủ cả tin nhắn.** Trước đây ô chỉ cao 5 dòng nên dòng "Số tiền thanh toán" bị che, trông như chưa điền số tiền.
- **Tự gộp người nhận trùng:** tích cùng một tên ở cả thẻ Khách hàng và thẻ Nhóm Zalo thì chỉ gửi **1 lần**, dùng dữ liệu Excel. Trước đây trường hợp này báo lỗi "Có nhiều người nhận trùng tên".
- Bảng khách hàng: bấm **ô ☐** để tích / bỏ tích, bấm **vào tên** để xem trước.
- Bước 2 gọn hơn: thư mục PDF chỉ hiển thị (chọn ở Bước 1); mẫu tin nhắn được lưu ngay khi sửa.
- Sửa lỗi hiển thị trên màn hình laptop 1366×768: nút "Tiếp tục" và khung nhật ký không còn bị khuất.

## v1.3 — 05/11/2026
**Thêm mới: quy trình gửi đề nghị thanh toán hằng tháng "mở lên → kiểm tra → bấm gửi"**
- **Tự ghép file PDF theo tên**:
  - Chọn thư mục PDF **một lần**, ứng dụng ghi nhớ cho các lần sau.
  - File đặt tên giống tên khách / tên nhóm Zalo, ví dụ `Nhóm F4.pdf`. Có thể đặt theo SĐT.
  - Một khách nhiều file: `Tên_HD01.pdf`, `Tên - Hợp đồng.pdf`.
  - Không nhầm "Nguyễn Văn An" với "Nguyễn Văn Anh".
  - Tên có ký tự Windows không cho phép (`/ \ : * ? " < > |`) thì tên file thay ký tự đó bằng `_`.
- **Ô "Tháng"** ở Bước 2: tự điền tháng trước, dùng trong tin nhắn bằng `{Tháng}`.
- **Tự định dạng số tiền**: cột có chữ "tiền", `5000000` thành `5.000.000`.
- **Mẫu tin nhắn A-One** có sẵn, kèm nút "Khôi phục mẫu A-One". Ứng dụng nhớ mẫu tin nhắn lần trước.
- **Bảng kiểm tra trước khi gửi**:
  - Mỗi người nhận một dòng: có nhóm Zalo không, file PDF nào, số tiền, trạng thái.
  - Dòng lỗi màu đỏ được đưa lên đầu.
  - Cảnh báo các file PDF không khớp với ai (thường do đặt sai tên).
- **Tự mở lại file Excel lần trước** khi khởi động và **tự tích chọn tất cả** khách hàng. Ghi nhớ các cột đã chọn.
- Excel không có cột SĐT thì tự dùng **cột tên khách để tìm nhóm Zalo**.
- Tùy chọn **"Tên phải có trong danh sách nhóm Zalo đã lấy"**: phát hiện sai tên nhóm **trước khi gửi**.
- Xem trước hiển thị cả tên file PDF sẽ gửi kèm.

**An toàn: bỏ qua người nhận khi**
- Thiếu PDF
- Thiếu dữ liệu trong tin (ví dụ ô Số tiền trống)
- Không có nhóm trong danh sách, hoặc có nhóm trùng tên
- Có 2 người nhận trùng tên

Không bao giờ gửi tin còn chữ dạng `{Số tiền}`.

**Thay đổi**
- Cửa sổ tự co vừa màn hình laptop (từ 1366×768).
- File mẫu mới: `mau_thanh_toan.xlsx` cùng thư mục `pdf_mau\` (PDF đặt theo tên khách).

## v1.2 — 05/11/2026
**Sửa lỗi**
- **Không tạo được biểu tượng trên Desktop**: Windows (WScript.Shell) không lưu được file shortcut có dấu tiếng Việt, nên tên bị thành `G?i tin Zalo.lnk`. Cách sửa:
  - Tạo shortcut tên không dấu ở thư mục tạm, rồi chuyển ra Desktop và đổi tên thành **"Gửi tin Zalo"**.
  - Nếu đổi tên lỗi thì giữ tên không dấu "Gui tin Zalo".
- **"Không đọc được danh sách nhóm"**: viết lại phần đọc nhóm dựa theo giao diện thật của Zalo Web (Danh bạ → Danh sách nhóm và cộng đồng):
  - Nhận diện được chữ tiếng Việt mã hóa Unicode kiểu tổ hợp, và trường hợp số với chữ "thành viên" nằm ở hai phần tử riêng.
  - Không lấy nhầm số in trên ảnh đại diện (ví dụ "12", "5") làm tên nhóm.
  - Đọc tổng số nhóm ở dòng "Nhóm và cộng đồng (51)" để biết đã đọc đủ chưa.
  - Giữ riêng các nhóm trùng tên, để khi gửi ứng dụng cảnh báo và bỏ qua, tránh gửi nhầm.
  - Chờ danh sách tải xong (tối đa 10 giây). Có cách cuộn dự phòng bằng con lăn chuột.

**Thêm mới**
- **Tự chẩn đoán lỗi**: khi không lấy được nhóm, hoặc lấy thiếu so với tổng Zalo báo, ứng dụng tự lưu ảnh chụp màn hình và cấu trúc trang vào thư mục `chan_doan\`, để gửi cho người hỗ trợ.

## v1.1 — 05/11/2026
**Thêm mới**
- **Icon riêng** cho ứng dụng: bong bóng chat, máy bay giấy và mũi tên tự động. Icon hiện ở cửa sổ ứng dụng và biểu tượng trên Desktop.
- **File cài `CAI_DAT.bat`**:
  - Tự kiểm tra Python và Google Chrome; thiếu thì mở trang tải về.
  - Tự cài thư viện và tạo biểu tượng **"Gửi tin Zalo"** trên Desktop.
- **Gửi kèm file PDF** (sau tin nhắn):
  - *File PDF chung*: chọn ở Bước 2, gửi cho tất cả người nhận.
  - *File PDF riêng*: chọn cột tên file trong Excel và thư mục chứa PDF. Một ô có thể ghi nhiều file, cách nhau bằng dấu `;`.
  - Thiếu file thì bỏ qua người nhận đó và ghi lý do vào báo cáo.
- **Gửi vào nhóm Zalo**:
  - Thẻ **"Nhóm Zalo"** có nút **"Lấy danh sách nhóm từ Zalo"**. Danh sách được lưu lại cho lần sau.
  - Cột **"Tên Zalo / tên nhóm"** trong Excel: dòng không có SĐT sẽ tìm theo tên này.
  - Chỉ gửi khi tên **trùng khớp hoàn toàn**, và kiểm tra lại tiêu đề cuộc trò chuyện trước khi gửi.
- Xem trước tin nhắn cho **bất kỳ** người nhận nào, không chỉ người đầu tiên.
- Màn hình xác nhận trước khi gửi: cho biết bao nhiêu người sẽ được gửi, bao nhiêu bị bỏ qua, tổng số file PDF.
- Báo cáo kết quả có thêm các cột: Loại, Tên tìm trên Zalo, Tin nhắn, PDF đã gửi.

**Thay đổi**
- Dùng **Google Chrome có sẵn trên máy**, không tải thêm trình duyệt Chromium (khoảng 150MB).
- Số phiên bản hiện ở tiêu đề cửa sổ và tên file zip.
- Tìm kiếm ổn định hơn: không kết luận "không tìm thấy" khi Zalo chưa hiện xong kết quả, và tự bỏ khoảng trắng thừa trong tên.
- Nếu ứng dụng gặp lỗi khi khởi động: hiện thông báo và ghi chi tiết vào file `loi.txt`.

## v1.0
- Đọc file khách hàng (.xlsx/.xls/.csv), tích chọn khách hàng.
- Soạn tin nhắn có chèn trường `{Tên cột}`, gửi qua Zalo Web theo số điện thoại.
- Nghỉ ngẫu nhiên giữa các tin, chế độ chạy thử, báo cáo kết quả ra file CSV.
