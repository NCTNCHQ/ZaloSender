"""CÔNG CỤ PHÁT HÀNH BẢN CẬP NHẬT — chỉ tác giả giữ (dùng chung khoa_bi_mat.pem với công cụ Tạo Key).

Tạo file phien_ban.json (có CHỮ KÝ SỐ) cho một bản zip mới. Sau đó đăng lên GitHub Releases
(kho NCTNCHQ/ZaloSender) với tag 'v<phiên bản>', đính kèm 2 file: file zip + phien_ban.json.

Dùng giao diện:   bấm đúp CHAY_PHAT_HANH.bat
Dùng dòng lệnh:   python phat_hanh.py --zip ZaloSender_v1.11.zip --notes "..." [--required]
"""
import argparse
import base64
import datetime
import hashlib
import json
import os
import re
import sys

from cryptography.hazmat.primitives import serialization

HERE = os.path.dirname(os.path.abspath(__file__))
KEY_FILE = os.path.join(HERE, "khoa_bi_mat.pem")
REPO = "NCTNCHQ/ZaloSender"


def canonical(data):  # phải GIỐNG updater.canonical trong ứng dụng
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def version_from_name(name):
    m = re.search(r"v(\d+(?:\.\d+)+)", os.path.basename(name))
    return m.group(1) if m else ""


def make_manifest(zip_path, notes, required=False, version=None):
    version = version or version_from_name(zip_path)
    if not version:
        raise ValueError("Không đọc được số phiên bản từ tên file (cần dạng ZaloSender_v1.11.zip)")
    h = hashlib.sha256()
    with open(zip_path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    name = os.path.basename(zip_path)
    data = {"version": version, "file": name, "size": os.path.getsize(zip_path), "sha256": h.hexdigest(),
            "url": f"https://github.com/{REPO}/releases/download/v{version}/{name}",
            "notes": notes.strip(), "required": bool(required), "date": f"{datetime.date.today():%d/%m/%Y}"}
    pk = serialization.load_pem_private_key(open(KEY_FILE, "rb").read(), None)
    return {"data": data, "sig": base64.b64encode(pk.sign(canonical(data))).decode()}


def write_manifest(zip_path, notes, required=False, out_dir=None):
    m = make_manifest(zip_path, notes, required)
    out = os.path.join(out_dir or os.path.dirname(os.path.abspath(zip_path)), "phien_ban.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(m, f, ensure_ascii=False, indent=1)
    return out, m


def gui():
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
    root = tk.Tk()
    root.title("Công cụ phát hành bản cập nhật – Gửi tin Zalo")
    f = ttk.Frame(root, padding=14)
    f.pack(fill="both", expand=True)
    zp = tk.StringVar()
    ttk.Label(f, text="File zip bản mới (tên dạng ZaloSender_v1.11.zip):", font=("", 10, "bold")).pack(anchor="w")
    r = ttk.Frame(f)
    r.pack(fill="x")
    ttk.Entry(r, textvariable=zp, width=70).pack(side="left")
    ttk.Button(r, text="Chọn...", command=lambda: zp.set(filedialog.askopenfilename(
        filetypes=[("Zip", "*.zip")]) or zp.get())).pack(side="left", padx=4)
    ttk.Label(f, text="Có gì mới (hiện cho người dùng):", font=("", 10, "bold")).pack(anchor="w", pady=(10, 0))
    notes = tk.Text(f, height=10, width=80)
    notes.pack()
    req = tk.BooleanVar()
    ttk.Checkbutton(f, text="BẮT BUỘC cập nhật (bản cũ có lỗi nghiêm trọng)", variable=req).pack(anchor="w", pady=6)
    out = ttk.Label(f, text="", foreground="#1e8449", wraplength=640)

    def run():
        try:
            path, m = write_manifest(zp.get(), notes.get("1.0", "end"), req.get())
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))
            return
        out.config(text=f"✅ Đã tạo {path}\nPhiên bản v{m['data']['version']} — SHA-256 {m['data']['sha256'][:16]}...\n"
                        f"Bây giờ đăng lên GitHub: Releases → Draft a new release → tag v{m['data']['version']} → "
                        f"đính kèm {m['data']['file']} và phien_ban.json → Publish.")
    ttk.Button(f, text="✍ Tạo phien_ban.json (ký số)", command=run).pack(anchor="w")
    out.pack(anchor="w", pady=8)
    root.mainloop()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        ap = argparse.ArgumentParser()
        ap.add_argument("--zip", required=True)
        ap.add_argument("--notes", default="")
        ap.add_argument("--notes-file")
        ap.add_argument("--required", action="store_true")
        ap.add_argument("--out")
        a = ap.parse_args()
        text = open(a.notes_file, encoding="utf-8").read() if a.notes_file else a.notes
        path, m = write_manifest(a.zip, text, a.required, a.out)
        print("Đã tạo", path, "| v" + m["data"]["version"], "| sha256", m["data"]["sha256"])
    else:
        gui()
