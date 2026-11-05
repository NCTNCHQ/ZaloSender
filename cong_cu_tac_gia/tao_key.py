"""CÔNG CỤ TẠO KEY PRO — CHỈ NHÀ CUNG CẤP GIỮ, KHÔNG GỬI CHO KHÁCH.

File khoa_bi_mat.pem là KHÓA BÍ MẬT: ai có file này đều tạo được Key PRO. Hãy sao lưu cẩn thận và không chia sẻ.
Cần file license.py (lấy từ thư mục ứng dụng ZaloSender) đặt cùng thư mục với công cụ này.
"""
import csv
import datetime
import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import license as lic  # noqa: E402
from cryptography.hazmat.primitives import serialization  # noqa: E402

KEY_FILE = os.path.join(HERE, "khoa_bi_mat.pem")
LOG_FILE = os.path.join(HERE, "so_key_da_cap.csv")
DURATIONS = [("Vĩnh viễn", None), ("1 tháng", 1), ("3 tháng", 3), ("6 tháng", 6), ("1 năm", 12), ("2 năm", 24),
             ("Tự chọn ngày hết hạn", "custom")]


def add_months(d, n):
    y, m = divmod(d.month - 1 + n, 12)
    y, m = d.year + y, m + 1
    for day in (d.day, 30, 29, 28):
        try:
            return d.replace(year=y, month=m, day=day)
        except ValueError:
            continue


class Tool(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Công cụ tạo Key PRO – Gửi tin Zalo")
        self.geometry("760x520")
        try:
            self.pk = serialization.load_pem_private_key(open(KEY_FILE, "rb").read(), None)
        except Exception as e:
            messagebox.showerror("Thiếu khóa bí mật", f"Không đọc được {KEY_FILE}\n{e}")
            self.destroy()
            return
        f = ttk.Frame(self, padding=14)
        f.pack(fill="both", expand=True)
        ttk.Label(f, text="Mã máy của khách (khách lấy ở nút '⭐ Nâng cấp PRO' trong ứng dụng):",
                  font=("", 10, "bold")).grid(row=0, column=0, columnspan=3, sticky="w")
        self.machine = tk.StringVar()
        ttk.Entry(f, textvariable=self.machine, width=40, font=("Consolas", 12)).grid(row=1, column=0, sticky="w", pady=4)
        ttk.Label(f, text="Tên khách / ghi chú:").grid(row=2, column=0, sticky="w", pady=(10, 0))
        self.note = tk.StringVar()
        ttk.Entry(f, textvariable=self.note, width=50).grid(row=3, column=0, sticky="w")
        ttk.Label(f, text="Thời hạn:").grid(row=4, column=0, sticky="w", pady=(10, 0))
        self.dur = ttk.Combobox(f, state="readonly", values=[d[0] for d in DURATIONS], width=24)
        self.dur.current(0)
        self.dur.grid(row=5, column=0, sticky="w")
        ttk.Label(f, text="Ngày hết hạn (nếu tự chọn, dạng dd/mm/yyyy):").grid(row=6, column=0, sticky="w", pady=(10, 0))
        self.custom = tk.StringVar()
        ttk.Entry(f, textvariable=self.custom, width=14).grid(row=7, column=0, sticky="w")
        ttk.Button(f, text="🔑 Tạo Key", command=self.make).grid(row=8, column=0, sticky="w", pady=14)
        ttk.Label(f, text="Key (gửi cho khách):", font=("", 10, "bold")).grid(row=9, column=0, sticky="w")
        self.out = tk.Text(f, height=5, width=86, font=("Consolas", 10), wrap="char")
        self.out.grid(row=10, column=0, columnspan=3, sticky="w")
        ttk.Button(f, text="📋 Sao chép Key", command=self.copy).grid(row=11, column=0, sticky="w", pady=8)
        self.info = ttk.Label(f, text="", foreground="#1e8449")
        self.info.grid(row=12, column=0, columnspan=3, sticky="w")
        ttk.Label(f, text=f"Mọi Key đã cấp được ghi vào: {LOG_FILE}", foreground="gray").grid(row=13, column=0, sticky="w")

    def make(self):
        m = lic.normalize_machine(self.machine.get())
        if not m:
            messagebox.showwarning("Sai mã máy", "Mã máy phải có dạng ZS-XXXX-XXXX-XXXX.")
            return
        label, months = DURATIONS[self.dur.current()]
        today = datetime.date.today()
        if months == "custom":
            try:
                exp = datetime.datetime.strptime(self.custom.get().strip(), "%d/%m/%Y").date()
            except ValueError:
                messagebox.showwarning("Sai ngày", "Ngày hết hạn phải có dạng dd/mm/yyyy, ví dụ 31/12/2027.")
                return
        else:
            exp = add_months(today, months) if months else None
        key = lic.make_key(self.pk, m, exp)
        chk = lic.check_key(key, m)
        if not chk["ok"]:
            messagebox.showerror("Lỗi", chk["reason"])
            return
        self.out.delete("1.0", "end")
        self.out.insert("1.0", key)
        hsd = exp.strftime("%d/%m/%Y") if exp else "Vĩnh viễn"
        self.info.config(text=f"✅ Đã tạo Key PRO cho máy {m} — hạn dùng: {hsd}")
        new = not os.path.exists(LOG_FILE)
        with open(LOG_FILE, "a", newline="", encoding="utf-8-sig") as fh:
            w = csv.writer(fh)
            if new:
                w.writerow(["Ngày cấp", "Mã máy", "Khách / ghi chú", "Hạn dùng", "Key"])
            w.writerow([today.strftime("%d/%m/%Y"), m, self.note.get(), hsd, key])

    def copy(self):
        self.clipboard_clear()
        self.clipboard_append(self.out.get("1.0", "end").strip())
        self.info.config(text="📋 Đã sao chép Key.")


if __name__ == "__main__":
    Tool().mainloop()
