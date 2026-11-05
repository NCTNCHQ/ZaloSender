"""Các hàm xử lý dữ liệu: đọc file khách hàng, nhận diện cột, chuẩn hóa SĐT, ghép nội dung tin nhắn."""
import os
import re
import unicodedata
from collections import Counter

import pandas as pd

PHONE_KEYWORDS = ["sdt", "so dien thoai", "dien thoai", "so dt", "phone", "mobile", "dt"]
NAME_KEYWORDS = ["ho ten", "ho va ten", "ten khach", "khach hang", "ten", "name"]
ZALO_NAME_KEYWORDS = ["ten zalo", "ten nhom", "zalo", "nhom", "group"]
PDF_KEYWORDS = ["file pdf", "pdf", "dinh kem", "tep", "file"]


def strip_accents(text: str) -> str:
    text = unicodedata.normalize("NFD", str(text))
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return text.replace("đ", "d").replace("Đ", "D").lower().strip()


def load_customers(path: str) -> pd.DataFrame:
    """Đọc file .xlsx / .xls / .csv, giữ mọi giá trị ở dạng chuỗi (không mất số 0 đầu SĐT)."""
    lower = path.lower()
    if lower.endswith(".csv"):
        last_err = None
        for enc in ("utf-8-sig", "cp1258", "cp1252"):
            try:
                df = pd.read_csv(path, dtype=str, encoding=enc, sep=None, engine="python")
                break
            except UnicodeDecodeError as e:
                last_err = e
        else:
            raise last_err
    else:
        df = pd.read_excel(path, dtype=str)
    df = df.fillna("")
    df.columns = [str(c).strip() for c in df.columns]
    df = df[[c for c in df.columns if not c.lower().startswith("unnamed")] or df.columns]
    # bỏ dòng trống hoàn toàn
    df = df[df.apply(lambda r: any(str(v).strip() for v in r), axis=1)].reset_index(drop=True)
    for c in df.columns:
        df[c] = df[c].astype(str).str.strip()
    return df


def _guess(columns, keywords, exclude=()):
    norm = {c: strip_accents(c) for c in columns if c not in exclude}
    for kw in keywords:
        for c, n in norm.items():
            if n == kw:
                return c
    for kw in keywords:
        for c, n in norm.items():
            if kw in n.split() or (len(kw) > 3 and kw in n):
                return c
    return None


def guess_phone_column(columns):
    # tránh nhận nhầm cột "Tên Zalo" là cột SĐT
    return _guess(columns, PHONE_KEYWORDS, exclude=[c for c in columns if "ten" in strip_accents(c).split()])


def guess_zalo_name_column(columns):
    return _guess(columns, ZALO_NAME_KEYWORDS)


def guess_name_column(columns, exclude=()):
    return _guess(columns, NAME_KEYWORDS, exclude=exclude)


def guess_pdf_column(columns):
    return _guess(columns, PDF_KEYWORDS)


def normalize_phone(raw: str) -> str:
    """'+84 912.345.678' -> '0912345678'. Trả về '' nếu không hợp lệ."""
    s = str(raw).strip()
    if s.endswith(".0"):  # số bị Excel đổi thành float
        s = s[:-2]
    digits = re.sub(r"\D", "", s)
    if digits.startswith("84") and len(digits) >= 11:
        digits = "0" + digits[2:]
    elif len(digits) == 9 and not digits.startswith("0"):
        digits = "0" + digits  # Excel làm mất số 0 đầu
    if not re.fullmatch(r"0\d{9}", digits):
        return ""
    return digits


_PLACEHOLDER = re.compile(r"\{([^{}]+)\}")


def render_segments(template: str, row: dict):
    """Tách tin nhắn thành các đoạn [(chữ, loại)]: loại = "" (chữ cố định), "var" (giá trị đã thay),
    "missing" (trường không có dữ liệu, giữ nguyên {Tên})."""
    lookup = {strip_accents(k): v for k, v in row.items()}
    out, pos = [], 0
    for m in _PLACEHOLDER.finditer(template):
        if m.start() > pos:
            out.append((template[pos:m.start()], ""))
        key = m.group(1)
        if key in row:
            val = row[key]
        else:
            val = lookup.get(strip_accents(key))
        if val is None or str(val).strip() == "":
            out.append((m.group(0) if val is None else "", "missing"))
        else:
            out.append((str(val), "var"))
        pos = m.end()
    if pos < len(template):
        out.append((template[pos:], ""))
    return out


def render_message(template: str, row: dict) -> str:
    """Thay {Tên cột} bằng giá trị của khách hàng. Không phân biệt hoa thường / dấu."""
    return "".join(t for t, _ in render_segments(template, row))


def unknown_placeholders(template: str, columns) -> list:
    known = {strip_accents(c) for c in columns}
    return [m for m in _PLACEHOLDER.findall(template) if strip_accents(m) not in known]


def norm_name(s: str) -> str:
    """Chuẩn hóa tên để so khớp chính xác: bỏ khoảng trắng thừa, không phân biệt hoa thường."""
    return " ".join(unicodedata.normalize("NFC", str(s)).split()).casefold()


def resolve_pdfs(value: str, folder: str):
    """Ô 'File PDF' có thể ghi nhiều file, cách nhau bởi dấu ;
    Trả về (danh_sách_đường_dẫn_tìm_thấy, danh_sách_tên_thiếu)."""
    found, missing = [], []
    for part in re.split(r"[;\n]", str(value or "")):
        name = part.strip().strip('"')
        if not name:
            continue
        candidates = [name] if os.path.isabs(name) else []
        if folder:
            candidates.append(os.path.join(folder, name))
            if not name.lower().endswith(".pdf"):
                candidates.append(os.path.join(folder, name + ".pdf"))
        hit = next((c for c in candidates if os.path.isfile(c)), None)
        if hit:
            found.append(os.path.abspath(hit))
        else:
            missing.append(name)
    return found, missing


# ================== v1.3 ==================
def is_money_column(col: str) -> bool:
    return "tien" in strip_accents(col).split() or "tien" in strip_accents(col)


def format_money(value) -> str:
    """'5000000' / '5000000.0' -> '5.000.000'. Giá trị đã có dấu chấm/phẩy hoặc không phải số thì giữ nguyên."""
    s = str(value).strip()
    m = re.fullmatch(r"(\d+)(?:\.0+)?", s)
    if not m:
        return s
    return f"{int(m.group(1)):,}".replace(",", ".")


def prepare_row(row: dict, extra: dict = None) -> dict:
    """Ghép dữ liệu khách + biến chung (vd. Tháng) và định dạng các cột tiền."""
    out = dict(extra or {})
    for k, v in row.items():
        out[k] = format_money(v) if is_money_column(k) else v
    return out


def empty_placeholders(template: str, row: dict) -> list:
    """Các trường có trong mẫu tin nhắn nhưng giá trị của người nhận này đang trống."""
    lookup = {strip_accents(k): str(v).strip() for k, v in row.items()}
    res = []
    for m in _PLACEHOLDER.findall(template):
        k = strip_accents(m)
        if k in lookup and not lookup[k] and m not in res:
            res.append(m)
    return res


_INVALID_FILE_CHARS = re.compile(r'[\\/:*?"<>|]')


def file_key(name: str) -> str:
    """Khóa so khớp tên file: thay ký tự Windows không cho phép bằng '_', chuẩn hóa khoảng trắng, chữ thường."""
    return norm_name(_INVALID_FILE_CHARS.sub("_", str(name)))


def index_pdf_folder(folder: str) -> dict:
    """{đường_dẫn: khóa_tên_file (không đuôi)} cho mọi file .pdf trong thư mục (không tính thư mục con)."""
    res = {}
    if folder and os.path.isdir(folder):
        for f in sorted(os.listdir(folder)):
            p = os.path.join(folder, f)
            if f.lower().endswith(".pdf") and os.path.isfile(p):
                res[p] = norm_name(os.path.splitext(f)[0])
    return res


def match_pdfs(keys, index: dict) -> list:
    """Tìm file PDF có tên = khóa, hoặc khóa + '_...' / khóa + ' - ...' (một khách nhiều file).
    'Nguyễn Văn An_HD01.pdf' khớp 'Nguyễn Văn An' nhưng 'Nguyễn Văn Anh.pdf' thì KHÔNG."""
    keys = [file_key(k) for k in keys if str(k).strip()]
    found = []
    for path, stem in index.items():
        for k in keys:
            if stem == k or stem.startswith(k + "_") or stem.startswith(k + " - "):
                found.append(path)
                break
    return found


def previous_month(today=None) -> str:
    import datetime
    today = today or datetime.date.today()
    y, m = (today.year, today.month - 1) if today.month > 1 else (today.year - 1, 12)
    return f"{m:02d}/{y}"


# ---- lưu cài đặt ----
import json as _json

import datadir as _dd  # v1.9.1: dữ liệu nằm ở thư mục cố định (AppData)

SETTINGS_PATH = _dd.path("cai_dat_ung_dung.json")


def load_settings() -> dict:
    try:
        with open(SETTINGS_PATH, encoding="utf-8") as f:
            return _json.load(f)
    except Exception:
        return {}


def save_settings(**kw):
    s = load_settings()
    s.update(kw)
    try:
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            _json.dump(s, f, ensure_ascii=False, indent=1)
    except Exception:
        pass


# ================== v1.6: BỘ NHỚ ĐỆM TIN NHẮN ==================
import datetime as _dt
import threading as _threading

BUFFER_DIR = _dd.path("bo_nho_dem")
STATUS_PENDING, STATUS_SENT = "Chưa gửi", "Đã gửi"


def is_valid_month(month: str) -> bool:
    m = re.fullmatch(r"\s*(\d{1,2})\s*[/\-.]\s*(\d{4})\s*", str(month or ""))
    return bool(m) and 1 <= int(m.group(1)) <= 12


def month_key(month: str) -> str:
    """'10/2026' -> '2026-10' (tên file bộ nhớ đệm)."""
    m = re.fullmatch(r"\s*(\d{1,2})\s*[/\-.]\s*(\d{4})\s*", str(month or ""))
    if m:
        return f"{m.group(2)}-{int(m.group(1)):02d}"
    return re.sub(r"[^\w\-]+", "_", str(month or "chua_ro_thang")).strip("_") or "chua_ro_thang"


class MessageBuffer:
    """Tin nhắn đã soạn sẵn cho từng người nhận của MỘT tháng, lưu ở bo_nho_dem/<YYYY-MM>.json.
    - Người CHƯA gửi: luôn được soạn lại tự động theo Excel mới nhất.
    - Người ĐÃ gửi: giữ nguyên, không gửi lại (trừ khi bấm 'Đặt lại: Chưa gửi')."""

    def __init__(self, month: str):
        self.month = month
        self.path = os.path.join(BUFFER_DIR, month_key(month) + ".json")
        self.lock = _threading.RLock()
        self.items = {}
        try:
            with open(self.path, encoding="utf-8") as f:
                self.items = _json.load(f).get("items", {})
        except Exception:
            self.items = {}

    @staticmethod
    def key_of(t: dict) -> str:
        # v1.7: khóa theo TÊN TRONG EXCEL (không đổi khi ghép lại nhóm Zalo)
        return norm_name(t.get("excel_name") or t.get("label") or t.get("search_name") or t.get("phone") or "")

    def save(self):
        with self.lock:
            os.makedirs(BUFFER_DIR, exist_ok=True)
            tmp = self.path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                _json.dump({"month": self.month, "items": self.items}, f, ensure_ascii=False, indent=1)
            os.replace(tmp, self.path)  # ghi an toàn: không hỏng file nếu mất điện giữa chừng

    def get(self, key):
        with self.lock:
            return self.items.get(key)

    def sync(self, plans) -> bool:
        """Cập nhật bộ nhớ đệm từ kế hoạch gửi (soạn từ Excel). Trả về True nếu có thay đổi (đã lưu)."""
        changed = False
        with self.lock:
            for p in plans:
                t = p["t"]
                k = self.key_of(t)
                if not k:
                    continue
                cur = self.items.get(k)
                new = {"name": t.get("label") or t.get("search_name") or t.get("phone"),
                       "zalo": t.get("search_name") or t.get("phone") or "",
                       "message": p["msg"], "files": [os.path.basename(f) for f in p["files"]],
                       "data": p.get("data", ""), "error": p.get("error", "")}
                if cur and cur.get("status") == STATUS_SENT:
                    changed_now = cur.get("message") != p["msg"]
                    if cur.get("excel_changed") != changed_now:
                        cur["excel_changed"] = changed_now
                        changed = True
                    continue
                base = cur or {"status": STATUS_PENDING}
                if any(base.get(f) != v for f, v in new.items()):
                    base.update(new)
                    self.items[k] = base
                    changed = True
            if changed:
                self.save()
        return changed

    def mark_sent(self, key, files, note=""):
        """note khác rỗng = đã gửi tin nhắn nhưng gửi PDF bị lỗi."""
        with self.lock:
            it = self.items.setdefault(key, {})
            it.update(status=STATUS_SENT, sent_at=_dt.datetime.now().strftime("%d/%m/%Y %H:%M"),
                      sent_files=files, last_error=note, excel_changed=False)
            self.save()

    def mark_error(self, key, note):
        with self.lock:
            it = self.items.setdefault(key, {"status": STATUS_PENDING})
            it["last_error"] = note
            self.save()

    def reset(self, key):
        with self.lock:
            it = self.items.get(key)
            if it:
                it.update(status=STATUS_PENDING, sent_at="", last_error="", excel_changed=False)
                self.save()

    def status_text(self, key):
        it = self.get(key)
        if not it:
            return STATUS_PENDING
        if it.get("status") == STATUS_SENT:
            s = (f"⚠ Đã gửi tin, THIẾU PDF {it.get('sent_at', '')}" if it.get("last_error")
                 else f"✅ Đã gửi {it.get('sent_at', '')}")
            return s + (" (Excel đã đổi sau khi gửi)" if it.get("excel_changed") else "")
        if it.get("last_error"):
            return "⏳ Chưa gửi (lần trước lỗi)"
        return "⏳ Chưa gửi"


# ================== v1.7: MÃ DROPBOX, GHÉP NHÓM, SẮP XẾP TIẾNG VIỆT ==================
import difflib as _difflib

_CODE_RE = re.compile(r"^\s*(\d[0-9A-Za-z]*)(?=[\s.\-_,:;)]|$)")


def dropbox_code(name: str) -> str:
    """Mã Dropbox ở đầu tên: bắt đầu bằng chữ số, có thể kèm chữ, kết thúc trước . - _ hoặc khoảng trắng.
    '99rs. công ty Anh TRUNG' -> '99rs'; '33- TOOL' -> '33'; 'Lớp 4TuổiB1' -> ''."""
    m = _CODE_RE.match(str(name or ""))
    return m.group(1).lower() if m else ""


def strip_code(name: str) -> str:
    """Bỏ mã Dropbox và dấu ngăn cách ở đầu tên: '99rs. công ty ABC' -> 'công ty ABC'."""
    s = str(name or "")
    m = _CODE_RE.match(s)
    if not m:
        return s.strip()
    return re.sub(r"^[\s.\-_,:;)]+", "", s[m.end():]).strip()


def leading_number(name: str):
    m = re.match(r"\s*(\d+)", str(name or ""))
    return int(m.group(1)) if m else None


def member_count(text) -> int:
    m = re.search(r"\d[\d.,]*", str(text or ""))
    return int(re.sub(r"[.,]", "", m.group(0))) if m else 0


# Bảng chữ cái tiếng Việt: a ă â b c d đ e ê g h i k l m n o ô ơ p q r s t u ư v x y
_VN_ALPHA = "aăâbcdđeêghiklmnoôơpqrstuưvxy"
_TONES = {"̀": 1, "́": 2, "̉": 3, "̃": 4, "̣": 5}  # huyền sắc hỏi ngã nặng


def vn_sort_key(name: str):
    """Khóa sắp xếp A → Z theo bảng chữ cái tiếng Việt (không phân biệt hoa thường)."""
    primary, tones = [], []
    for ch in unicodedata.normalize("NFC", str(name or "").lower()):
        d = unicodedata.normalize("NFD", ch)
        tone = next((_TONES[c] for c in d if c in _TONES), 0)
        base = unicodedata.normalize("NFC", "".join(c for c in d if c not in _TONES))
        if base in _VN_ALPHA:
            primary.append((1, _VN_ALPHA.index(base), ""))
        elif base.isdigit():
            primary.append((0, int(base), ""))
        elif base.isspace():
            primary.append((-1, 0, ""))
        else:
            primary.append((2, 0, base))
        tones.append(tone)
    return (primary, tones)


_LEGAL_WORDS = ["cong ty", "cty", "tnhh", "co phan", "cp", "mtv", "mot thanh vien", "1 thanh vien",
                "dntn", "doanh nghiep tu nhan", "tm", "dv", "xnk", "tmdv", "jsc", "ltd", "co ltd", "va",
                "nhom", "group", "hoi", "team"]  # v1.8: bỏ cả chữ chung "Nhóm", "Group"...


def _company_tokens(name: str):
    s = strip_accents(strip_code(name))
    s = re.sub(r"[^\w\s]", " ", s)
    s = " " + " ".join(s.split()) + " "
    for w in sorted(_LEGAL_WORDS, key=len, reverse=True):
        s = s.replace(" " + w + " ", " ")
    return s.split()


def name_similarity(a: str, b: str) -> float:
    """Độ giống 0..1 giữa 2 tên công ty (đã bỏ mã Dropbox và các chữ chung như Công ty, TNHH...)."""
    ta, tb = _company_tokens(a), _company_tokens(b)
    if not ta or not tb:
        return 0.0
    ratio = _difflib.SequenceMatcher(None, " ".join(ta), " ".join(tb)).ratio()
    sa, sb = set(ta), set(tb)
    jaccard = len(sa & sb) / len(sa | sb)
    # v1.8: kết hợp độ giống chuỗi + tỉ lệ từ trùng (Jaccard) -> "NHÓM A" vs "Nhóm Mây" không còn 86%
    score = 0.5 * ratio + 0.5 * jaccard
    if min(len(" ".join(ta)), len(" ".join(tb))) <= 3 and ta != tb:
        score = min(score, 0.4)  # tên quá ngắn (vd 'a', 'b') chỉ coi là giống khi trùng hẳn
    return round(score, 3)


MATCH_CONFIRMED, MATCH_CODE, MATCH_NAME = "confirmed", "auto_code", "auto_name"
MATCH_SUGGEST, MATCH_AMBIGUOUS, MATCH_NONE = "suggest", "ambiguous", "none"
MATCH_OK = (MATCH_CONFIRMED, MATCH_CODE, MATCH_NAME)


class GroupMap:
    """Ghi nhớ VĨNH VIỄN lựa chọn ghép 'tên khách trong Excel' -> 'tên nhóm Zalo' (ghep_nhom.json)."""

    PATH = _dd.path("ghep_nhom.json")

    def __init__(self):
        try:
            with open(self.PATH, encoding="utf-8") as f:
                self.items = _json.load(f).get("items", {})
        except Exception:
            self.items = {}

    def save(self):
        tmp = self.PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            _json.dump({"items": self.items}, f, ensure_ascii=False, indent=1)
        os.replace(tmp, self.PATH)

    def get(self, excel_name):
        return self.items.get(norm_name(excel_name))

    def confirm(self, excel_name, zalo_name, kind="nhom"):
        self.items[norm_name(excel_name)] = {"excel": excel_name, "zalo": zalo_name, "type": kind,
                                             "at": _dt.datetime.now().strftime("%d/%m/%Y %H:%M")}
        self.save()

    def forget(self, excel_name):
        if self.items.pop(norm_name(excel_name), None) is not None:
            self.save()


def match_group(excel_name: str, group_names, gmap: "GroupMap" = None, types: dict = None) -> dict:
    """Tìm nhóm Zalo cho 1 khách. Chỉ tự ghép khi CHẮC CHẮN (trùng đúng 1 nhóm);
    còn lại trả về gợi ý / danh sách ứng viên để người dùng xác nhận."""
    names = list(group_names)
    norm_count = Counter(norm_name(g) for g in names)
    ranked = sorted(names, key=lambda g: -name_similarity(excel_name, g))

    types = types or {}

    def res(status, zalo=None, candidates=None, score=None, note=""):
        cand = candidates if candidates is not None else ranked[:15]
        return {"status": status, "zalo": zalo, "candidates": cand, "score": score, "note": note,
                "type": types.get(norm_name(zalo), "nhom") if zalo else None}

    # 1. đã được người dùng xác nhận
    saved = gmap.get(excel_name) if gmap else None
    if saved and saved.get("zalo"):
        if norm_count.get(norm_name(saved["zalo"]), 0) >= 1:
            return res(MATCH_CONFIRMED, saved["zalo"], note="bạn đã xác nhận " + saved.get("at", ""))
        note = f"nhóm đã xác nhận '{saved['zalo']}' không còn trong danh sách nhóm Zalo"
    else:
        note = ""
    # 2. trùng khớp hoàn toàn cả tên
    exact = [g for g in names if norm_name(g) == norm_name(excel_name)]
    if len(exact) == 1:
        return res(MATCH_NAME, exact[0], note="trùng tên")
    if len(exact) > 1:
        return res(MATCH_AMBIGUOUS, None, exact, note=f"{len(exact)} nhóm / bạn bè Zalo trùng tên")
    # 3. mã Dropbox
    code = dropbox_code(excel_name)
    if code:
        same = [g for g in names if dropbox_code(g) == code]
        if len(same) == 1 and norm_count[norm_name(same[0])] == 1:
            return res(MATCH_CODE, same[0], note=f"mã {code}")
        if len(same) > 1:
            same.sort(key=lambda g: -name_similarity(excel_name, g))
            return res(MATCH_AMBIGUOUS, None, same + [g for g in ranked if g not in same][:10],
                       note=f"{len(same)} nhóm cùng mã {code}")
    # 4. tên công ty (đã bỏ mã) trùng khớp hoàn toàn
    comp = norm_name(strip_code(excel_name))
    if comp:
        same = [g for g in names if norm_name(strip_code(g)) == comp]
        if len(same) == 1 and norm_count[norm_name(same[0])] == 1:
            return res(MATCH_NAME, same[0], note="trùng tên công ty")
        if len(same) > 1:
            return res(MATCH_AMBIGUOUS, None, same, note=f"{len(same)} nhóm trùng tên công ty")
    # 5. gần giống -> chỉ gợi ý
    if ranked:
        best = ranked[0]
        sc = name_similarity(excel_name, best)
        if sc >= 0.6:
            return res(MATCH_SUGGEST, best, score=sc, note=(note + "; " if note else "") + f"giống {sc:.0%}")
    return res(MATCH_NONE, None, note=note or "không tìm thấy nhóm phù hợp")


def last_sent_map() -> dict:
    """{tên Zalo (chuẩn hóa): thời điểm gửi gần nhất (datetime)} — quét mọi bộ nhớ đệm các tháng."""
    out = {}
    if not os.path.isdir(BUFFER_DIR):
        return out
    for f in os.listdir(BUFFER_DIR):
        if not f.endswith(".json"):
            continue
        try:
            with open(os.path.join(BUFFER_DIR, f), encoding="utf-8") as fh:
                items = _json.load(fh).get("items", {})
        except Exception:
            continue
        for it in items.values():
            if it.get("status") != STATUS_SENT or not it.get("sent_at"):
                continue
            try:
                when = _dt.datetime.strptime(it["sent_at"], "%d/%m/%Y %H:%M")
            except ValueError:
                continue
            for key in {norm_name(it.get("zalo") or ""), norm_name(it.get("name") or "")} - {""}:
                if key not in out or when > out[key]:
                    out[key] = when
    return out


def first_letter(name: str) -> str:
    """Chữ cái đầu theo bảng chữ cái tiếng Việt (bỏ dấu thanh): 'Đặng' -> 'đ', 'Ánh' -> 'a', '33.' -> '0-9'."""
    s = unicodedata.normalize("NFC", str(name or "").strip().lower())
    if not s:
        return ""
    if s[0].isdigit():
        return "0-9"
    d = unicodedata.normalize("NFD", s[0])
    base = unicodedata.normalize("NFC", "".join(c for c in d if c not in _TONES))
    return base if base in _VN_ALPHA else "#"


# ================== v1.8: KHO MẪU TIN NHẮN ==================
class TemplateStore:
    """Các mẫu tin nhắn do người dùng đặt tên (mau_tin_nhan.json). Mặc định ban đầu: 'AONE'."""

    PATH = _dd.path("mau_tin_nhan.json")

    def __init__(self, factory_text: str, factory_name: str = "AONE"):
        try:
            with open(self.PATH, encoding="utf-8") as f:
                d = _json.load(f)
            self.templates = dict(d.get("templates", {}))
            self.default = d.get("default", factory_name)
        except Exception:
            self.templates, self.default = {}, factory_name
        if not self.templates:
            # lần đầu: lấy nội dung đang dùng ở bản cũ (nếu có) làm mẫu AONE
            self.templates = {factory_name: load_settings().get("template") or factory_text}
            self.default = factory_name
            self.save()
        if self.default not in self.templates:
            self.default = next(iter(self.templates))

    def save(self):
        tmp = self.PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            _json.dump({"default": self.default, "templates": self.templates}, f, ensure_ascii=False, indent=1)
        os.replace(tmp, self.PATH)

    def names(self):
        return list(self.templates)

    def get(self, name):
        return self.templates.get(name, "")

    def put(self, name, text):
        self.templates[name] = text
        self.save()

    def rename(self, old, new):
        self.templates = {(new if k == old else k): v for k, v in self.templates.items()}
        if self.default == old:
            self.default = new
        self.save()

    def delete(self, name):
        if len(self.templates) <= 1:
            raise ValueError("Phải còn ít nhất 1 mẫu")
        self.templates.pop(name, None)
        if self.default == name:
            self.default = next(iter(self.templates))
        self.save()

    def set_default(self, name):
        self.default = name
        self.save()
