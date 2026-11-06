"""Ứng dụng gửi tin nhắn Zalo tự động cho khách hàng / nhóm được chọn.

Bước 1: Chọn khách hàng (từ file Excel/CSV) và/hoặc nhóm Zalo (lấy từ Zalo Web) bằng cách tích chọn.
Bước 2: Nhập nội dung tin nhắn, chọn file PDF đính kèm -> Gửi (tin nhắn trước, PDF sau).
"""
import csv
import datetime
import json
import os
import queue
import random
import re
import sys
import threading
import time
import tkinter as tk
import traceback
from collections import Counter
from tkinter import filedialog, messagebox, ttk

import core
import license as lic
from version import APP_NAME, APP_VERSION, AUTHOR, AUTHOR_EMAIL

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_ICO = os.path.join(BASE_DIR, "icon.ico")
ICON_PNG = os.path.join(BASE_DIR, "icon.png")
import datadir  # noqa: E402

GROUPS_FILE = datadir.path("nhom_zalo.json")
CHECK, UNCHECK = "☑", "☐"
NONE = "(không dùng)"
GROUP_FIELD = "Tên nhóm"
MONTH_FIELD = "Tháng"
DATE_FIELD = "Đến ngày"     # v1.11: lấy từ dòng "Từ ngày … đến ngày …" của file công nợ
AMOUNT_FIELD = "Số tiền"    # v1.11: luôn dùng được {Số tiền} = cột số tiền đã chọn
DEFAULT_TEMPLATE = """Công ty A-One Kính gửi Quý Khách hàng đề nghị thanh toán phí dịch vụ Tháng {Tháng} và hóa đơn kèm theo.
Kính đề nghị quý khách hàng thanh toán số tiền trên bằng Chuyển Khoản trong vòng 7 ngày từ khi nhận được hóa đơn

Thông tin chi tiết
Công Ty TNHH Tư Vấn A-one
Số TK: 25058788
Tại Ngân hàng Thương mại cổ phần Kỹ Thương Việt Nam (Techcombank) – Trụ sở vận hành
Số tiền thanh toán: {Số tiền} VNĐ

Trân Trọng cảm ơn quý khách hàng!"""
# v1.11: mẫu cho file công nợ của kế toán (số tiền = tổng dư nợ cộng dồn đến ngày lập báo cáo)
CONG_NO_NAME = "AONE – Công nợ"
CONG_NO_TEMPLATE = """Công ty A-One kính gửi Quý Khách hàng thông báo công nợ phí dịch vụ tính đến ngày {Đến ngày} và hóa đơn kèm theo.
Kính đề nghị quý khách hàng thanh toán số tiền trên bằng Chuyển Khoản trong vòng 7 ngày từ khi nhận được hóa đơn

Thông tin chi tiết
Công Ty TNHH Tư Vấn A-one
Số TK: 25058788
Tại Ngân hàng Thương mại cổ phần Kỹ Thương Việt Nam (Techcombank) – Trụ sở vận hành
Tổng số tiền cần thanh toán: {Số tiền} VNĐ

Trân Trọng cảm ơn quý khách hàng!"""


FRIEND_FIELD = "Tên bạn bè"
ZALO_FIELD = "Tên Zalo"  # v1.8: trường chung cho mọi người nhận (tên nhóm / bạn bè trên Zalo)
VN_LETTERS = ["A", "Ă", "Â", "B", "C", "D", "Đ", "E", "Ê", "G", "H", "I", "K", "L", "M", "N", "O", "Ô", "Ơ",
              "P", "Q", "R", "S", "T", "U", "Ư", "V", "X", "Y", "0-9"]
LIST_KINDS = {
    "nhom": {"unit": "nhóm", "file": "nhom_zalo.json", "fetch": "🔄 Lấy danh sách nhóm từ Zalo",
             "name_col": "Tên nhóm", "export": "DanhSachNhomZalo", "sheet": "Nhóm Zalo",
             "sorts": (("num", "1. Số đầu tên"), ("mem", "2. Thành viên (nhiều → ít)"), ("az", "3. A → Z")),
             "shows": (("num", "1. Chỉ nhóm có số"), ("matched", "2. Chỉ đã ghép Excel"),
                       ("unmatched", "3. Chỉ chưa ghép"), ("checked", "4. Chỉ đã tích ☑"),
                       ("all", "5. Mặc định (tất cả)")),
             "hint": "Tích ở đây để gửi cho nhóm KHÔNG có trong file Excel (thông báo chung). "
                     "Nhóm đã ghép với khách trong Excel sẽ tự gộp (chỉ gửi 1 lần)."},
    "ban": {"unit": "bạn bè", "file": "ban_be_zalo.json", "fetch": "🔄 Lấy danh sách bạn bè từ Zalo",
            "name_col": "Tên bạn bè", "export": "DanhSachBanBeZalo", "sheet": "Bạn bè Zalo",
            "sorts": (("num", "1. Số đầu tên"), ("az", "2. A → Z"), ("za", "3. Z → A"),
                      ("matched", "4. Đã ghép Excel lên trước"), ("recent", "5. Gửi gần nhất lên trước")),
            "shows": (("num", "1. Chỉ tên có số"), ("matched", "2. Chỉ bạn đã ghép Excel"),
                      ("unmatched", "3. Chỉ bạn chưa ghép"), ("checked", "4. Chỉ bạn đã tích ☑"),
                      ("all", "5. Mặc định (tất cả)")),
            "hint": "Tích để gửi thông báo chung cho bạn bè. Khách trong Excel là bạn bè thì ghép ở '🔗 Ghép Zalo'. "
                    "Người TRÙNG TÊN sẽ không được gửi (không phân biệt được)."},
}


def set_icon(win):
    pro = lic.is_pro()
    ico = os.path.join(BASE_DIR, "icon_pro.ico" if pro else "icon.ico")
    png = os.path.join(BASE_DIR, "icon_pro.png" if pro else "icon.png")
    try:
        if sys.platform.startswith("win") and os.path.exists(ico):
            win.iconbitmap(ico)
        elif os.path.exists(png):
            win._icon_img = tk.PhotoImage(file=png)
            win.iconphoto(True, win._icon_img)
    except Exception:
        pass


def app_title():
    return f"{APP_NAME} – {lic.get().edition} v{APP_VERSION}"


def setup_style(root):
    """v1.9: giao diện phẳng, thẻ (tab) to rõ, nút to có viền rõ, nút chính màu xanh."""
    st = ttk.Style(root)
    try:
        st.theme_use("clam")
    except tk.TclError:
        pass
    blue, blue_dark, line, light = "#0068FF", "#0050C8", "#8A97A8", "#EEF2F7"
    base = ("Segoe UI", 10) if sys.platform.startswith("win") else ("", 10)
    st.configure(".", font=base)
    st.configure("TButton", padding=(12, 6), borderwidth=1, relief="solid", bordercolor=line,
                 background="#FFFFFF", lightcolor="#FFFFFF", darkcolor=line)
    st.map("TButton", background=[("pressed", "#D6E4FF"), ("active", "#E8F0FF")],
           bordercolor=[("active", blue)])
    st.configure("Accent.TButton", font=(base[0], 10, "bold"), foreground="#FFFFFF", background=blue,
                 bordercolor=blue_dark, lightcolor=blue, darkcolor=blue_dark, padding=(14, 7))
    st.map("Accent.TButton", background=[("pressed", blue_dark), ("active", "#1A7BFF"), ("disabled", "#9DB8E6")],
           foreground=[("disabled", "#EEF2F7")])
    st.configure("Pro.TButton", font=(base[0], 10, "bold"), foreground="#5A3A00", background="#FFC400",
                 bordercolor="#C79500", lightcolor="#FFD84D", darkcolor="#C79500", padding=(12, 6))
    st.map("Pro.TButton", background=[("pressed", "#E0A800"), ("active", "#FFD84D")])
    # Thẻ làm việc: to, viền rõ, thẻ đang mở nền xanh chữ trắng
    st.configure("TNotebook", background=light, borderwidth=0, tabmargins=(6, 6, 6, 0))
    st.configure("TNotebook.Tab", font=(base[0], 11, "bold"), padding=(22, 10), borderwidth=2,
                 background="#DCE3EC", foreground="#33475B", bordercolor=line, lightcolor="#DCE3EC")
    st.map("TNotebook.Tab", background=[("selected", blue), ("active", "#C7D6EA")],
           foreground=[("selected", "#FFFFFF")], bordercolor=[("selected", blue_dark)],
           padding=[("selected", (26, 12))], expand=[("selected", (2, 2, 2, 0))])
    st.configure("Treeview", rowheight=24, bordercolor=line, borderwidth=1)
    st.configure("Treeview.Heading", font=(base[0], 10, "bold"), background="#E3EAF3", relief="solid",
                 borderwidth=1, bordercolor=line, padding=(4, 5))
    st.map("Treeview", background=[("selected", "#CFE0FF")], foreground=[("selected", "#000000")])
    st.configure("TCombobox", padding=4, arrowsize=16, bordercolor=line)
    st.configure("TEntry", padding=4, bordercolor=line)
    st.configure("TCheckbutton", padding=(2, 3))
    st.configure("Muted.TLabel", foreground="#6B7785")
    # v1.10: nút Giới thiệu & Hỗ trợ — nổi bật hơn nút thường một chút (chữ xanh đậm, viền xanh)
    st.configure("Info.TButton", font=(base[0], 10, "bold"), foreground=blue_dark, bordercolor=blue,
                 darkcolor=blue, padding=(14, 6))
    st.map("Info.TButton", background=[("pressed", "#D6E4FF"), ("active", "#EAF2FF")],
           bordercolor=[("active", blue_dark)])
    root.configure(background=st.lookup(".", "background"))
    return st


def build_plans(targets, tpl, month, folder, shared_pdfs, has_pdf_col, groups, check_groups, only=None,
                den_ngay="", internal_kw=("xu ly",)):
    """Tính trước cho từng người nhận: nội dung, PDF, kiểm tra nhóm Zalo, lỗi.
    Dùng chung cho Bước 1 (hiện trong bảng), xem trước và Bước 2 (gửi).
    Trả về (plans, các_file_PDF_trong_thư_mục_không_khớp_ai)."""
    extra = {MONTH_FIELD: (month or "").strip(), DATE_FIELD: (den_ngay or "").strip()}
    folder = (folder or "").strip()
    auto_pdf = bool(folder) and not has_pdf_col
    index = core.index_pdf_folder(folder) if auto_pdf else {}
    missing_shared = [p for p in shared_pdfs if not os.path.isfile(p)]
    group_names = [core.norm_name(g["name"]) for g in groups]
    check_groups = check_groups and bool(group_names)
    ident = lambda t: core.norm_name(t["cust_key"]) if t.get("cust_key") else core.file_key(t["label"] or t["search_name"])
    key_count = Counter(ident(t) for t in targets)
    zalo_count = Counter(core.norm_name(t["search_name"]) for t in targets
                         if t["search_name"] and not t["phone"] and t.get("match", {}).get("status", core.MATCH_NAME)
                         in core.MATCH_OK)
    # PDF: file công nợ -> theo Số Dropbox (hoặc file chọn tay); file thường -> tên Excel / nhóm / SĐT / mã
    pdf_hits, pdf_missing_manual = {}, {}
    if auto_pdf:
        for i, t in enumerate(targets):
            if t.get("pdf_manual"):
                found = [os.path.join(folder, n) for n in t["pdf_manual"] if os.path.isfile(os.path.join(folder, n))]
                pdf_hits[i] = [os.path.abspath(f) for f in found]
                pdf_missing_manual[i] = [n for n in t["pdf_manual"] if not os.path.isfile(os.path.join(folder, n))]
            elif "code_parsed" in t:
                pdf_hits[i] = core.pdf_by_code(t["code_parsed"], index)
            else:
                keys = [t["label"], t.get("excel_name", ""), t["search_name"], t["phone"],
                        core.dropbox_code(t.get("excel_name") or t["label"])]
                pdf_hits[i] = core.match_pdfs(dict.fromkeys(k for k in keys if k), index)
    pdf_users = Counter(f for fs in pdf_hits.values() for f in fs)
    no_pdf_source = not folder and not has_pdf_col and not shared_pdfs
    plans, used = [], set()
    for i, t in enumerate(targets):
        if only is not None and i not in only:
            continue
        ttpl = t.get("tpl_text") or tpl  # v1.11: mẫu tin riêng cho khách (PRO)
        fields = list(dict.fromkeys(core._PLACEHOLDER.findall(ttpl or "")))
        # tin nhắn nói "kèm theo" mà không có nguồn PDF nào -> không gửi (tránh gửi thiếu hóa đơn)
        needs_pdf = bool(re.search(r"kem theo|dinh kem|attached", core.strip_accents(ttpl or "")))
        zf = {ZALO_FIELD: t["search_name"] or t["label"] or t["phone"]} if lic.is_pro() else {}  # {Tên Zalo}: PRO
        row = core.prepare_row(t["row"], {**extra, **zf})
        p = {"t": t, "row": row, "msg": core.render_message(ttpl, row) if ttpl else "", "tpl": ttpl,
             "files": [], "error": "", "zalo": "", "data": "", "warn": ""}
        p["data"] = "; ".join(f"{m}: {core.render_message('{' + m + '}', row)}" for m in fields
                              if m not in (MONTH_FIELD, DATE_FIELD))
        errors = []
        if missing_shared:
            errors.append("Thiếu file PDF chung: " + ", ".join(os.path.basename(m) for m in missing_shared))
        if needs_pdf and no_pdf_source:
            errors.append("Chưa chọn thư mục PDF (tin nhắn ghi 'hóa đơn kèm theo') — bấm 'Chọn thư mục PDF' ở Bước 1")
        if not t["phone"] and not t["search_name"]:
            errors.append(f"Không có SĐT hợp lệ ({t['raw_phone']!r}) và không có tên Zalo")
        if t.get("duplicate"):
            errors.append("Có nhiều nhóm / bạn bè trùng tên này trên Zalo")
        m = t.get("match")
        if m and m.get("warn_name"):
            p["warn"] = m["warn_name"]
        if t["phone"]:
            p["zalo"] = "theo SĐT"
        elif t["search_name"] and t.get("zalo_type", "nhom") == "nhom" and (not m or m["status"] in core.MATCH_OK) \
                and core.is_internal_group(t["search_name"], internal_kw):
            p["zalo"] = "🔒 nhóm nội bộ"
            errors.append("Nhóm nội bộ (có chữ 'Xử lý') — không gửi")
        elif m and m["status"] not in core.MATCH_OK:  # chưa ghép được nhóm Zalo
            if m["status"] == core.MATCH_SUGGEST:
                p["zalo"] = f"⚠ gợi ý: {m['zalo']}"
                errors.append(f"Chờ bạn xác nhận Zalo (gợi ý '{m['zalo']}', {m['note']}) — bấm '🔗 Ghép Zalo'")
            elif m["status"] == core.MATCH_AMBIGUOUS:
                p["zalo"] = "⚠ cần chọn"
                errors.append(f"Chờ bạn chọn nhóm / bạn bè Zalo ({m['note']}) — bấm '🔗 Ghép Zalo'")
            else:
                p["zalo"] = "❌ không thấy"
                errors.append(f"Chưa ghép được nhóm / bạn bè Zalo ({m['note']}) — bấm '🔗 Ghép Zalo'")
        elif t["search_name"] and check_groups:
            c = group_names.count(core.norm_name(t["search_name"]))
            p["zalo"] = (("⚠ " if p["warn"] else "✅ ") + t["search_name"]) if c == 1 else \
                ("❌ không thấy" if c == 0 else "⚠ trùng tên")
            if c == 1 and zalo_count[core.norm_name(t["search_name"])] > 1:
                errors.append(f"Nhiều khách cùng ghép vào nhóm '{t['search_name']}'")
            if c == 0:
                errors.append("Không có nhóm tên này trong danh sách nhóm Zalo")
            elif c > 1 and not t.get("duplicate"):
                errors.append("Có nhiều nhóm / bạn bè trùng tên này trên Zalo")
        elif t["search_name"]:
            p["zalo"] = "tìm khi gửi"
        if ttpl:
            if not extra[MONTH_FIELD] and MONTH_FIELD in fields:
                errors.append("Chưa nhập Tháng")
            if not extra[DATE_FIELD] and DATE_FIELD in fields:
                errors.append("Chưa nhập Đến ngày")
            miss = core.unknown_placeholders(ttpl, list(row.keys()))
            if miss:
                errors.append("Tin nhắn có trường không có trong Excel: " + ", ".join("{" + m + "}" for m in miss))
            empty = core.empty_placeholders(ttpl, row)
            if empty:
                errors.append("Thiếu dữ liệu: " + ", ".join(empty))
        own = []
        if has_pdf_col and t["own_pdf"]:
            own, missing = core.resolve_pdfs(t["own_pdf"], folder)
            if missing:
                errors.append("Thiếu file PDF: " + ", ".join(missing))
        elif auto_pdf and t["kind"] == "Khách hàng":  # nhóm/bạn bè tích trực tiếp: chỉ nhận PDF chung
            own = pdf_hits.get(i, [])
            if pdf_missing_manual.get(i):
                errors.append("Không còn file PDF đã chọn: " + ", ".join(pdf_missing_manual[i])
                              + " — chọn lại ở '🔗 Ghép Zalo'")
            elif not own:
                code = core.code_text(t.get("code_parsed")) if "code_parsed" in t else ""
                errors.append((f"Không tìm thấy file PDF có mã {code}" if code else
                               "Không tìm thấy file PDF trùng tên / mã") + " — chọn tay ở '🔗 Ghép Zalo'")
            elif key_count[ident(t)] > 1:
                errors.append("Có nhiều người nhận trùng tên / mã, không biết PDF của ai")
            elif any(pdf_users[f] > 1 for f in own):
                shared = [os.path.basename(f) for f in own if pdf_users[f] > 1]
                errors.append("File PDF khớp nhiều khách: " + ", ".join(shared))
        used.update(own)
        p["files"] = list(shared_pdfs) + own
        p["error"] = "; ".join(errors)
        plans.append(p)
    unmatched = [os.path.basename(f) for f in index if f not in used] if only is None else []
    return plans, unmatched


def show_preview(widget, template, row):
    """Hiện tin nhắn trong ô xem trước, tô ĐỎ các chữ thay đổi theo khách (tháng, số tiền...)."""
    widget.config(state="normal")
    widget.delete("1.0", "end")
    widget.tag_configure("var", foreground="#d0021b", font=("", 10, "bold"))
    widget.tag_configure("missing", foreground="#ffffff", background="#d0021b")
    for text, kind in core.render_segments(template or "", row):
        widget.insert("end", text if text or kind != "missing" else "[TRỐNG]", kind or ())
    widget.config(state="disabled")


class CheckTable(ttk.Frame):
    """Bảng có cột tích chọn ☐/☑, ô lọc, nút chọn tất cả / bỏ chọn."""

    def __init__(self, master, on_change, on_select=None):
        super().__init__(master)
        self.on_change = on_change
        self.on_select = on_select
        self.columns, self.rows, self.checked = [], [], set()
        self.order = None        # v1.7: thứ tự hiển thị (danh sách chỉ số dòng); None = như dữ liệu gốc
        self.row_filter = None   # v1.7: hàm lọc thêm (chỉ số dòng -> True/False)
        self.is_locked = None    # v1.11: dòng không cho tích (vd nhóm nội bộ "Xử lý")

        bar = ttk.Frame(self)
        bar.pack(fill="x", pady=(0, 6))
        ttk.Label(bar, text="🔍 Lọc:").pack(side="left")
        self.filter_var = tk.StringVar()
        self.filter_var.trace_add("write", lambda *_: self.refresh())
        ttk.Entry(bar, textvariable=self.filter_var, width=30).pack(side="left", padx=4)
        ttk.Button(bar, text="Chọn tất cả (đang hiển thị)", command=lambda: self.set_visible(True)).pack(side="left", padx=6)
        ttk.Button(bar, text="Bỏ chọn tất cả", command=self.clear).pack(side="left")

        box = ttk.Frame(self)
        box.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(box, show="headings", selectmode="browse")
        ysb = ttk.Scrollbar(box, orient="vertical", command=self.tree.yview)
        xsb = ttk.Scrollbar(box, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=ysb.set, xscrollcommand=xsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        ysb.grid(row=0, column=1, sticky="ns")
        xsb.grid(row=1, column=0, sticky="ew")
        box.rowconfigure(0, weight=1)
        box.columnconfigure(0, weight=1)
        self.tree.bind("<Button-1>", self._on_click)
        self.tree.bind("<space>", lambda e: self.tree.focus() and self.toggle(self.tree.focus()))

    def set_data(self, columns, rows, keep_checked=False, widths=None):
        same_cols = list(columns) == self.columns
        self.columns, self.rows = list(columns), [list(r) for r in rows]
        if not keep_checked:
            self.checked.clear()
        self.checked &= set(range(len(self.rows)))
        sel = self.tree.selection()
        if not same_cols:
            self.tree["columns"] = ["_chk"] + self.columns
            self.tree.heading("_chk", text="Chọn")
            self.tree.column("_chk", width=50, anchor="center", stretch=False)
            for c in self.columns:
                self.tree.heading(c, text=c)
                self.tree.column(c, width=(widths or {}).get(c, 160), anchor="w")
        self.refresh()
        if sel and self.tree.exists(sel[0]):
            self.tree.selection_set(sel[0])

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        q = core.strip_accents(self.filter_var.get())
        order = self.order if self.order is not None else range(len(self.rows))
        for idx in order:
            if idx >= len(self.rows):
                continue
            values = self.rows[idx]
            if self.row_filter and not self.row_filter(idx):
                continue
            if q and q not in core.strip_accents(" ".join(map(str, values))):
                continue
            mark = CHECK if idx in self.checked else UNCHECK
            self.tree.insert("", "end", iid=str(idx), values=[mark] + values)
        self.on_change()

    def toggle(self, iid):
        idx = int(iid)
        if self.is_locked and self.is_locked(idx) and idx not in self.checked:
            return
        if idx in self.checked:
            self.checked.discard(idx)
        else:
            self.checked.add(idx)
        self.tree.set(iid, "_chk", CHECK if idx in self.checked else UNCHECK)
        self.on_change()

    def _on_click(self, event):
        if self.tree.identify_region(event.x, event.y) != "cell":
            return
        iid = self.tree.identify_row(event.y)
        if not iid:
            return
        self.tree.focus(iid)
        # bấm vào cột "Chọn" (hoặc bảng không có xem trước) -> tích/bỏ tích; cột khác -> xem trước
        if self.tree.identify_column(event.x) == "#1" or not self.on_select:
            self.toggle(iid)
        if self.on_select:
            self.tree.selection_set(iid)
            self.on_select(int(iid))
            return "break" if self.tree.identify_column(event.x) == "#1" else None

    def set_visible(self, value):
        for iid in self.tree.get_children():
            if value and self.is_locked and self.is_locked(int(iid)):
                continue
            (self.checked.add if value else self.checked.discard)(int(iid))
            self.tree.set(iid, "_chk", CHECK if value else UNCHECK)
        self.on_change()

    def clear(self):
        self.checked.clear()
        self.refresh()


class ZaloListTab(ttk.Frame):
    """v1.8: Thẻ danh sách trên Zalo (nhóm hoặc bạn bè): lấy danh sách, tích chọn, sắp xếp, hiển thị,
    lọc theo chữ cái đầu, menu chuột phải, xuất Excel."""

    def __init__(self, nb, app, kind):
        super().__init__(nb, padding=8)
        self.app, self.kind, self.cfg = app, kind, LIST_KINDS[kind]
        self.items, self.updated = [], ""
        st = core.load_settings()
        self.sort_var = tk.StringVar(value=st.get(f"{kind}_sort", st.get("group_sort", "") if kind == "nhom" else ""))
        old_show = st.get("group_show", "all") if kind == "nhom" else "all"
        self.show_var = tk.StringVar(value=st.get(f"{kind}_show", old_show))
        self.letter_var = tk.StringVar(value="")

        self.locked = (kind == "ban" and not lic.is_pro())  # thẻ Bạn bè: chỉ bản PRO
        if self.locked:
            self._build_locked()
            return
        top = ttk.Frame(self)
        top.pack(fill="x")
        self.fetch_btn = ttk.Button(top, text=self.cfg["fetch"], style="Accent.TButton", command=self.start_fetch)
        self.fetch_btn.pack(side="left")
        ttk.Button(top, text="📤 Xuất ra Excel", command=self.export).pack(side="left", padx=6)
        self.menu_btn = ttk.Button(top, text="☰ Sắp xếp / Lọc", command=self.show_menu_at_button)
        self.menu_btn.pack(side="left")
        self.status = ttk.Label(top, text=f"Chưa có danh sách {self.cfg['unit']}")
        self.status.pack(side="left", padx=10)

        # v1.9: không còn 3 hàng Sắp xếp / Hiển thị / Chữ đầu -> dùng menu chuột phải hoặc nút ☰
        vr = ttk.Frame(self)
        vr.pack(fill="x", pady=(6, 0))
        self.view_label = ttk.Label(vr, text="", foreground="#0050C8", font=("", 9, "bold"))
        self.view_label.pack(side="left")
        self.clear_btn = ttk.Button(vr, text="✖ Bỏ lọc", command=self.clear_view)
        ttk.Label(self, text=self.cfg["hint"] + "  Bấm CHUỘT PHẢI vào bảng (hoặc nút ☰) để sắp xếp / lọc.",
                  style="Muted.TLabel", wraplength=1100).pack(anchor="w", pady=(4, 0))
        self.table = CheckTable(self, app.update_count)
        self.table.pack(fill="both", expand=True, pady=(6, 0))
        self.table.row_filter = self.visible
        if kind == "nhom":
            self.table.is_locked = lambda i: i < len(self.items) and core.is_internal_group(
                self.items[i]["name"], self.app.internal_kw)
        self.menu = self._build_menu()
        self.table.tree.bind("<Button-3>", lambda e: self.menu.tk_popup(e.x_root, e.y_root))
        self.update_view_label()

    PRO_SHOWS = ("matched", "unmatched", "checked")

    def _build_locked(self):
        """Bản Standard: thẻ Bạn bè bị khóa, giới thiệu chức năng và nút nâng cấp."""
        self.table = CheckTable(ttk.Frame(self), self.app.update_count)  # bảng ẩn để mã khác dùng chung
        box = ttk.Frame(self, padding=30)
        box.pack(expand=True)
        ttk.Label(box, text="🔒 Thẻ Bạn bè Zalo chỉ có ở bản PRO", font=("", 14, "bold")).pack(pady=(0, 10))
        for line in ("• Lấy danh sách bạn bè từ Zalo, sắp xếp, lọc theo chữ cái đầu, xuất Excel",
                     "• Gửi thông báo chung cho bạn bè (chat riêng)",
                     "• Ghép khách hàng trong Excel với bạn bè Zalo để gửi đề nghị thanh toán kèm PDF",
                     "• Tự phát hiện bạn bè trùng tên để tránh gửi nhầm"):
            ttk.Label(box, text=line, font=("", 10)).pack(anchor="w")
        ttk.Button(box, text="⭐ Nâng cấp PRO", style="Pro.TButton",
                   command=lambda: UpgradeWindow(self.app)).pack(pady=16)
        self.status = ttk.Label(box, text="")
        self.fetch_btn = ttk.Button(box)

    def _build_menu(self):
        pro = lic.is_pro()
        m = tk.Menu(self, tearoff=0)
        ms = tk.Menu(m, tearoff=0)
        for val, txt in self.cfg["sorts"]:
            ms.add_checkbutton(label=txt, variable=self.sort_var, onvalue=val, offvalue="", command=self.apply_view)
        m.add_cascade(label="Sắp xếp (chọn 1)", menu=ms)
        mh = tk.Menu(m, tearoff=0)
        for val, txt in self.cfg["shows"]:
            if val in self.PRO_SHOWS and not pro:
                mh.add_command(label="🔒 " + txt + "  (PRO)", command=self.pro_prompt)
            else:
                mh.add_checkbutton(label=txt, variable=self.show_var, onvalue=val, offvalue="all",
                                   command=self.apply_view)
        m.add_cascade(label="Hiển thị", menu=mh)
        if pro:
            ml = tk.Menu(m, tearoff=0)
            for val, txt in [("", "Tất cả")] + [(l.lower(), l) for l in VN_LETTERS]:
                ml.add_radiobutton(label=txt, variable=self.letter_var, value=val, command=self.apply_view,
                                   columnbreak=(txt in ("K", "S")))
            m.add_cascade(label="Chữ đầu", menu=ml)
        else:
            m.add_command(label="🔒 Chữ đầu  (PRO)", command=self.pro_prompt)
        m.add_separator()
        m.add_command(label="✖ Bỏ sắp xếp & lọc", command=self.clear_view)
        m.add_command(label="📤 Xuất danh sách đang hiển thị ra Excel", command=self.export)
        return m

    def show_menu_at_button(self):
        b = self.menu_btn
        self.menu.tk_popup(b.winfo_rootx(), b.winfo_rooty() + b.winfo_height())

    def pro_prompt(self):
        if messagebox.askyesno("Chức năng PRO", "Chức năng này thuộc bản PRO.\nMở cửa sổ Nâng cấp PRO?"):
            UpgradeWindow(self.app)

    def clear_view(self):
        self.sort_var.set("")
        self.show_var.set("all")
        self.letter_var.set("")
        self.apply_view()

    def update_view_label(self):
        parts = []
        sorts, shows = dict(self.cfg["sorts"]), dict(self.cfg["shows"])
        if self.sort_var.get() in sorts:
            parts.append("Sắp xếp: " + sorts[self.sort_var.get()].split(". ", 1)[-1])
        if self.show_var.get() != "all" and self.show_var.get() in shows:
            parts.append(shows[self.show_var.get()].split(". ", 1)[-1])
        if self.letter_var.get():
            parts.append(f'Chữ đầu "{self.letter_var.get().upper()}"')
        if parts:
            self.view_label.config(text="Đang xem:  " + "  ·  ".join(parts))
            self.clear_btn.pack(side="left", padx=10)
        else:
            self.view_label.config(text="")
            self.clear_btn.pack_forget()

    # ----- dữ liệu -----
    @property
    def path(self):
        return datadir.path(self.cfg["file"])

    def load_saved(self):
        if self.locked:
            return
        try:
            with open(self.path, encoding="utf-8") as f:
                data = json.load(f)
            self.set_items(data.get("groups" if self.kind == "nhom" else "friends", []), data.get("updated", ""),
                           refresh=False)
        except Exception:
            pass

    def set_items(self, items, updated, refresh=True):
        self.items, self.updated = items, updated
        dup = sum(1 for it in items if int(it.get("same_name", 1)) > 1)
        self.status.config(text=f"{len(items)} {self.cfg['unit']} — cập nhật lúc {updated}"
                                + (f"   ⚠ {dup} tên bị trùng (không gửi được)" if dup else ""))
        self.update_table(keep_checked=False)
        if refresh:
            self.app.refresh_info()

    def rows(self):
        mc = self.app.matched_customers()
        last = core.last_sent_map()
        out = []
        for it in self.items:
            k = core.norm_name(it["name"])
            sent = last.get(k)
            matched = "; ".join(mc.get(k, []))
            when = sent.strftime("%d/%m/%Y %H:%M") if sent else ""
            if self.kind == "nhom":
                if core.is_internal_group(it["name"], self.app.internal_kw):
                    matched = "🔒 Nhóm nội bộ (Xử lý) — không gửi"
                out.append([it["name"], it.get("members", ""), core.dropbox_code(it["name"]), matched, when])
            else:
                same = int(it.get("same_name", 1))
                out.append([it["name"], core.dropbox_code(it["name"]), f"⚠ {same} người" if same > 1 else "",
                            matched, when])
        return out

    def columns(self):
        if self.kind == "nhom":
            return ["Tên nhóm", "Thành viên", "Mã Dropbox", "Khách hàng đã ghép (Excel)", "Gửi gần nhất"]
        return ["Tên bạn bè", "Mã Dropbox", "Trùng tên", "Khách hàng đã ghép (Excel)", "Gửi gần nhất"]

    def update_table(self, keep_checked=True):
        self._rows = self.rows()
        self.table.order = self.order()
        w = {c: 120 for c in self.columns()}
        w.update({self.cfg["name_col"]: 360, "Khách hàng đã ghép (Excel)": 330, "Gửi gần nhất": 130})
        self.table.set_data(self.columns(), self._rows, keep_checked=keep_checked, widths=w)

    def order(self):
        idx = list(range(len(self.items)))
        name = lambda i: self.items[i]["name"]
        mode = self.sort_var.get()
        rows = getattr(self, "_rows", None) or self.rows()
        if mode == "num":
            idx.sort(key=lambda i: (core.leading_number(name(i)) is None, core.leading_number(name(i)) or 0,
                                    core.vn_sort_key(name(i))))
        elif mode == "mem":
            idx.sort(key=lambda i: (-core.member_count(self.items[i].get("members")), core.vn_sort_key(name(i))))
        elif mode == "az":
            idx.sort(key=lambda i: core.vn_sort_key(name(i)))
        elif mode == "za":
            idx.sort(key=lambda i: core.vn_sort_key(name(i)), reverse=True)
        elif mode == "matched":
            idx.sort(key=lambda i: (not rows[i][3], core.vn_sort_key(name(i))))
        elif mode == "recent":
            last = core.last_sent_map()
            idx.sort(key=lambda i: (-(last[core.norm_name(name(i))].timestamp())
                                    if core.norm_name(name(i)) in last else float("inf"), core.vn_sort_key(name(i))))
        return idx

    def visible(self, i):
        if i >= len(self.items):
            return False
        name = self.items[i]["name"]
        show = self.show_var.get()
        if show in self.PRO_SHOWS and not lic.is_pro():
            show = "all"
        rows = getattr(self, "_rows", None)
        matched = bool(rows[i][3]) if rows and i < len(rows) else False
        if show == "num" and core.leading_number(name) is None:
            return False
        if show == "matched" and not matched:
            return False
        if show == "unmatched" and matched:
            return False
        if show == "checked" and i not in self.table.checked:
            return False
        letter = self.letter_var.get() if lic.is_pro() else ""
        if letter and core.first_letter(name) != letter:
            return False
        return True

    def apply_view(self):
        if self.locked:
            return
        core.save_settings(**{f"{self.kind}_sort": self.sort_var.get(), f"{self.kind}_show": self.show_var.get()})
        self.table.order = self.order()
        self.table.refresh()
        self.update_view_label()

    # ----- lấy danh sách từ Zalo -----
    def start_fetch(self):
        if self.app.busy.is_set():
            messagebox.showinfo("Đang bận", "Ứng dụng đang dùng Zalo (lấy danh sách hoặc gửi tin). Hãy đợi xong.")
            return
        self.app.busy.set()
        self.fetch_btn.config(state="disabled")
        self.status.config(text="Đang mở Zalo Web...")
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self):
        q, kind, sender = self.app.q, self.kind, None
        try:
            from zalo_web import ZaloWebSender
            sender = ZaloWebSender(log=lambda m: q.put(("list_status", (kind, m))))
            sender.start()
            sender.wait_for_login()
            items = sender.fetch_groups() if kind == "nhom" else sender.fetch_friends()
            updated = f"{datetime.datetime.now():%d/%m/%Y %H:%M}"
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump({"updated": updated, ("groups" if kind == "nhom" else "friends"): items}, f,
                          ensure_ascii=False, indent=1)
            q.put(("list_done", (kind, items, updated)))
        except Exception as e:
            q.put(("list_error", (kind, (str(e) or type(e).__name__).splitlines()[0])))
        finally:
            try:
                if sender:
                    sender.close()
            except Exception:
                pass
            self.app.busy.clear()

    # ----- xuất Excel -----
    def export(self):
        if not self.items:
            messagebox.showinfo("Chưa có dữ liệu", f"Hãy bấm '{self.cfg['fetch'][2:]}' trước.")
            return
        path = filedialog.asksaveasfilename(
            title=f"Lưu danh sách {self.cfg['unit']} Zalo", defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")],
            initialfile=f"{self.cfg['export']}_{datetime.datetime.now():%Y%m%d_%H%M}.xlsx")
        if not path:
            return
        visible = [int(i) for i in self.table.tree.get_children()]  # đúng thứ tự & bộ lọc đang hiển thị
        rows = self.rows()
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Alignment, Font, PatternFill
            wb = Workbook()
            ws = wb.active
            ws.title = self.cfg["sheet"]
            if self.kind == "nhom":
                ws.append(["STT", "Tên nhóm Zalo", "Số thành viên", "Mã Dropbox", "Có số đầu tên",
                           "Khách hàng đã ghép (Excel)", "Gửi gần nhất"])
                for n, i in enumerate(visible, 1):
                    name, members, code, matched, when = rows[i]
                    ws.append([n, name, core.member_count(members), code or None,
                               "Có" if core.leading_number(name) is not None else "Không", matched or None, when or None])
                widths = (6, 48, 14, 14, 14, 44, 18)
            else:
                ws.append(["STT", "Tên bạn bè Zalo", "Mã Dropbox", "Có số đầu tên", "Số người trùng tên",
                           "Khách hàng đã ghép (Excel)", "Gửi gần nhất"])
                for n, i in enumerate(visible, 1):
                    name, code, _same, matched, when = rows[i]
                    ws.append([n, name, code or None, "Có" if core.leading_number(name) is not None else "Không",
                               int(self.items[i].get("same_name", 1)), matched or None, when or None])
                widths = (6, 40, 14, 14, 18, 44, 18)
            for c in ws[1]:
                c.font = Font(bold=True, color="FFFFFF")
                c.fill = PatternFill("solid", fgColor="0068FF")
                c.alignment = Alignment(horizontal="center", vertical="center")
            for col, w in zip("ABCDEFG", widths):
                ws.column_dimensions[col].width = w
            ws.freeze_panes = "A2"
            ws.auto_filter.ref = ws.dimensions
            wb.save(path)
        except PermissionError:
            messagebox.showerror("Không lưu được", "File đang mở trong Excel. Hãy đóng file rồi thử lại.")
            return
        except Exception as e:
            messagebox.showerror("Lỗi xuất Excel", str(e))
            return
        if messagebox.askyesno("Đã xuất", f"Đã lưu {len(visible)} {self.cfg['unit']} vào:\n{path}\n\nMở file ngay?"):
            try:
                os.startfile(path)  # Windows
            except Exception:
                pass


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(app_title())
        self.geometry(f"1180x{min(780, self.winfo_screenheight() - 80)}+10+5")
        setup_style(self)
        set_icon(self)
        self.df = None
        self.busy = threading.Event()  # đang dùng Chrome (lấy nhóm / gửi tin)
        self.q = queue.Queue()
        st = core.load_settings()
        self.month = tk.StringVar(value=core.previous_month())          # dùng chung Bước 1 & 2
        self.month.trace_add("write", lambda *_: self.schedule_refresh())
        self.pdf_dir = tk.StringVar(value=st.get("pdf_dir", ""))         # v1.4: chọn ở Bước 1
        self.check_groups = tk.BooleanVar(value=True)
        self.step1_plans = []
        self.buffer = None
        self.gmap = core.GroupMap()  # v1.7: ghi nhớ ghép nhóm
        self.pdfmap = core.PdfMap()  # v1.11: PDF chọn tay theo Mã khách hàng
        self.file_meta = {}
        self.den_ngay = tk.StringVar(value=f"{datetime.date.today():%d/%m/%Y}")
        self.den_ngay.trace_add("write", lambda *_: self.schedule_refresh())
        self.show_zero = tk.BooleanVar(value=False)
        self.internal_kw = [core.strip_accents(k) for k in st.get("internal_keywords", ["xử lý"])]
        self.tstore = core.TemplateStore(DEFAULT_TEMPLATE, "AONE",
                                         builtins={CONG_NO_NAME: CONG_NO_TEMPLATE})  # v1.8 kho mẫu; v1.11 mẫu Công nợ
        self._refresh_job = None
        self._build()
        self._load_saved_groups()
        self.after(150, self._poll)
        # v1.3: tự mở lại file Excel lần trước và tích chọn tất cả
        last = core.load_settings().get("excel_path")
        if last and os.path.isfile(last):
            self.after(200, lambda: self.load_file(last, auto=True))
        self.after(1500, self._mark_started)
        self.after(3000, lambda: self.check_update(silent=True))

    # ================= v1.10: CẬP NHẬT QUA GITHUB =================
    def _mark_started(self):
        """Báo cho trình cập nhật biết bản này đã mở thành công (nếu không, nó sẽ quay về bản cũ)."""
        try:
            with open(datadir.path("khoi_dong_ok.json"), "w", encoding="utf-8") as f:
                json.dump({"version": APP_VERSION, "pid": os.getpid(),
                           "at": f"{datetime.datetime.now():%d/%m/%Y %H:%M:%S}"}, f)
        except Exception:
            pass

    def check_update(self, silent=True, parent=None):
        """silent=True: tự kiểm tra lúc mở (tối đa 1 lần/ngày, lỗi mạng thì im lặng)."""
        today = f"{datetime.date.today():%Y-%m-%d}"
        if silent and core.load_settings().get("last_update_check") == today:
            cached = core.load_settings().get("update_cache")
            if cached:
                self.show_update_bar(cached)
            return

        def work():
            try:
                import updater
                data = updater.check()
                core.save_settings(last_update_check=today, update_cache=data)
                self.q.put(("update", ("", data, silent, parent, None)))
            except Exception as e:
                self.q.put(("update", ("", None, silent, parent, str(e).splitlines()[0] if str(e) else type(e).__name__)))
        threading.Thread(target=work, daemon=True).start()

    def _on_update_result(self, data, silent, parent, err):
        if data:
            self.show_update_bar(data)
            if data.get("required"):
                self.force_update(data)
            elif not silent:
                messagebox.showinfo("Có bản mới", f"Đã có phiên bản v{data['version']}. "
                                    "Bấm 'Cập nhật ngay' ở thanh thông báo phía trên.", parent=parent or self)
        elif not silent:
            if err:
                messagebox.showwarning("Không kiểm tra được", "Không kiểm tra được bản mới (mất mạng hoặc chưa có "
                                       f"bản phát hành).\nChi tiết: {err}", parent=parent or self)
            else:
                messagebox.showinfo("Đã là bản mới nhất", f"Bạn đang dùng bản mới nhất v{APP_VERSION}.",
                                    parent=parent or self)

    def show_update_bar(self, data):
        import updater
        if not data or not updater.is_newer(data.get("version")):
            return
        bar = self.update_bar
        for w in bar.winfo_children():
            w.destroy()
        req = bool(data.get("required"))
        bg = "#FDECEA" if req else "#FFF4CE"
        bar.configure(bg=bg, highlightbackground="#E0B400" if not req else "#C0392B", highlightthickness=1)
        notes = (data.get("notes") or "").strip().splitlines()
        tk.Label(bar, bg=bg, font=("", 10, "bold"), fg="#C0392B" if req else "#7A5A00",
                 text=("⛔ BẮT BUỘC cập nhật" if req else "🔔 Có phiên bản mới") + f" v{data['version']}"
                      + (f" — {notes[0][:70]}" if notes else "")).pack(side="left", padx=10, pady=6)
        tk.Button(bar, text="⬇ Cập nhật ngay", bg="#0068FF", fg="#FFFFFF", activebackground="#0050C8",
                  relief="flat", font=("", 9, "bold"), padx=10, cursor="hand2",
                  command=lambda: self.start_update(data)).pack(side="right", padx=6, pady=4)
        tk.Button(bar, text="Xem có gì mới", relief="flat", bg="#FFFFFF", padx=8, cursor="hand2",
                  command=lambda: messagebox.showinfo(f"Có gì mới trong v{data['version']}",
                                                      data.get("notes") or "(không có ghi chú)", parent=self)
                  ).pack(side="right", padx=2)
        if not req:
            tk.Button(bar, text="Để sau", relief="flat", bg=bg, padx=8, cursor="hand2",
                      command=bar.pack_forget).pack(side="right", padx=2)
        if not bar.winfo_ismapped():
            bar.pack(fill="x", padx=10, pady=(6, 0), before=self._head)

    def force_update(self, data):
        if messagebox.askyesno("Bắt buộc cập nhật", f"Bản v{data['version']} là bản BẮT BUỘC (sửa lỗi quan trọng).\n"
                               "Cập nhật ngay bây giờ?\n\n(Chọn 'No' để đóng ứng dụng.)", parent=self):
            self.start_update(data)
        else:
            self.destroy()

    def start_update(self, data):
        if self.busy.is_set():
            messagebox.showinfo("Đang bận", "Ứng dụng đang gửi tin / lấy danh sách. Hãy đợi xong rồi cập nhật.",
                                parent=self)
            return
        UpdateWindow(self, data)

    # ================= BƯỚC 1 =================
    def _build(self):
        bottom = ttk.Frame(self, padding=8)
        bottom.pack(side="bottom", fill="x")
        self.count_label = ttk.Label(bottom, text="Đã chọn: 0 khách hàng, 0 nhóm", font=("", 10, "bold"))
        self.count_label.pack(side="left")
        ttk.Button(bottom, text="Tiếp tục ➜ Bước 2: Soạn tin nhắn", style="Accent.TButton",
                   command=self.open_step2).pack(side="right")
        self.update_bar = tk.Frame(self)  # v1.10: thanh "Có phiên bản mới" (ẩn khi không có)
        head = ttk.Frame(self)
        head.pack(fill="x", padx=10, pady=(8, 2))
        self._head = head
        ttk.Label(head, text="Bước 1: Tích chọn khách hàng, nhóm hoặc bạn bè Zalo cần gửi",
                  font=("", 11, "bold")).pack(side="left")
        ttk.Button(head, text="ℹ Giới thiệu & Hỗ trợ", style="Info.TButton",
                   command=lambda: AboutWindow(self)).pack(side="right")
        self.lic_box = ttk.Frame(head)  # nút "Nâng cấp PRO" (Standard) hoặc nhãn mờ "✅ PRO — ..." (PRO)
        self.lic_box.pack(side="right", padx=8)
        self.apply_license_ui()
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=8, pady=4)

        # --- Thẻ khách hàng ---
        tab1 = ttk.Frame(self.nb, padding=8)
        self.nb.add(tab1, text="👤 Khách hàng (file Excel/CSV)")
        top = ttk.Frame(tab1)
        top.pack(fill="x")
        ttk.Button(top, text="📂 Chọn file Excel", style="Accent.TButton", command=self.open_file).pack(side="left")
        self.file_label = ttk.Label(top, text="Chưa chọn file", width=30)
        self.file_label.pack(side="left", padx=(6, 16))
        ttk.Button(top, text="📁 Chọn thư mục PDF", style="Accent.TButton", command=self.pick_pdf_dir).pack(side="left")
        ttk.Entry(top, textvariable=self.month, width=9).pack(side="right")   # bên phải cùng
        ttk.Label(top, text="Tháng:").pack(side="right", padx=(12, 2))
        self.match_btn = ttk.Button(top, text="🔗 Ghép Zalo", command=self.open_match_window)
        self.match_btn.pack(side="right", padx=(12, 0))
        self.match_label = ttk.Label(top, text="", foreground="#c0392b", font=("", 9, "bold"))
        self.match_label.pack(side="right")
        self.pdf_label = ttk.Label(top, text=self.pdf_dir.get() or "Chưa chọn thư mục PDF", foreground="#0050c8")
        self.pdf_label.pack(side="left", padx=6)
        self.pdf_dir.trace_add("write", lambda *_: (self.pdf_label.config(
            text=self.pdf_dir.get() or "Chưa chọn thư mục PDF"), core.save_settings(pdf_dir=self.pdf_dir.get())))

        cfg = ttk.Frame(tab1)
        cfg.pack(fill="x", pady=6)
        self.col_boxes = {}
        for key, label in (("phone", "Cột SĐT:"), ("name", "Cột tên khách:"),
                           ("zalo", "Cột tên Zalo / tên nhóm:"), ("pdf", "Cột file PDF riêng:")):
            ttk.Label(cfg, text=label).pack(side="left")
            cb = ttk.Combobox(cfg, state="readonly", width=18)
            cb.pack(side="left", padx=(3, 12))
            cb.bind("<<ComboboxSelected>>", lambda e: self.refresh_info())
            self.col_boxes[key] = cb
        # v1.11: file công nợ của kế toán — chọn sheet, cột Mã KH / Số Dropbox / Số tiền
        cfg2 = ttk.Frame(tab1)
        cfg2.pack(fill="x", pady=(0, 4))
        ttk.Label(cfg2, text="Sheet:").pack(side="left")
        self.sheet_cb = ttk.Combobox(cfg2, state="readonly", width=22)
        self.sheet_cb.pack(side="left", padx=(3, 12))
        self.sheet_cb.bind("<<ComboboxSelected>>", lambda e: self.excel_path and self.load_file(
            self.excel_path, sheet=self.sheet_cb.get()))
        for key, label in (("key", "Cột mã KH:"), ("code", "Cột Số Dropbox:"), ("amount", "Cột số tiền:")):
            ttk.Label(cfg2, text=label).pack(side="left")
            cb = ttk.Combobox(cfg2, state="readonly", width=18)
            cb.pack(side="left", padx=(3, 12))
            cb.bind("<<ComboboxSelected>>", lambda e: self.refresh_info())
            self.col_boxes[key] = cb
        ttk.Checkbutton(cfg2, text="Hiện cả khách đã hết nợ", variable=self.show_zero,
                        command=lambda: self.cust_table.refresh()).pack(side="left", padx=(4, 10))
        ttk.Button(cfg2, text="📤 DS cần xử lý", command=self.export_issues).pack(side="right")
        self.phone_warn = ttk.Label(tab1, text="", foreground="#c0392b", font=("", 9, "bold"))
        self.hint1 = ttk.Label(tab1, text="Bấm ô ☐ để tích / bỏ tích. Bấm vào tên khách để xem trước tin nhắn. "
                            "Có cột Số Dropbox thì ghép nhóm Zalo theo mã; nhóm có chữ 'Xử lý' là nội bộ, không gửi.",
                               foreground="gray")
        self.hint1.pack(anchor="w")
        pane = ttk.PanedWindow(tab1, orient="vertical")
        pane.pack(fill="both", expand=True, pady=(6, 0))
        self.cust_table = CheckTable(pane, self.update_count, on_select=self.preview_row)
        self.cust_table.tree.bind("<Button-3>", self.cust_menu)  # v1.11: chọn mẫu tin riêng cho khách
        pane.add(self.cust_table, weight=3)
        pvf = ttk.Frame(pane)
        pane.add(pvf, weight=2)
        pvh = ttk.Frame(pvf)
        pvh.pack(fill="x", pady=(4, 2))
        ttk.Label(pvh, text="Xem trước tin nhắn:", font=("", 10, "bold")).pack(side="left")
        ttk.Button(pvh, text="↺ Đặt lại: Chưa gửi", command=self.reset_selected).pack(side="right")
        self.preview_info = ttk.Label(pvh, text="(bấm vào tên một khách hàng trong bảng)", foreground="gray")
        self.preview_info.pack(side="left", padx=8)
        self.preview_text = tk.Text(pvf, height=12, wrap="word", font=("", 10), background="#f7f7f7",
                                    state="disabled")
        self.preview_text.pack(fill="both", expand=True)

        # --- v1.8: Thẻ Nhóm Zalo + Thẻ Bạn bè Zalo (dùng chung 1 khối giao diện) ---
        self.group_tab = ZaloListTab(self.nb, self, "nhom")
        self.nb.add(self.group_tab, text="👥 Nhóm Zalo")
        self.friend_tab = ZaloListTab(self.nb, self, "ban")
        self.nb.add(self.friend_tab, text="🧑‍🤝‍🧑 Bạn bè Zalo")
        self.group_table = self.group_tab.table
        self.friend_table = self.friend_tab.table

    def open_file(self):
        path = filedialog.askopenfilename(
            title="Chọn file dữ liệu khách hàng",
            filetypes=[("Excel / CSV", "*.xlsx *.xls *.csv"), ("Tất cả", "*.*")])
        if path:
            self.load_file(path)

    def load_file(self, path, auto=False, sheet=None):
        try:
            df, meta = core.load_table(path, sheet or (core.load_settings().get("excel_sheet")
                                                        if core.load_settings().get("excel_path") == path else None))
        except Exception as e:
            messagebox.showerror("Lỗi đọc file", str(e))
            return
        if df.empty:
            messagebox.showwarning("File trống", "Không có dòng dữ liệu nào (hoặc không tìm thấy dòng tên cột).")
            return
        self.df, self.file_meta = df, meta
        self.sheet_cb["values"] = meta.get("sheets", [])
        self.sheet_cb.set(meta.get("sheet", ""))
        if meta.get("den_ngay"):
            self.den_ngay.set(meta["den_ngay"])
        cols = list(df.columns)
        g = {"phone": core.guess_phone_column(cols), "key": core.guess_key_column(cols),
             "code": core.guess_code_column(cols), "amount": core.guess_amount_column(cols)}
        g["zalo"] = core.guess_zalo_name_column([c for c in cols if c not in (g["phone"], g["code"])])
        g["name"] = core.guess_name_column(cols, exclude=[c for c in (g["zalo"], g["key"]) if c])
        g["pdf"] = core.guess_pdf_column([c for c in cols if c not in g.values() and not core.is_money_column(c)])
        if not g["phone"] and not g["zalo"] and not g["code"] and g["name"]:
            g["zalo"] = g["name"]  # không có SĐT / Số Dropbox: tìm nhóm Zalo theo tên khách
        saved = core.load_settings()
        if saved.get("excel_path") == path:  # khôi phục cột đã chọn lần trước
            for k, v in saved.get("columns", {}).items():
                if k in g and (v in cols or v is None):
                    g[k] = v
        for key in ("phone", "name", "zalo", "pdf", "key", "code", "amount"):
            optional = key != "name"
            cb = self.col_boxes[key]
            cb["values"] = ([NONE] if optional else []) + cols
            cb.set(g.get(key) or (NONE if optional else cols[0]))
        n_debt = sum(1 for i in range(len(df)) if self._cust_visible(i))
        self.file_label.config(text=f"{os.path.basename(path)} — {len(df)} dòng"
                                    + (f", {n_debt} còn nợ" if self.col("amount") else "")
                                    + (" (mở lại lần trước)" if auto else ""))
        self.excel_path = path
        self.cust_table.row_filter = self._cust_visible
        self.refresh_info(keep_checked=False)
        self.cust_table.set_visible(True)  # tích chọn các dòng đang hiện (file công nợ: chỉ khách còn nợ)
        kids = self.cust_table.tree.get_children()
        if kids:
            self.cust_table.tree.selection_set(kids[0])
            self.preview_row(int(kids[0]))
        core.save_settings(excel_path=path, excel_sheet=meta.get("sheet"))

    def cust_menu(self, event):
        """v1.11 (PRO): chuột phải vào khách -> chọn mẫu tin riêng cho khách này (nhớ theo Mã KH)."""
        iid = self.cust_table.tree.identify_row(event.y)
        if not iid or int(iid) >= len(self.step1_plans):
            return
        self.cust_table.tree.selection_set(iid)
        self.preview_row(int(iid))
        t = self.step1_plans[int(iid)]["t"]
        m = tk.Menu(self, tearoff=0)
        if not lic.is_pro():
            m.add_command(label="🔒 Chọn mẫu tin riêng cho khách này  (PRO)", command=lambda: UpgradeWindow(self))
        elif not t.get("cust_key"):
            m.add_command(label="Cần chọn 'Cột mã KH' để chọn mẫu tin riêng cho từng khách", state="disabled")
        else:
            m.add_command(label=f"Mẫu tin cho: {t['label'] or t['cust_key']}", state="disabled")
            cur = tk.StringVar(value=t.get("tpl_name") or "")
            m.add_radiobutton(label="(Dùng mẫu chung của đợt gửi)", variable=cur, value="",
                              command=lambda: self.set_cust_tpl(t["cust_key"], ""))
            for name in self.tstore.names():
                m.add_radiobutton(label=name, variable=cur, value=name,
                                  command=lambda n=name: self.set_cust_tpl(t["cust_key"], n))
            m._var = cur
        m.tk_popup(event.x_root, event.y_root)

    def set_cust_tpl(self, key, name):
        d = core.load_settings().get("cust_tpl", {})
        if name:
            d[core.norm_name(key)] = name
        else:
            d.pop(core.norm_name(key), None)
        core.save_settings(cust_tpl=d)
        self.refresh_info()

    def export_issues(self):
        """v1.11: xuất danh sách khách còn nợ nhưng chưa gửi được / cần kiểm tra -> Excel cho kế toán."""
        if self.df is None or not self.step1_plans:
            messagebox.showinfo("Chưa có dữ liệu", "Hãy chọn file Excel trước.")
            return
        rows = []
        for i, p in enumerate(self.step1_plans):
            if not self._cust_visible(i) or not (p["error"] or p["warn"]):
                continue
            t = p["t"]
            rows.append([t.get("cust_key", ""), t["label"], t.get("code_raw", ""),
                         core.parse_amount(t["row"].get(AMOUNT_FIELD, "")) or None,
                         (t.get("match") or {}).get("zalo") or "", p["error"] or ("⚠ " + p["warn"])])
        if not rows:
            messagebox.showinfo("Không có", "Không có khách nào cần xử lý. 👍")
            return
        path = filedialog.asksaveasfilename(title="Lưu danh sách cần xử lý", defaultextension=".xlsx",
                                            filetypes=[("Excel", "*.xlsx")],
                                            initialfile=f"DanhSachCanXuLy_{datetime.datetime.now():%Y%m%d_%H%M}.xlsx")
        if not path:
            return
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill
            wb = Workbook()
            ws = wb.active
            ws.title = "Cần xử lý"
            ws.append(["Mã khách hàng", "Tên khách hàng", "Số Dropbox", "Số tiền", "Nhóm Zalo (gợi ý)", "Vấn đề"])
            for r in rows:
                ws.append(r)
            for c in ws[1]:
                c.font = Font(bold=True, color="FFFFFF")
                c.fill = PatternFill("solid", fgColor="C0392B")
            for col, w in zip("ABCDEF", (16, 46, 14, 14, 40, 90)):
                ws.column_dimensions[col].width = w
            for r in ws.iter_rows(min_row=2, min_col=4, max_col=4):
                r[0].number_format = "#,##0"
            ws.freeze_panes = "A2"
            ws.auto_filter.ref = ws.dimensions
            wb.save(path)
        except PermissionError:
            messagebox.showerror("Không lưu được", "File đang mở trong Excel. Hãy đóng file rồi thử lại.")
            return
        if messagebox.askyesno("Đã xuất", f"Đã lưu {len(rows)} khách cần xử lý vào:\n{path}\n\nMở file ngay?"):
            try:
                os.startfile(path)
            except Exception:
                pass

    def _cust_visible(self, i):
        """v1.11: có cột số tiền thì mặc định chỉ hiện khách còn nợ (> 0)."""
        ac = self.col("amount") if hasattr(self, "col_boxes") else None
        if self.df is None or not ac or self.show_zero.get() or i >= len(self.df):
            return True
        return (core.parse_amount(self.df.iloc[i][ac]) or 0) > 0

    # --- v1.4: thư mục PDF, bảng thông tin & xem trước ở Bước 1 ---
    def pick_pdf_dir(self):
        d = filedialog.askdirectory(title="Chọn thư mục chứa file PDF của khách hàng",
                                    initialdir=self.pdf_dir.get() or None)
        if d:
            d = os.path.normpath(d)
            self.pdf_dir.set(d)
            self.pdf_label.config(text=d)
            core.save_settings(pdf_dir=d)
            self.refresh_info()

    def apply_license_ui(self):
        """v1.9.1: cập nhật NGAY tiêu đề, icon, nút/nhãn bản quyền (không cần khởi động lại)."""
        self.title(app_title())
        set_icon(self)
        for w in self.lic_box.winfo_children():
            w.destroy()
        L = lic.get()
        if not L.is_pro:
            ttk.Button(self.lic_box, text="⭐ Nâng cấp PRO", style="Pro.TButton",
                       command=lambda: UpgradeWindow(self)).pack()
            return
        exp = L.info.get("expires")
        days = (exp - datetime.date.today()).days if exp else None
        if days is not None and days <= 15:  # sắp hết hạn: nhắc gia hạn (màu cam, bấm được)
            tk.Button(self.lic_box, text=f"⚠ PRO còn {days} ngày — Gia hạn", fg="#FFFFFF", bg="#E67E22",
                      activebackground="#CA6F1E", relief="flat", font=("", 9, "bold"), padx=10, pady=3,
                      cursor="hand2", command=lambda: UpgradeWindow(self)).pack()
        else:  # đã là PRO: chỉ là nhãn mờ, không còn mời nâng cấp
            ttk.Label(self.lic_box, text=f"✅ PRO — {L.expiry_text()}", foreground="#5B8A72",
                      font=("", 9, "bold")).pack()

    def open_match_window(self):
        if self.df is None:
            messagebox.showinfo("Chưa có file", "Hãy chọn file Excel khách hàng trước.")
            return
        if not self.groups and not self.friends:
            messagebox.showinfo("Chưa có danh sách", "Hãy lấy danh sách nhóm (thẻ 'Nhóm Zalo') và/hoặc bạn bè "
                                                    "(thẻ 'Bạn bè Zalo') từ Zalo trước.")
            return
        GroupMatchWindow(self)

    def get_buffer(self):
        """Bộ nhớ đệm của tháng đang chọn (đổi tháng -> đổi bộ nhớ đệm)."""
        m = self.month.get().strip()
        if self.buffer is None or self.buffer.month != m:
            self.buffer = core.MessageBuffer(m)
        return self.buffer

    def reset_selected(self):
        sel = self.cust_table.tree.selection()
        if not sel or int(sel[0]) >= len(self.step1_plans):
            messagebox.showinfo("Chưa chọn", "Bấm vào tên một khách hàng trong bảng trước.")
            return
        p = self.step1_plans[int(sel[0])]
        buf = self.get_buffer()
        key = buf.key_of(p["t"])
        it = buf.get(key) or {}
        if it.get("status") != core.STATUS_SENT:
            messagebox.showinfo("Chưa gửi", "Khách này đang ở trạng thái Chưa gửi.")
            return
        if messagebox.askyesno("Đặt lại", f"Đặt '{it.get('name')}' về 'Chưa gửi'?\n"
                               f"Lần gửi tới, khách này sẽ được GỬI LẠI tin nhắn và PDF."):
            buf.reset(key)
            self.refresh_info()

    def current_template(self):
        return core.load_settings().get("template") or DEFAULT_TEMPLATE

    def customer_targets(self, indices):
        pc, nc, zc, fc = self.col("phone"), self.col("name"), self.col("zalo"), self.col("pdf")
        kc, cc, ac = self.col("key"), self.col("code"), self.col("amount")
        cust_tpl = core.load_settings().get("cust_tpl", {}) if lic.is_pro() else {}
        zitems = self.zalo_items()
        ztypes = {}
        for z in zitems:  # tên vừa là nhóm vừa là bạn bè -> coi là nhóm (đằng nào cũng bị coi là trùng)
            ztypes.setdefault(core.norm_name(z["name"]), z["type"])
        out = []
        for i in indices:
            row = self.df.loc[i].to_dict()
            t = {
                "kind": "Khách hàng",
                "label": row.get(nc, "") if nc else "",
                "phone": core.normalize_phone(row.get(pc, "")) if pc else "",
                "raw_phone": row.get(pc, "") if pc else "",
                "search_name": row.get(zc, "").strip() if zc else "",
                "row": row,
                "own_pdf": row.get(fc, "") if fc else "",
            }
            # v1.11: file công nợ — Mã KH làm chìa khóa, {Số tiền} = cột số tiền, ghép theo Số Dropbox
            if kc and row.get(kc, "").strip():
                t["cust_key"] = row[kc].strip()
                t["pdf_manual"] = self.pdfmap.get(t["cust_key"])
                name = cust_tpl.get(core.norm_name(t["cust_key"]))
                if name and name in self.tstore.templates:
                    t["tpl_name"], t["tpl_text"] = name, self.tstore.get(name)
            if ac:
                row = dict(row)
                row.setdefault(AMOUNT_FIELD, row.get(ac, ""))
                t["row"] = row
            if cc:
                t["code_raw"] = row.get(cc, "")
                t["code_parsed"] = core.parse_code(t["code_raw"])
                if not t["label"]:
                    t["label"] = t["code_raw"]
                if not t["search_name"]:
                    t["search_name"] = t["label"] or t["code_raw"] or ""
            if cc and not t["phone"]:
                t["excel_name"] = t["label"] or t["code_raw"]
                if zitems:
                    m = core.match_group(t["label"], [z["name"] for z in zitems], self.gmap, ztypes,
                                         code=t["code_raw"], map_key=t.get("cust_key"))
                else:
                    m = {"status": core.MATCH_NONE, "zalo": None, "candidates": [], "score": None, "type": None,
                         "note": "chưa lấy danh sách nhóm Zalo (thẻ Nhóm Zalo)"}
                t["match"] = m
                if m["status"] in core.MATCH_OK:
                    t["search_name"] = m["zalo"]
                    t["zalo_type"] = m["type"]
            # v1.7: ghép tên trong Excel -> tên nhóm THẬT trên Zalo (mã Dropbox / tên công ty / đã xác nhận)
            elif not t["phone"] and t["search_name"] and zitems:
                m = core.match_group(t["search_name"], [z["name"] for z in zitems], self.gmap, ztypes,
                                     map_key=t.get("cust_key"))
                t["excel_name"] = t["search_name"]
                t["match"] = m
                if m["status"] in core.MATCH_OK:
                    t["search_name"] = m["zalo"]
                    t["zalo_type"] = m["type"]
            out.append(t)
        return out

    def schedule_refresh(self):
        if self._refresh_job:
            self.after_cancel(self._refresh_job)
        self._refresh_job = self.after(300, self.refresh_info)

    def refresh_info(self, keep_checked=True):
        """Tính lại cột File PDF / Nhóm Zalo / Trạng thái cho mọi khách trong file Excel."""
        self._refresh_job = None
        if self.df is None:
            return
        cols = list(self.df.columns)
        if self.col("code"):  # v1.11: file công nợ — chỉ hiện các cột cần thiết (cột bôi vàng + tên để dễ nhìn)
            cols = [c for c in dict.fromkeys((self.col("key"), self.col("name"), self.col("code"), self.col("amount")))
                    if c]
        targets = self.customer_targets(range(len(self.df)))
        plans, _ = build_plans(targets, self.current_template(), self.month.get(), self.pdf_dir.get(), [],
                               bool(self.col("pdf")), self.zalo_items(), self.check_groups.get(),
                               den_ngay=self.den_ngay.get(), internal_kw=self.internal_kw)
        self.step1_plans = plans
        # v1.6: tự soạn sẵn vào bộ nhớ đệm của tháng (khách đã gửi giữ nguyên)
        buf = self.get_buffer()
        if core.is_valid_month(self.month.get()):
            buf.sync(plans)
        rows = []
        for p in plans:
            vals = [p["row"].get(c, "") for c in cols]  # số tiền đã định dạng 5.000.000
            pdf = ", ".join(os.path.basename(f) for f in p["files"]) or ("❌ không thấy" if self.pdf_dir.get() else "—")
            rows.append(vals + [pdf, p["zalo"] or "—", ("❌ " + p["error"]) if p["error"] else
                                (("⚠ " + p["warn"]) if p["warn"] else "✅ Sẵn sàng"),
                                buf.status_text(buf.key_of(p["t"]))]
                        + ([p["t"].get("tpl_name") or "(mẫu chung)"] if lic.is_pro() else []))
        extra = ["📎 File PDF", "Nhóm Zalo", "Kiểm tra", "Gửi"] + (["Mẫu tin"] if lic.is_pro() else [])
        widths = {c: 190 for c in cols}
        widths.update({"📎 File PDF": 190, "Nhóm Zalo": 200, "Kiểm tra": 220, "Gửi": 200, "Mẫu tin": 130})
        if self.col("code"):
            widths.update({self.col("key"): 110, self.col("code"): 90, self.col("amount"): 110})
        self.cust_table.set_data(cols + extra, rows, keep_checked=keep_checked, widths=widths)
        sel = self.cust_table.tree.selection()
        if sel:
            self.preview_row(int(sel[0]))
        # v1.9: cảnh báo chọn nhầm cột SĐT (không có số điện thoại hợp lệ nào)
        pc = self.col("phone")
        if pc and not any(core.normalize_phone(v) for v in self.df[pc]):
            self.phone_warn.config(text=f"⚠ Cột SĐT '{pc}' không có số điện thoại hợp lệ nào — "
                                        f"nếu file không có SĐT, hãy chọn Cột SĐT = (không dùng).")
            if not self.phone_warn.winfo_ismapped():
                self.phone_warn.pack(anchor="w", before=self.hint1)  # chỉ chiếm chỗ khi có cảnh báo
        else:
            self.phone_warn.pack_forget()
        # v1.7: số khách cần xác nhận ghép nhóm + cột "Khách đã ghép" ở thẻ Nhóm Zalo
        need = sum(1 for i, t in enumerate(targets) if self._cust_visible(i)
                   and t.get("match") and t["match"]["status"] not in core.MATCH_OK)
        self.match_label.config(text=f"⚠ {need} cần xác nhận →" if need else "")
        if self.groups or self.friends:
            self.update_group_table(keep_checked=True)

    def preview_row(self, idx):
        if idx >= len(self.step1_plans):
            return
        p = self.step1_plans[idx]
        buf = self.get_buffer()
        it = buf.get(buf.key_of(p["t"])) or {}
        name = p['t']['label'] or p['t']['search_name']
        if it.get("status") == core.STATUS_SENT:  # đã gửi: hiện đúng nội dung ĐÃ gửi trong bộ nhớ đệm
            self.preview_text.config(state="normal")
            self.preview_text.delete("1.0", "end")
            self.preview_text.insert("1.0", it.get("message", ""))
            self.preview_text.config(state="disabled")
            self.preview_info.config(text=f"{name}   {buf.status_text(buf.key_of(p['t']))}   "
                                          f"📎 {', '.join(it.get('sent_files') or []) or '—'}", foreground="#7f8c8d")
            return
        show_preview(self.preview_text, p.get("tpl") or self.current_template(), p["row"])
        files = ", ".join(os.path.basename(f) for f in p["files"])
        info = name + (f"   📎 {files}" if files else "") + (f"   📝 {p['t']['tpl_name']}" if p["t"].get("tpl_name") else "")
        if p["error"]:
            info += "   ⚠ " + p["error"]
        elif p.get("warn"):
            info += "   ⚠ " + p["warn"]
        self.preview_info.config(text=info, foreground="#c0392b" if p["error"] else "#1e8449")

    def col(self, key):
        v = self.col_boxes[key].get()
        return None if v in ("", NONE) else v

    # --- nhóm & bạn bè (v1.8) ---
    @property
    def groups(self):
        return self.group_tab.items if hasattr(self, "group_tab") else []

    @property
    def friends(self):
        return self.friend_tab.items if hasattr(self, "friend_tab") else []

    def zalo_items(self):
        """Mọi tên trên Zalo (nhóm + bạn bè). Bạn bè trùng tên được lặp lại để luôn bị coi là 'không rõ ràng'."""
        out = [{"name": g["name"], "type": "nhom"} for g in self.groups
               if not core.is_internal_group(g["name"], self.internal_kw)]  # v1.11: bỏ nhóm nội bộ "Xử lý"
        for f in (self.friends if lic.is_pro() else []):  # ghép với bạn bè: chỉ bản PRO
            out += [{"name": f["name"], "type": "ban"}] * max(1, int(f.get("same_name", 1)))
        return out

    def _load_saved_groups(self):
        self.group_tab.load_saved()
        self.friend_tab.load_saved()

    def matched_customers(self):
        """{tên Zalo (chuẩn hóa): [tên khách trong Excel đã ghép]}"""
        res = {}
        for p in self.step1_plans:
            t = p["t"]
            if t.get("match") and t["match"]["status"] in core.MATCH_OK:
                res.setdefault(core.norm_name(t["search_name"]), []).append(t.get("excel_name") or t["label"])
        return res

    def update_group_table(self, keep_checked=True):
        self.group_tab.update_table(keep_checked)
        self.friend_tab.update_table(keep_checked)

    def _poll(self):
        try:
            while True:
                kind, val = self.q.get_nowait()
                if kind == "update":
                    self._on_update_result(*val[1:])
                    continue
                tab = {"nhom": self.group_tab, "ban": self.friend_tab}[val[0]]
                if kind == "list_status":
                    tab.status.config(text=val[1])
                elif kind == "list_done":
                    tab.set_items(val[1], val[2])
                    tab.fetch_btn.config(state="normal")
                    messagebox.showinfo("Xong", f"Đã lấy {len(val[1])} {tab.cfg['unit']} từ Zalo.")
                elif kind == "list_error":
                    tab.fetch_btn.config(state="normal")
                    tab.status.config(text=f"Lỗi khi lấy danh sách {tab.cfg['unit']}")
                    messagebox.showerror(f"Lỗi lấy danh sách {tab.cfg['unit']}", val[1])
        except queue.Empty:
            pass
        self.after(150, self._poll)

    def update_count(self):
        if hasattr(self, "count_label"):
            self.count_label.config(
                text=f"Đã chọn: {len(self.cust_table.checked)} khách hàng, {len(self.group_table.checked)} nhóm, "
                     f"{len(self.friend_table.checked)} bạn bè")

    # --- sang bước 2 ---
    def open_step2(self):
        targets = []
        if self.df is not None and self.cust_table.checked:
            if not self.col("phone") and not self.col("zalo") and not self.col("code"):
                messagebox.showwarning("Thiếu cột", "Hãy chọn Cột SĐT, Cột tên Zalo / tên nhóm hoặc Cột Số Dropbox.")
                return
            targets = self.customer_targets(sorted(self.cust_table.checked))
        # v1.4: nhóm trùng tên với khách trong Excel -> gộp (chỉ gửi 1 lần, dùng dữ liệu Excel)
        cust_names = {core.norm_name(t["search_name"]) for t in targets if t["search_name"]}
        all_names = [core.norm_name(z["name"]) for z in self.zalo_items()]
        merged = 0
        for kind, label, field, ztype, table, items in (
                ("Nhóm", "nhóm", GROUP_FIELD, "nhom", self.group_table, self.groups),
                ("Bạn bè", "bạn", FRIEND_FIELD, "ban", self.friend_table, self.friends)):
            for i in sorted(table.checked):
                g = items[i]
                k = core.norm_name(g["name"])
                if k in cust_names:
                    merged += 1
                    continue
                cust_names.add(k)
                targets.append({
                    "kind": kind, "label": g["name"], "phone": "", "raw_phone": "",
                    "search_name": g["name"], "row": {field: g["name"]}, "own_pdf": "", "zalo_type": ztype,
                    "duplicate": all_names.count(k) > 1,  # trùng tên (kể cả nhóm trùng tên bạn bè) -> không gửi
                })
        if not targets:
            messagebox.showinfo("Chưa chọn", "Hãy tích chọn ít nhất một khách hàng, một nhóm hoặc một bạn bè.")
            return
        cust_cols = list(self.df.columns) if self.df is not None else []
        if self.df is not None:
            core.save_settings(columns={k: self.col(k) for k in ("phone", "name", "zalo", "pdf")})
        ComposeWindow(self, targets, cust_cols, has_pdf_col=bool(self.col("pdf")), merged=merged)


# ================= BƯỚC 2 =================
class ComposeWindow(tk.Toplevel):
    def __init__(self, app, targets, cust_cols, has_pdf_col, merged=0):
        super().__init__(app)
        self.app = app
        n_c = sum(t["kind"] == "Khách hàng" for t in targets)
        n_g = sum(t["kind"] == "Nhóm" for t in targets)
        n_f = sum(t["kind"] == "Bạn bè" for t in targets)
        self.title(f"Bước 2: Soạn tin nhắn – {n_c} khách hàng, {n_g} nhóm, {n_f} bạn bè"
                   + (f" (đã gộp {merged} trùng với khách Excel)" if merged else "") + f" – v{APP_VERSION}")
        self.has_friends = n_f > 0
        h = min(900, self.winfo_screenheight() - 90)  # vừa màn hình laptop
        w = min(1120, self.winfo_screenwidth() - 30)
        self.geometry(f"{w}x{h}+10+10")
        set_icon(self)
        self.targets, self.cust_cols, self.has_pdf_col = targets, cust_cols, has_pdf_col
        self.has_groups = n_g > 0
        self.has_custs = n_c > 0
        self.shared_pdfs = []
        self.q = queue.Queue()
        self.stop_flag = threading.Event()
        self.worker = None
        self._build()
        self.after(150, self._poll)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build(self):
        pad = {"padx": 10, "pady": 3}
        st = core.load_settings()
        small = self.winfo_screenheight() < 900  # laptop 1366x768
        tpl_h, pv_h = (7, 9) if small else (11, 12)
        # --- biến chung + nội dung ---
        top = ttk.Frame(self)
        top.pack(fill="x", **pad)
        ttk.Label(top, text="Nội dung tin nhắn:", font=("", 11, "bold")).pack(side="left")
        ttk.Label(top, text="     Tháng {Tháng}:").pack(side="left")
        self.month = self.app.month  # dùng chung với Bước 1
        ttk.Entry(top, textvariable=self.month, width=10).pack(side="left", padx=4)
        self._mtrace = self.month.trace_add("write", lambda *_: self.update_preview())
        ttk.Label(top, text="   Đến ngày {Đến ngày}:").pack(side="left")
        ttk.Entry(top, textvariable=self.app.den_ngay, width=11).pack(side="left", padx=4)
        self._dtrace = self.app.den_ngay.trace_add("write", lambda *_: self.update_preview())

        ph = ttk.Frame(self)
        ph.pack(fill="x", padx=10)
        fields = [MONTH_FIELD, DATE_FIELD, AMOUNT_FIELD] + ([ZALO_FIELD] if lic.is_pro() else []) + \
                 ([GROUP_FIELD] if self.has_groups else []) + \
                 ([FRIEND_FIELD] if self.has_friends else []) + \
                 [c for c in (self.cust_cols if self.has_custs else []) if c != MONTH_FIELD]
        ttk.Label(ph, text="Chèn trường:").pack(side="left")
        self.field_cb = ttk.Combobox(ph, state="readonly", values=fields, width=25)
        self.field_cb.pack(side="left", padx=4)
        self.field_cb.current(0)
        ttk.Button(ph, text="Chèn vào tin nhắn", command=self.insert_field).pack(side="left")
        ttk.Label(ph, text="  (cột có chữ \"tiền\" tự định dạng 5.000.000)", foreground="gray").pack(side="left")

        # v1.8: quản lý mẫu tin nhắn
        ts = self.app.tstore
        tb = ttk.Frame(self)
        tb.pack(fill="x", padx=10, pady=(4, 0))
        ttk.Label(tb, text="Mẫu tin nhắn:", font=("", 9, "bold")).pack(side="left")
        self.tpl_cb = ttk.Combobox(tb, state="readonly", width=24)
        self.tpl_cb.pack(side="left", padx=4)
        self.tpl_cb.bind("<<ComboboxSelected>>", lambda e: self.choose_template())
        pro = lic.is_pro()
        # v1.11: Standard cũng CHỌN được giữa các mẫu có sẵn (AONE, AONE – Công nợ); tạo/sửa tên/xóa là PRO
        for txt, cmd, need_pro in (("➕ Tạo mới", self.tpl_new, True), ("💾 Lưu", self.tpl_save, False),
                                   ("✏ Đổi tên", self.tpl_rename, True), ("🗑 Xóa", self.tpl_delete, True),
                                   ("⭐ Đặt mặc định", self.tpl_default, True)):
            locked = need_pro and not pro
            ttk.Button(tb, text=("🔒 " + txt.split(" ", 1)[1]) if locked else txt,
                       command=self.pro_prompt if locked else cmd).pack(side="left", padx=1)
        self.restore_btn = ttk.Button(ph, command=self.reset_template)   # cùng dòng "Chèn trường" cho đỡ tràn
        self.restore_btn.pack(side="right")
        self.dirty_label = ttk.Label(tb, text="", foreground="#c0392b", font=("", 9, "bold"))
        self.dirty_label.pack(side="left", padx=6)
        name = st.get("template_name")
        self.tpl_name = name if name in ts.templates else ts.default

        self.text = tk.Text(self, height=tpl_h, wrap="word", font=("", 10), undo=True)
        self.text.pack(fill="x", **pad)
        working = st.get("template") if name in ts.templates else None  # bản đang soạn dở lần trước
        self.text.insert("1.0", working or ts.get(self.tpl_name))
        self.text.edit_modified(False)
        self.refresh_tpl_bar()
        self.text.bind("<<Modified>>", self._on_modified)

        pv = ttk.Frame(self)
        pv.pack(fill="x", padx=10)
        ttk.Label(pv, text="Xem trước cho:").pack(side="left")
        self.preview_cb = ttk.Combobox(pv, state="readonly", width=50,
                                       values=[f"{i + 1}. [{t['kind']}] {t['label'] or t['search_name'] or t['raw_phone']}"
                                               for i, t in enumerate(self.targets)])
        self.preview_cb.current(0)
        self.preview_cb.bind("<<ComboboxSelected>>", lambda e: self.update_preview())
        self.preview_cb.pack(side="left", padx=4)
        ttk.Label(pv, text="(chữ đỏ = thay đổi theo từng khách)", foreground="#d0021b").pack(side="left")
        self.preview_pdf = ttk.Label(self, text="", foreground="#0050c8")
        self.preview_pdf.pack(anchor="w", padx=10)
        self.preview = tk.Text(self, height=pv_h, wrap="word", font=("", 10), background="#f7f7f7", state="disabled")
        self.preview.pack(fill="x", **pad)

        # --- PDF (thư mục chọn ở Bước 1) ---
        pdf = ttk.Frame(self)
        pdf.pack(fill="x", **pad)
        folder = self.app.pdf_dir.get() or "(chưa chọn — về Bước 1 bấm 'Chọn thư mục PDF')"
        if len(folder) > 45:
            folder = "…" + folder[-44:]
        ttk.Label(pdf, text=f"📁 Thư mục PDF: {folder}", foreground="#0050c8").pack(side="left")
        ttk.Label(pdf, text="   File PDF chung (không bắt buộc):").pack(side="left")
        ttk.Button(pdf, text="➕", width=3, command=self.add_pdf).pack(side="left", padx=2)
        ttk.Button(pdf, text="➖", width=3, command=self.remove_pdf).pack(side="left")
        self.pdf_list = tk.Listbox(self, height=1)
        self.pdf_list.pack(fill="x", padx=10)

        # --- tùy chọn ---
        opt = ttk.Frame(self)
        opt.pack(fill="x", **pad)
        ttk.Label(opt, text="Nghỉ giữa 2 lượt (giây): từ").pack(side="left")
        self.dmin, self.dmax = tk.IntVar(value=st.get("delay_min", 20)), tk.IntVar(value=st.get("delay_max", 45))
        ttk.Spinbox(opt, from_=3, to=600, textvariable=self.dmin, width=5).pack(side="left", padx=3)
        ttk.Label(opt, text="đến").pack(side="left")
        ttk.Spinbox(opt, from_=3, to=900, textvariable=self.dmax, width=5).pack(side="left", padx=3)
        self.dry = tk.BooleanVar(value=False)
        ttk.Checkbutton(opt, text="Chạy thử (KHÔNG gửi)", variable=self.dry).pack(side="left", padx=12)
        ttk.Checkbutton(opt, text="Tên phải có trong danh sách nhóm / bạn bè Zalo đã lấy",
                        variable=self.app.check_groups, command=self.update_preview).pack(side="left")

        act = ttk.Frame(self)
        act.pack(fill="x", **pad)
        self.send_btn = ttk.Button(act, text="🔎 Kiểm tra & gửi", style="Accent.TButton", command=self.start_sending)
        self.send_btn.pack(side="left")
        self.stop_btn = ttk.Button(act, text="⏹ Dừng", command=self.stop_flag.set, state="disabled")
        self.stop_btn.pack(side="left", padx=6)
        self.progress = ttk.Progressbar(act, maximum=len(self.targets))
        self.progress.pack(side="left", fill="x", expand=True, padx=10)
        self.prog_label = ttk.Label(act, text=f"0/{len(self.targets)}")
        self.prog_label.pack(side="left")

        ttk.Label(self, text="Nhật ký:").pack(anchor="w", padx=10)
        self.log_box = tk.Text(self, height=4, font=("Consolas", 9), state="disabled")
        self.log_box.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.update_preview()

    # ----- soạn thảo -----
    def insert_field(self):
        f = self.field_cb.get()
        if f:
            self.text.insert("insert", "{" + f + "}")
            self.text.focus_set()

    def pro_prompt(self):
        if messagebox.askyesno("Chức năng PRO", "Quản lý nhiều mẫu tin nhắn thuộc bản PRO.\n"
                                                "Mở cửa sổ Nâng cấp PRO?", parent=self):
            UpgradeWindow(self.app)

    # ----- v1.8: quản lý mẫu tin nhắn -----
    def set_text(self, text):
        self.text.delete("1.0", "end")
        self.text.insert("1.0", text)
        self.update_preview()

    def is_dirty(self):
        return self.template() != self.app.tstore.get(self.tpl_name).strip()

    def refresh_tpl_bar(self):
        ts = self.app.tstore
        self.tpl_cb["values"] = [n + ("  ⭐" if n == ts.default else "") for n in ts.names()]
        self.tpl_cb.set(self.tpl_name + ("  ⭐" if self.tpl_name == ts.default else ""))
        self.restore_btn.config(text=f'↺ Khôi phục mẫu "{self.tpl_name}"')
        self.dirty_label.config(text="✱ có sửa đổi chưa lưu" if self.is_dirty() else "")

    def _ask_save_if_dirty(self):
        """True = được phép tiếp tục."""
        if not self.is_dirty():
            return True
        ans = messagebox.askyesnocancel("Chưa lưu", f'Mẫu "{self.tpl_name}" có sửa đổi chưa lưu.\n'
                                        "Lưu lại trước khi đổi mẫu?", parent=self)
        if ans is None:
            return False
        if ans:
            self.app.tstore.put(self.tpl_name, self.template())
        return True

    def choose_template(self):
        new = self.tpl_cb.get().replace("  ⭐", "")
        if new == self.tpl_name:
            return
        if not self._ask_save_if_dirty():
            self.refresh_tpl_bar()
            return
        self.tpl_name = new
        self.set_text(self.app.tstore.get(new))
        self.refresh_tpl_bar()

    def _ask_name(self, title, initial=""):
        from tkinter import simpledialog
        name = simpledialog.askstring(title, "Tên mẫu tin nhắn:", initialvalue=initial, parent=self)
        name = (name or "").strip()
        if not name:
            return None
        if name in self.app.tstore.templates and name != initial:
            messagebox.showwarning("Trùng tên", f'Đã có mẫu tên "{name}".', parent=self)
            return None
        return name

    def tpl_new(self):
        name = self._ask_name("Tạo mẫu mới")
        if name:
            self.app.tstore.put(name, self.template())  # mẫu mới = nội dung đang soạn
            self.tpl_name = name
            self.refresh_tpl_bar()

    def tpl_save(self):
        self.app.tstore.put(self.tpl_name, self.template())
        self.refresh_tpl_bar()

    def tpl_rename(self):
        name = self._ask_name("Đổi tên mẫu", self.tpl_name)
        if name and name != self.tpl_name:
            self.app.tstore.rename(self.tpl_name, name)
            self.tpl_name = name
            self.refresh_tpl_bar()

    def tpl_delete(self):
        ts = self.app.tstore
        if len(ts.templates) <= 1:
            messagebox.showinfo("Không xóa được", "Phải còn ít nhất 1 mẫu tin nhắn.", parent=self)
            return
        if messagebox.askyesno("Xóa mẫu", f'Xóa mẫu "{self.tpl_name}"?', parent=self):
            ts.delete(self.tpl_name)
            self.tpl_name = ts.default
            self.set_text(ts.get(self.tpl_name))
            self.refresh_tpl_bar()

    def tpl_default(self):
        self.app.tstore.set_default(self.tpl_name)
        self.refresh_tpl_bar()

    def reset_template(self):
        if messagebox.askyesno("Khôi phục", f'Bỏ các sửa đổi chưa lưu và khôi phục nội dung đã lưu của mẫu '
                                            f'"{self.tpl_name}"?', parent=self):
            self.set_text(self.app.tstore.get(self.tpl_name))
            self.refresh_tpl_bar()

    def _on_modified(self, _):
        if self.text.edit_modified():
            self.update_preview()
            self.text.edit_modified(False)

    def template(self):
        return self.text.get("1.0", "end-1c").strip()

    def update_preview(self):
        if not hasattr(self, "log_box"):  # giao diện chưa dựng xong
            return
        idx = max(self.preview_cb.current(), 0)
        tpl = self.template()
        plans, _ = self._plan(tpl, only=[idx])
        p = plans[0]
        show_preview(self.preview, p.get("tpl") or tpl, p["row"])
        names = [os.path.basename(f) for f in p["files"]]
        txt = ("📎 Gửi kèm: " + ", ".join(names)) if names else "📎 Không có file PDF"
        if p["t"].get("tpl_name"):
            txt += f"   📝 Khách này dùng mẫu riêng: {p['t']['tpl_name']}"
        if p["error"]:
            txt += "   ⚠ " + p["error"]
        self.preview_pdf.config(text=txt, foreground="#c0392b" if p["error"] else "#1e8449")
        core.save_settings(template=tpl, template_name=self.tpl_name)  # nhớ bản đang soạn
        if hasattr(self, "dirty_label"):
            self.dirty_label.config(text="✱ có sửa đổi chưa lưu" if self.is_dirty() else "")

    def add_pdf(self):
        for p in filedialog.askopenfilenames(parent=self, title="Chọn file PDF",
                                             filetypes=[("PDF", "*.pdf"), ("Tất cả", "*.*")]):
            if p not in self.shared_pdfs:
                self.shared_pdfs.append(p)
                self.pdf_list.insert("end", p)
        self.update_preview()

    def remove_pdf(self):
        for i in reversed(self.pdf_list.curselection()):
            self.pdf_list.delete(i)
            del self.shared_pdfs[i]
        self.update_preview()

    # ----- nhật ký / tiến độ -----
    def log(self, msg):
        self.q.put(("log", msg))

    def _poll(self):
        try:
            while True:
                kind, val = self.q.get_nowait()
                if kind == "log":
                    self.log_box.config(state="normal")
                    self.log_box.insert("end", f"[{datetime.datetime.now():%H:%M:%S}] {val}\n")
                    self.log_box.see("end")
                    self.log_box.config(state="disabled")
                elif kind == "progress":
                    self.progress["value"] = val
                    self.prog_label.config(text=f"{val}/{len(self.targets)}")
                elif kind == "done":
                    self.send_btn.config(state="normal")
                    self.stop_btn.config(state="disabled")
                    self.app.refresh_info()  # cập nhật cột "Gửi" ở Bước 1
                    messagebox.showinfo("Hoàn tất", val, parent=self)
        except queue.Empty:
            pass
        try:
            if self.winfo_exists():
                self.after(150, self._poll)
        except tk.TclError:
            pass

    # ----- chuẩn bị -----
    def _plan(self, tpl, only=None):
        app = self.app
        plans, unmatched = build_plans(self.targets, tpl, app.month.get(), app.pdf_dir.get(), self.shared_pdfs,
                                       self.has_pdf_col, app.zalo_items(), app.check_groups.get(), only=only,
                                       den_ngay=app.den_ngay.get(), internal_kw=app.internal_kw)
        if only is None:  # v1.6: đối chiếu bộ nhớ đệm
            buf = app.get_buffer()
            buf.sync(plans)
            for p in plans:
                p["key"] = buf.key_of(p["t"])
                it = buf.get(p["key"]) or {}
                if it.get("status") == core.STATUS_SENT:
                    p["already_sent"] = True
                    p["error"] = f"Đã gửi lúc {it.get('sent_at', '')} (muốn gửi lại: bấm 'Đặt lại: Chưa gửi' ở Bước 1)"
                else:
                    p["msg"] = it.get("message", p["msg"])  # gửi đúng nội dung trong bộ nhớ đệm
        return plans, unmatched

    def start_sending(self):
        if self.app.busy.is_set():
            messagebox.showinfo("Đang bận", "Ứng dụng đang dùng Zalo (lấy nhóm hoặc gửi tin). Hãy đợi xong.", parent=self)
            return
        tpl = self.template()
        if not tpl and not self.shared_pdfs and not self.app.pdf_dir.get().strip():
            messagebox.showwarning("Thiếu nội dung", "Hãy nhập nội dung tin nhắn hoặc chọn file PDF.", parent=self)
            return
        try:
            dmin, dmax = sorted((int(self.dmin.get()), int(self.dmax.get())))
        except (tk.TclError, ValueError):
            messagebox.showwarning("Sai thời gian", "Thời gian nghỉ phải là số.", parent=self)
            return
        if not core.is_valid_month(self.month.get()):
            messagebox.showwarning("Sai tháng", "Ô Tháng phải có dạng MM/YYYY, ví dụ 10/2026.", parent=self)
            return
        core.save_settings(template=tpl, delay_min=dmin, delay_max=dmax)
        plans, unmatched = self._plan(tpl)
        dry = self.dry.get()

        def go():
            self.stop_flag.clear()
            self.send_btn.config(state="disabled")
            self.stop_btn.config(state="normal")
            self.app.busy.set()
            self.worker = threading.Thread(target=self._run, args=(plans, dmin, dmax, dry), daemon=True)
            self.worker.start()

        PrecheckWindow(self, plans, unmatched, dry, go)

    # ----- gửi -----
    def _run(self, plans, dmin, dmax, dry):
        report = None
        ok = fail = 0
        sender = None
        try:
            from zalo_web import ZaloWebSender
            os.makedirs(datadir.path("ket_qua"), exist_ok=True)
            report = datadir.path("ket_qua", f"ket_qua_{datetime.datetime.now():%Y%m%d_%H%M%S}.csv")
            sender = ZaloWebSender(log=self.log)
            self.log(f"Phiên bản v{APP_VERSION} — đang mở Zalo Web bằng Google Chrome...")
            sender.start()
            if not sender.wait_for_login(should_stop=self.stop_flag.is_set):
                raise RuntimeError("Đã dừng.")
            self.log("Đã đăng nhập Zalo.")
            with open(report, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(["Thời gian", "Loại", "Tên", "SĐT", "Tên tìm trên Zalo", "Tin nhắn",
                            "PDF đã gửi", "Kết quả", "Ghi chú"])
                for i, p in enumerate(plans, 1):
                    if self.stop_flag.is_set():
                        self.log("⏹ Người dùng đã dừng.")
                        break
                    t = p["t"]
                    who = t["label"] or t["search_name"] or t["raw_phone"]
                    status, note, sent_files, tried = "THẤT BẠI", p["error"], [], False
                    if not p["error"]:
                        tried = True
                        try:
                            if t["phone"]:
                                sender.open_chat_by_phone(t["phone"])
                            else:
                                sender.open_chat_by_name(t["search_name"], kind=t.get("zalo_type"))
                            for path in p["files"]:
                                if not os.path.isfile(path):
                                    raise RuntimeError(f"File không còn tồn tại: {os.path.basename(path)}")
                            if dry:
                                if p["msg"]:
                                    sender.send_text(p["msg"], dry_run=True)  # dán + kiểm tra rồi xóa
                                status = "CHẠY THỬ OK"
                            else:
                                if p["msg"]:
                                    sender.send_text(p["msg"])  # chỉ gửi khi nội dung khớp từng dòng
                                status = "ĐÃ GỬI"
                                for path in p["files"]:
                                    try:
                                        sender.send_file(path)
                                        sent_files.append(os.path.basename(path))
                                    except Exception as e:
                                        status = "GỬI THIẾU PDF"
                                        note = f"Lỗi gửi {os.path.basename(path)}: {str(e).splitlines()[0][:150]}"
                                        break
                        except Exception as e:
                            note = str(e).splitlines()[0][:200] if str(e) else type(e).__name__
                    # v1.6: ghi trạng thái vào bộ nhớ đệm ngay sau mỗi người nhận
                    if not dry and p.get("key") and not p.get("already_sent"):
                        if status in ("ĐÃ GỬI", "GỬI THIẾU PDF"):
                            self.app.buffer.mark_sent(p["key"], sent_files,
                                                      note if status == "GỬI THIẾU PDF" else "")
                        elif tried:
                            self.app.buffer.mark_error(p["key"], note)
                    if status in ("ĐÃ GỬI", "CHẠY THỬ OK"):
                        ok += 1
                        extra = f" + {len(sent_files)} PDF" if sent_files else ""
                        if dry and p["files"]:
                            extra = f" ({len(p['files'])} PDF sẵn sàng)"
                        self.log(f"✅ {i}. [{t['kind']}] {who}: {status}{extra}")
                    else:
                        fail += 1
                        self.log(f"❌ {i}. [{t['kind']}] {who}: {status} — {note}")
                    w.writerow([f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S}", t["kind"], t["label"], t["phone"],
                                t["search_name"], p["msg"], "; ".join(sent_files), status, note])
                    f.flush()
                    self.q.put(("progress", i))
                    # v1.5: chỉ nghỉ khi đã thực sự gửi (hoặc chạy thử mở được chat)
                    if i < len(plans) and tried and status != "THẤT BẠI":
                        wait = random.randint(dmin, dmax)
                        self.log(f"   nghỉ {wait}s...")
                        for _ in range(wait * 10):
                            if self.stop_flag.is_set():
                                break
                            time.sleep(0.1)
            summary = f"Thành công: {ok}, thất bại: {fail}.\nBáo cáo: {report}"
        except Exception as e:
            summary = f"Lỗi: {e}\nThành công: {ok}, thất bại: {fail}."
            self.log(summary)
        finally:
            try:
                if sender:
                    sender.close()
            except Exception:
                pass
            self.app.busy.clear()
        self.q.put(("done", summary))

    def on_close(self):
        if self.worker and self.worker.is_alive():
            if not messagebox.askyesno("Đang gửi", "Đang gửi tin. Dừng và đóng?", parent=self):
                return
            self.stop_flag.set()
        try:
            self.month.trace_remove("write", self._mtrace)
            self.app.den_ngay.trace_remove("write", self._dtrace)
        except Exception:
            pass
        self.destroy()
        self.app.refresh_info()  # cập nhật lại bảng & xem trước ở Bước 1 theo mẫu tin mới


class GroupMatchWindow(tk.Toplevel):
    """v1.7: Ghép 'tên khách trong Excel' với 'nhóm Zalo'. Trường hợp không chắc chắn -> người dùng xác nhận,
    ứng dụng ghi nhớ vĩnh viễn (ghep_nhom.json) để lần sau không hỏi lại."""

    LABELS = {core.MATCH_CONFIRMED: "✅ Bạn đã xác nhận", core.MATCH_CODE: "✅ Tự động",
              core.MATCH_NAME: "✅ Tự động", core.MATCH_SUGGEST: "⚠ Gợi ý — chờ xác nhận",
              core.MATCH_AMBIGUOUS: "⚠ Cần bạn chọn", core.MATCH_NONE: "❌ Chưa có nhóm"}

    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.title(f"Ghép khách hàng (Excel) với nhóm / bạn bè Zalo – v{APP_VERSION}")
        self.geometry(f"{min(1150, self.winfo_screenwidth() - 40)}x{min(680, self.winfo_screenheight() - 90)}+15+10")
        set_icon(self)
        items = app.zalo_items()
        self.all_names = [z["name"] for z in items]          # có lặp lại tên trùng
        self.types = {}
        for z in items:
            self.types.setdefault(core.norm_name(z["name"]), set()).add(z["type"])
        self.uniq_names = list(dict.fromkeys(self.all_names))
        top = ttk.Frame(self, padding=8)
        top.pack(fill="x")
        self.summary = ttk.Label(top, font=("", 10, "bold"))
        self.summary.pack(side="left")
        self.only_need = tk.BooleanVar(value=True)
        ttk.Checkbutton(top, text="Chỉ hiện dòng cần xác nhận", variable=self.only_need,
                        command=self.reload).pack(side="left", padx=20)
        ttk.Button(top, text="✔ Xác nhận tất cả GỢI Ý", command=self.confirm_all).pack(side="right")

        box = ttk.Frame(self, padding=(8, 0))
        box.pack(fill="both", expand=True)
        cols = ("excel", "zalo", "status", "pdf")
        self.tree = ttk.Treeview(box, columns=cols, show="headings", selectmode="browse")
        for c, t, w in (("excel", "Khách trong Excel", 300), ("zalo", "Nhóm / bạn bè Zalo", 300),
                        ("status", "Trạng thái", 300), ("pdf", "📎 File PDF", 230)):
            self.tree.heading(c, text=t)
            self.tree.column(c, width=w, anchor="w")
        self.tree.tag_configure("ok", foreground="#1e8449")
        self.tree.tag_configure("need", foreground="#b9770e")
        self.tree.tag_configure("none", foreground="#c0392b")
        ysb = ttk.Scrollbar(box, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=ysb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        ysb.pack(side="left", fill="y")
        self.tree.bind("<<TreeviewSelect>>", lambda e: self.on_select())

        edit = ttk.LabelFrame(self, text="Chọn nhóm / bạn bè Zalo cho khách đang chọn", padding=8)
        edit.pack(fill="x", padx=8, pady=8)
        self.cur_label = ttk.Label(edit, text="(bấm vào một dòng ở bảng trên)", font=("", 10, "bold"))
        self.cur_label.pack(anchor="w")
        row = ttk.Frame(edit)
        row.pack(fill="x", pady=4)
        ttk.Label(row, text="Nhóm / bạn bè (gõ để tìm):").pack(side="left")
        self.combo = ttk.Combobox(row, width=60)
        self.combo.pack(side="left", padx=6)
        self.combo.bind("<KeyRelease>", self.on_type)
        ttk.Button(row, text="✔ Xác nhận", command=self.confirm_current).pack(side="left", padx=4)
        ttk.Button(row, text="↺ Xóa xác nhận", command=self.forget_current).pack(side="left")
        prow = ttk.Frame(edit)  # v1.11: chọn file PDF bằng tay khi không tự ghép được
        prow.pack(fill="x", pady=(2, 4))
        ttk.Label(prow, text="File PDF:").pack(side="left")
        self.pdf_label = ttk.Label(prow, text="—", foreground="#0050C8")
        self.pdf_label.pack(side="left", padx=6)
        ttk.Button(prow, text="📎 Chọn file PDF…", command=self.pick_pdf).pack(side="left", padx=4)
        ttk.Button(prow, text="✖ Bỏ PDF chọn tay", command=self.clear_pdf).pack(side="left")
        ttk.Label(edit, text="[Nhóm] = nhóm Zalo, [Bạn bè] = chat riêng với bạn bè. Xếp theo độ giống với tên khách. "
                             "Lựa chọn được GHI NHỚ — lần sau không hỏi lại.", foreground="gray").pack(anchor="w")
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.reload()

    def lab(self, name):
        ts = self.types.get(core.norm_name(name), set())
        tag = "[Nhóm + Bạn bè]" if len(ts) > 1 else ("[Bạn bè]" if "ban" in ts else "[Nhóm]")
        return f"{tag} {name}"

    @staticmethod
    def unlab(text):
        return re.sub(r"^\s*\[(Nhóm \+ Bạn bè|Nhóm|Bạn bè)\]\s*", "", text or "").strip()

    @staticmethod
    def mkey(t):
        return t.get("cust_key") or t["excel_name"]  # v1.11: ghi nhớ theo Mã khách hàng nếu có

    def show_name(self, t):
        return f"{t.get('code_raw') or '—'}  ·  {t['label']}" if "code_raw" in t else t["excel_name"]

    def reload(self, select=None):
        app = self.app
        plans = app.step1_plans
        self.rows = [(i, t, plans[i] if i < len(plans) else None)
                     for i, t in enumerate(app.customer_targets(range(len(app.df))))
                     if t.get("match") and app._cust_visible(i)]
        self.targets = [t for _, t, _ in self.rows]
        self.tree.delete(*self.tree.get_children())
        need = pdf_need = 0
        for k, (i, t, p) in enumerate(self.rows):
            m = t["match"]
            ok = m["status"] in core.MATCH_OK
            pdf_err = bool(p and ("PDF" in p["error"]) and app.pdf_dir.get())
            warn = m.get("warn_name")
            need += not ok
            pdf_need += ok and pdf_err
            if self.only_need.get() and ok and not pdf_err and not warn and str(k) != select:
                continue
            zalo = self.lab(m["zalo"]) if m["zalo"] else \
                ("— " + str(len(m["candidates"])) + " ứng viên" if m["candidates"] else "—")
            tag = "ok" if ok and not pdf_err else ("none" if m["status"] == core.MATCH_NONE else "need")
            st = f"{self.LABELS[m['status']]} ({m['note']})" + (f" ⚠ {warn}" if warn else "")
            pdf = (", ".join(os.path.basename(f) for f in p["files"]) if p and p["files"] else
                   ("❌ chưa có" if pdf_err else "—")) + (" (chọn tay)" if t.get("pdf_manual") else "")
            self.tree.insert("", "end", iid=str(k), tags=(tag,), values=(self.show_name(t), zalo, st, pdf))
        self.summary.config(text=f"{len(self.rows)} khách — ✅ đã ghép nhóm: {len(self.rows) - need}   "
                                 f"⚠ cần xác nhận nhóm: {need}" + (f"   📎 thiếu PDF: {pdf_need}" if pdf_need else ""))
        if select and self.tree.exists(select):
            self.tree.selection_set(select)
            self.tree.see(select)

    def current(self):
        sel = self.tree.selection()
        return (int(sel[0]), self.targets[int(sel[0])]) if sel else (None, None)

    def on_select(self):
        i, t = self.current()
        if t is None:
            return
        m = t["match"]
        self.cur_label.config(text=f"Khách: {self.show_name(t)}     →     {self.LABELS[m['status']]} ({m['note']})")
        p = self.rows[i][2]
        self.pdf_label.config(text=(", ".join(os.path.basename(f) for f in p["files"]) if p and p["files"] else "—")
                              + (" (chọn tay)" if t.get("pdf_manual") else ""))
        ranked = list(dict.fromkeys(m["candidates"] + sorted(
            self.uniq_names, key=lambda g: -core.name_similarity(t["excel_name"], g))))
        self.ranked = [self.lab(g) for g in ranked]
        self.combo["values"] = self.ranked
        self.combo.set(self.lab(m["zalo"]) if m["zalo"] else (self.ranked[0] if self.ranked else ""))

    def on_type(self, event):
        if event.keysym in ("Up", "Down", "Return", "Escape"):
            return
        q = core.strip_accents(self.combo.get())
        base = getattr(self, "ranked", [self.lab(g) for g in self.uniq_names])
        self.combo["values"] = [g for g in base if q in core.strip_accents(g)] if q else base

    def confirm_current(self):
        i, t = self.current()
        if t is None:
            messagebox.showinfo("Chưa chọn", "Bấm vào một dòng trong bảng trước.", parent=self)
            return
        name = self.unlab(self.combo.get())
        exact = [g for g in self.all_names if core.norm_name(g) == core.norm_name(name)]
        if len(exact) != 1:
            messagebox.showwarning("Không hợp lệ", "Hãy chọn ĐÚNG một nhóm / bạn bè có trong danh sách."
                                   + (" (Trên Zalo có nhiều nhóm / bạn bè trùng tên này — không thể phân biệt "
                                      "khi gửi. Hãy đổi tên gợi nhớ trên Zalo cho khác nhau.)"
                                      if len(exact) > 1 else ""), parent=self)
            return
        kind = next(iter(self.types.get(core.norm_name(exact[0]), {"nhom"})))
        self.app.gmap.confirm(self.mkey(t), exact[0], kind)
        self.after_change(str(i))

    def forget_current(self):
        i, t = self.current()
        if t is not None:
            self.app.gmap.forget(self.mkey(t))
            self.after_change(str(i))

    def confirm_all(self):
        sug = [t for t in self.targets if t["match"]["status"] == core.MATCH_SUGGEST]
        if not sug:
            messagebox.showinfo("Không có gợi ý", "Không có dòng nào ở trạng thái Gợi ý.", parent=self)
            return
        lines = "\n".join(f"• {self.show_name(t)}  →  {self.lab(t['match']['zalo'])}" for t in sug[:15])
        more = f"\n… và {len(sug) - 15} dòng khác" if len(sug) > 15 else ""
        if messagebox.askyesno("Xác nhận tất cả gợi ý", f"Xác nhận {len(sug)} gợi ý sau?\n\n{lines}{more}",
                               parent=self):
            for t in sug:
                self.app.gmap.confirm(self.mkey(t), t["match"]["zalo"], t["match"].get("type") or "nhom")
            self.after_change()

    def pick_pdf(self):
        i, t = self.current()
        if t is None:
            messagebox.showinfo("Chưa chọn", "Bấm vào một dòng trong bảng trước.", parent=self)
            return
        folder = self.app.pdf_dir.get()
        if not folder:
            messagebox.showinfo("Chưa có thư mục PDF", "Hãy bấm 'Chọn thư mục PDF' ở Bước 1 trước.", parent=self)
            return
        files = filedialog.askopenfilenames(parent=self, title=f"Chọn file PDF cho {self.show_name(t)}",
                                            initialdir=folder, filetypes=[("PDF", "*.pdf")])
        if not files:
            return
        if any(os.path.normcase(os.path.dirname(os.path.abspath(f))) != os.path.normcase(os.path.abspath(folder))
               for f in files):
            messagebox.showwarning("Sai thư mục", "Chỉ chọn file nằm trong thư mục PDF đã chọn ở Bước 1.", parent=self)
            return
        self.app.pdfmap.set(self.mkey(t), [os.path.basename(f) for f in files])
        self.after_change(str(i))

    def clear_pdf(self):
        i, t = self.current()
        if t is not None:
            self.app.pdfmap.set(self.mkey(t), [])
            self.after_change(str(i))

    def after_change(self, select=None):
        self.app.refresh_info()
        self.reload(select)
        self.on_select()

    def close(self):
        self.destroy()
        self.app.refresh_info()


def restart_app():
    """Khởi động lại ứng dụng (sau khi kích hoạt / hủy kích hoạt Key)."""
    import subprocess
    exe = sys.executable
    pyw = os.path.join(os.path.dirname(exe), "pythonw.exe")
    if sys.platform.startswith("win") and os.path.isfile(pyw):
        exe = pyw
    return subprocess.Popen([exe, os.path.join(BASE_DIR, "app.py")], cwd=BASE_DIR)


def update_desktop_icon(pro):
    """Đổi icon của biểu tượng 'Gửi tin Zalo' trên Desktop (chỉ Windows, lỗi thì bỏ qua)."""
    if not sys.platform.startswith("win"):
        return
    try:
        import cai_dat
        pyw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
        cai_dat.create_shortcut(pyw if os.path.isfile(pyw) else sys.executable,
                                icon=os.path.join(BASE_DIR, "icon_pro.ico" if pro else "icon.ico"))
    except Exception:
        pass


def open_mail(subject, body=""):
    import urllib.parse
    import webbrowser
    q = urllib.parse.urlencode({"subject": subject, "body": body}, quote_via=urllib.parse.quote)
    try:
        webbrowser.open(f"mailto:{AUTHOR_EMAIL}?{q}")
    except Exception:
        pass


class UpdateWindow(tk.Toplevel):
    """v1.10: tải bản mới (kiểm SHA-256) rồi giao cho cap_nhat.py cài sau khi ứng dụng đóng."""

    def __init__(self, app, data):
        super().__init__(app)
        self.app, self.data = app, data
        self.title(f"Cập nhật lên v{data['version']}")
        set_icon(self)
        self.transient(app)
        f = ttk.Frame(self, padding=18)
        f.pack(fill="both", expand=True)
        ttk.Label(f, text=f"Cập nhật v{APP_VERSION}  →  v{data['version']}", font=("", 13, "bold")).pack(anchor="w")
        notes = tk.Text(f, height=8, width=70, wrap="word", font=("", 10), background="#F7F7F7")
        notes.insert("1.0", data.get("notes") or "(không có ghi chú)")
        notes.config(state="disabled")
        notes.pack(fill="x", pady=8)
        ttk.Label(f, text="Dữ liệu của bạn (Key PRO, mẫu tin, ghép nhóm, đã gửi...) được GIỮ NGUYÊN. "
                          "Bản cũ được sao lưu, nếu bản mới lỗi sẽ tự quay về.", style="Muted.TLabel",
                  wraplength=560).pack(anchor="w")
        self.bar = ttk.Progressbar(f, length=560)
        self.bar.pack(fill="x", pady=8)
        self.msg = ttk.Label(f, text="Đang tải bản mới từ GitHub...", font=("", 10, "bold"))
        self.msg.pack(anchor="w")
        self.cancel = threading.Event()
        b = ttk.Frame(f)
        b.pack(fill="x", pady=(10, 0))
        ttk.Button(b, text="Hủy", command=self.on_cancel).pack(side="right")
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.grab_set()
        self.app.busy.set()
        threading.Thread(target=self.work, daemon=True).start()

    def on_cancel(self):
        self.cancel.set()
        self.app.busy.clear()
        self.destroy()

    def work(self):
        import updater

        def prog(done, total):
            self.app.after(0, lambda: self._prog(done, total))
        try:
            zp = updater.download(self.data, prog, self.cancel.is_set)
            self.app.after(0, lambda: self.install(zp))
        except Exception as e:
            err = str(e).splitlines()[0] if str(e) else type(e).__name__
            self.app.after(0, lambda: self.fail(err))

    def _prog(self, done, total):
        if not self.winfo_exists():
            return
        if total:
            self.bar["maximum"] = total
            self.bar["value"] = done
            self.msg.config(text=f"Đang tải... {done / 1e6:.1f} / {total / 1e6:.1f} MB")
        else:
            self.msg.config(text=f"Đang tải... {done / 1e6:.1f} MB")

    def fail(self, err):
        self.app.busy.clear()
        if self.winfo_exists():
            self.msg.config(text="❌ " + err, foreground="#c0392b")

    def install(self, zp):
        import updater
        self.msg.config(text="✅ Đã tải và kiểm tra chữ ký. Ứng dụng sẽ đóng để cài bản mới rồi tự mở lại...",
                        foreground="#1e8449")
        self.update()
        try:
            updater.launch_installer(zp, self.data["version"])
        except Exception as e:
            self.fail(f"Không chạy được trình cài: {e}")
            return
        self.app.after(1200, self.app.destroy)


class UpgradeWindow(tk.Toplevel):
    """⭐ Nâng cấp PRO: hiện Mã máy, nhập Key để mở khóa."""

    def __init__(self, app):
        super().__init__(app)
        self.app = app
        L = lic.get()
        self.title("Nâng cấp lên bản PRO")  # cửa sổ tự co giãn theo nội dung (không cắt chữ)
        set_icon(self)
        self.transient(app)
        f = ttk.Frame(self, padding=18)
        f.pack(fill="both", expand=True)
        if L.is_pro:
            ttk.Label(f, text="✅ Bạn đang dùng bản PRO", font=("", 14, "bold"), foreground="#1e8449").pack(anchor="w")
            ttk.Label(f, text=f"Hạn dùng: {L.expiry_text()}", font=("", 11)).pack(anchor="w", pady=4)
        else:
            ttk.Label(f, text="⭐ Nâng cấp lên bản PRO", font=("", 14, "bold")).pack(anchor="w")
            ttk.Label(f, text="Bản PRO mở khóa thêm:", font=("", 10, "bold")).pack(anchor="w", pady=(8, 2))
            for feat in lic.PRO_FEATURES:
                ttk.Label(f, text="   • " + feat).pack(anchor="w")
        mf = ttk.LabelFrame(f, text="Bước 1: Gửi Mã máy này cho nhà cung cấp để nhận Key", padding=10)
        mf.pack(fill="x", pady=(14, 8))
        self.code = lic.machine_code()
        ttk.Label(mf, text=self.code, font=("Consolas", 16, "bold"), foreground="#0050C8").pack(side="left")
        ttk.Button(mf, text="📋 Sao chép mã máy", command=self.copy_code).pack(side="left", padx=14)
        ttk.Button(mf, text="✉ Gửi email xin Key", command=lambda: open_mail(
            f"Xin Key PRO – Gửi tin Zalo – Mã máy {self.code}",
            f"Xin chào anh Trung,\n\nTôi muốn nâng cấp bản PRO.\nMã máy: {self.code}\nTên / đơn vị: \n"
            f"Thời hạn mong muốn: \n")).pack(side="left")
        ttk.Label(f, text=f"Gửi Mã máy cho tác giả {AUTHOR}: {AUTHOR_EMAIL}", style="Muted.TLabel").pack(
            anchor="w", before=mf, pady=(10, 0))
        kf = ttk.LabelFrame(f, text="Bước 2: Dán Key nhận được vào đây rồi bấm Kích hoạt", padding=10)
        kf.pack(fill="x")
        self.key = tk.Text(kf, height=4, font=("Consolas", 10), wrap="char")
        self.key.pack(fill="x")
        row = ttk.Frame(kf)
        row.pack(fill="x", pady=(8, 0))
        ttk.Button(row, text="🔑 Kích hoạt", style="Accent.TButton", command=self.activate).pack(side="left")
        if L.is_pro:
            ttk.Button(row, text="Hủy kích hoạt (về Standard)", command=self.deactivate).pack(side="right")
        self.msg = ttk.Label(f, text="", font=("", 10, "bold"), wraplength=660)
        self.msg.pack(anchor="w", pady=8)
        self.grab_set()

    def copy_code(self):
        self.clipboard_clear()
        self.clipboard_append(self.code)
        self.msg.config(text="📋 Đã sao chép mã máy. Hãy gửi mã này cho nhà cung cấp.", foreground="#1e8449")

    def activate(self):
        key = self.key.get("1.0", "end").strip()
        if not key:
            self.msg.config(text="Hãy dán Key vào ô trên.", foreground="#c0392b")
            return
        info = lic.get().activate(key)
        if not info["ok"]:
            self.msg.config(text="❌ " + info["reason"], foreground="#c0392b")
            return
        update_desktop_icon(True)
        self.app.apply_license_ui()  # nút vàng biến mất ngay, tiêu đề + icon đổi sang PRO
        exp = info["expires"].strftime("%d/%m/%Y") if info["expires"] else "Vĩnh viễn"
        messagebox.showinfo("Kích hoạt thành công", f"✅ Đã kích hoạt bản PRO (hạn dùng: {exp}).\n"
                            "Ứng dụng sẽ khởi động lại để mở khóa thẻ Bạn bè và các chức năng PRO.", parent=self)
        self.restart()

    def deactivate(self):
        if messagebox.askyesno("Hủy kích hoạt", "Xóa Key trên máy này và quay về bản Standard?", parent=self):
            lic.get().deactivate()
            update_desktop_icon(False)
            self.app.apply_license_ui()
            self.restart()

    def restart(self):
        app = self.app
        manual = "Hãy TẮT rồi MỞ LẠI ứng dụng để dùng đầy đủ chức năng."
        if app.busy.is_set():
            messagebox.showinfo("Đang bận", "Ứng dụng đang gửi tin / lấy danh sách.\n" + manual, parent=self)
            self.destroy()
            return
        try:
            proc = restart_app()
        except Exception as e:
            messagebox.showwarning("Chưa tự mở lại được", f"Không tự khởi động lại được ({e}).\n" + manual, parent=self)
            self.destroy()
            return
        self.destroy()

        def check(n=0):  # chỉ đóng cửa sổ cũ khi bản mới đã mở được
            code = proc.poll() if proc else 0
            if code is not None and code != 0:
                messagebox.showwarning("Chưa tự mở lại được", "Ứng dụng mới không mở được.\n" + manual, parent=app)
            elif code is None and n < 3:
                app.after(700, lambda: check(n + 1))
            else:
                app.destroy()
        app.after(700, check)


class AboutWindow(tk.Toplevel):
    def copy_email(self):
        self.clipboard_clear()
        self.clipboard_append(AUTHOR_EMAIL)
        self.copied.config(text="📋 Đã sao chép email.")

    @staticmethod
    def open_data():
        try:
            os.startfile(datadir.DATA_DIR)  # Windows
        except Exception:
            messagebox.showinfo("Thư mục dữ liệu", datadir.DATA_DIR)

    """ℹ Giới thiệu: bản đang dùng, phiên bản, mã máy, chức năng."""

    def __init__(self, app):
        super().__init__(app)
        L = lic.get()
        self.title("Giới thiệu")
        set_icon(self)
        self.transient(app)
        f = ttk.Frame(self, padding=18)
        f.pack(fill="both", expand=True)
        try:
            self._img = tk.PhotoImage(file=os.path.join(BASE_DIR, "icon_pro.png" if L.is_pro else "icon.png")) \
                .subsample(3, 3)
            ttk.Label(f, image=self._img).pack(side="top", anchor="w")
        except Exception:
            pass
        ttk.Label(f, text=APP_NAME, font=("", 14, "bold")).pack(anchor="w", pady=(6, 0))
        ttk.Label(f, text=f"Bản {L.edition} — phiên bản v{APP_VERSION}", font=("", 11, "bold"),
                  foreground="#B8860B" if L.is_pro else "#0050C8").pack(anchor="w")
        if L.is_pro:
            ttk.Label(f, text=f"Hạn dùng PRO: {L.expiry_text()}").pack(anchor="w")
        ttk.Label(f, text=f"Mã máy: {lic.machine_code()}", font=("Consolas", 10)).pack(anchor="w", pady=(2, 10))
        ttk.Label(f, text="Chức năng bản PRO:", font=("", 10, "bold")).pack(anchor="w")
        for feat in lic.PRO_FEATURES:
            ttk.Label(f, text=("   ✅ " if L.is_pro else "   🔒 ") + feat).pack(anchor="w")
        ttk.Label(f, text="Lịch sử thay đổi: xem file NHAT_KY_PHIEN_BAN.md trong thư mục ứng dụng.",
                  style="Muted.TLabel").pack(anchor="w", pady=(12, 0))
        ttk.Label(f, text=f"Dữ liệu (Key, mẫu tin, ghép nhóm, đã gửi, báo cáo, đăng nhập Zalo) lưu tại:\n{datadir.DATA_DIR}",
                  style="Muted.TLabel").pack(anchor="w", pady=(4, 0))
        # v1.10: thông tin tác giả
        au = ttk.LabelFrame(f, text="Tác giả & hỗ trợ", padding=10)
        au.pack(fill="x", pady=(12, 0))
        ttk.Label(au, text=f"👤 Tác giả:  {AUTHOR}", font=("", 10, "bold")).pack(anchor="w")
        er = ttk.Frame(au)
        er.pack(fill="x", pady=(4, 0))
        ttk.Label(er, text=f"✉ Liên hệ:  {AUTHOR_EMAIL}", font=("", 10)).pack(side="left")
        ttk.Button(er, text="📋 Sao chép email", command=self.copy_email).pack(side="left", padx=(12, 4))
        ttk.Button(er, text="✉ Gửi email hỗ trợ", command=lambda: open_mail(
            f"Hỗ trợ Gửi tin Zalo – {L.edition} v{APP_VERSION} – Mã máy {lic.machine_code()}",
            "Xin chào anh Trung,\n\nTôi cần hỗ trợ: ")).pack(side="left")
        self.copied = ttk.Label(au, text="", foreground="#1e8449")
        self.copied.pack(anchor="w")
        ttk.Label(au, text=f"© {datetime.date.today().year} {AUTHOR}", style="Muted.TLabel").pack(anchor="w")
        b = ttk.Frame(f)
        b.pack(fill="x", pady=12)
        if not L.is_pro:
            ttk.Button(b, text="⭐ Nâng cấp PRO", style="Pro.TButton",
                       command=lambda: (self.destroy(), UpgradeWindow(app))).pack(side="left")
        else:
            ttk.Button(b, text="🔑 Gia hạn / Quản lý Key",
                       command=lambda: (self.destroy(), UpgradeWindow(app))).pack(side="left")
        ttk.Button(b, text="📂 Mở thư mục dữ liệu", command=self.open_data).pack(side="left", padx=8)
        ttk.Button(b, text="🔄 Kiểm tra cập nhật",
                   command=lambda: app.check_update(silent=False, parent=self)).pack(side="left")
        ttk.Button(b, text="Đóng", command=self.destroy).pack(side="right")


class PrecheckWindow(tk.Toplevel):
    """v1.3: Bảng kiểm tra trước khi gửi — mỗi người nhận một dòng."""

    def __init__(self, parent, plans, unmatched, dry, on_ok):
        super().__init__(parent)
        self.title(f"Kiểm tra trước khi gửi – v{APP_VERSION}")
        w = min(1250, self.winfo_screenwidth() - 40)
        self.geometry(f"{w}x{min(620, self.winfo_screenheight() - 90)}+10+10")
        set_icon(self)
        self.transient(parent)
        self.on_ok = on_ok
        ready = [p for p in plans if not p["error"]]
        n_sent = sum(1 for p in plans if p.get("already_sent"))
        n_pdf = sum(len(p["files"]) for p in ready)

        head = ttk.Frame(self, padding=10)
        head.pack(fill="x")
        mode = "CHẠY THỬ (không gửi)" if dry else "GỬI THẬT"
        ttk.Label(head, text=f"Chế độ: {mode}", font=("", 11, "bold"),
                  foreground="#0050c8" if dry else "#c0392b").pack(anchor="w")
        ttk.Label(head, text=f"✅ Sẵn sàng gửi: {len(ready)} người nhận (kèm {n_pdf} file PDF)      "
                             f"⏭ Đã gửi trước đó: {n_sent}      "
                             f"❌ Bỏ qua do lỗi: {len(plans) - len(ready) - n_sent}",
                  font=("", 10, "bold")).pack(anchor="w", pady=2)
        if unmatched:
            more = f" … và {len(unmatched) - 8} file khác" if len(unmatched) > 8 else ""
            ttk.Label(head, foreground="#b9770e", wraplength=1000,
                      text=f"⚠ {len(unmatched)} file PDF trong thư mục không khớp với người nhận nào (có thể đặt sai tên, "
                           f"hoặc khách này không được chọn): " + ", ".join(unmatched[:8]) + more).pack(anchor="w")

        box = ttk.Frame(self, padding=(10, 0))
        box.pack(fill="both", expand=True)
        cols = ("stt", "who", "zalo", "pdf", "data", "status")
        tree = ttk.Treeview(box, columns=cols, show="headings")
        for c, t, w in (("stt", "#", 35), ("who", "Người nhận", 210), ("zalo", "Nhóm Zalo", 95),
                        ("pdf", "File PDF", 210), ("data", "Dữ liệu trong tin", 140), ("status", "Trạng thái", 480)):
            tree.heading(c, text=t)
            tree.column(c, width=w, minwidth=w // 2, anchor="w", stretch=(c == "status"))
        tree.tag_configure("bad", foreground="#c0392b")
        tree.tag_configure("ok", foreground="#1e8449")
        tree.tag_configure("sent", foreground="#7f8c8d")
        # dòng lỗi lên trước để dễ thấy
        order = lambda x: (0 if x[1]["error"] and not x[1].get("already_sent") else 2 if x[1].get("already_sent") else 1)
        for i, p in sorted(enumerate(plans, 1), key=order):
            t = p["t"]
            tag = "sent" if p.get("already_sent") else ("bad" if p["error"] else "ok")
            status = ("⏭ " + p["error"]) if p.get("already_sent") else \
                (("❌ Bỏ qua: " + p["error"]) if p["error"] else "✅ Sẵn sàng")
            tree.insert("", "end", tags=(tag,), values=(
                i, t["label"] or t["search_name"] or t["raw_phone"], p["zalo"],
                ", ".join(os.path.basename(f) for f in p["files"]) or "—", p["data"],
                status))
        ysb = ttk.Scrollbar(box, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=ysb.set)
        tree.pack(side="left", fill="both", expand=True)
        ysb.pack(side="left", fill="y")

        bot = ttk.Frame(self, padding=10)
        bot.pack(fill="x")
        ttk.Button(bot, text="Hủy (quay lại sửa)", command=self.destroy).pack(side="right")
        b = ttk.Button(bot, text=f"🚀 Bắt đầu {'chạy thử' if dry else 'gửi'} ({len(ready)})", style="Accent.TButton",
                       command=self.ok)
        b.pack(side="right", padx=8)
        if not ready:
            b.config(state="disabled")
        self.grab_set()

    def ok(self):
        self.grab_release()
        self.destroy()
        self.on_ok()


def main():
    try:
        if sys.platform.startswith("win"):
            import ctypes
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(1)  # chữ nét trên màn hình độ phân giải cao
            except Exception:
                pass
        datadir.migrate_old_data()  # v1.9.1: chép dữ liệu cũ (nếu có) sang thư mục dữ liệu cố định
        App().mainloop()
    except Exception:
        err = traceback.format_exc()
        with open(datadir.path("loi.txt"), "w", encoding="utf-8") as f:
            f.write(err)
        try:
            messagebox.showerror("Lỗi", f"Ứng dụng gặp lỗi:\n{err[-800:]}\n\nChi tiết lưu ở file loi.txt")
        except Exception:
            print(err)


if __name__ == "__main__":
    main()
