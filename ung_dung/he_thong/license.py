"""Bản quyền: Standard (mặc định) / PRO (mở khóa bằng Key).

- Mã máy: lấy từ mã định danh của Windows (MachineGuid), băm SHA-256 -> 'ZS-XXXX-XXXX-XXXX'.
- Key: nội dung (mã máy | hạn dùng | ngày cấp | PRO) + CHỮ KÝ SỐ Ed25519.
  Ứng dụng chỉ giữ KHÓA CÔNG KHAI để kiểm tra; khóa bí mật để tạo Key nằm ở công cụ Tạo Key của nhà cung cấp.
- Kiểm tra hoàn toàn offline, không cần Internet.
"""
import base64
import datetime
import hashlib
import json
import os
import platform
import re
import uuid

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
try:  # v1.9.1: Key lưu ở thư mục dữ liệu cố định (cài lại không mất)
    import datadir
    LICENSE_FILE = datadir.path("ban_quyen.json")
except ImportError:  # công cụ Tạo Key không cần file này
    LICENSE_FILE = os.path.join(BASE_DIR, "ban_quyen.json")
PUBLIC_KEY_B64 = "sW1SNV0s+QmFX2Rc8FfpuJVlfJzpkBXuh/tPvP+u/Tk="
_SALT = "ZaloSender/v1"
FOREVER = "VV"  # vĩnh viễn

PRO_FEATURES = [
    "Quản lý nhiều mẫu tin nhắn (tạo mới, lưu, đổi tên, xóa, đặt mặc định)",
    "Thẻ Bạn bè Zalo: lấy danh sách, gửi thông báo chung cho bạn bè",
    "Ghép khách hàng trong Excel với bạn bè Zalo (chat riêng)",
    "Lọc theo Chữ đầu và các kiểu hiển thị nâng cao (Chỉ đã ghép / Chưa ghép / Đã tích)",
    "Trường {Tên Zalo} dùng chung cho mọi người nhận",
]


def _raw_machine_id():
    try:
        import winreg  # Windows
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography",
                            0, winreg.KEY_READ | getattr(winreg, "KEY_WOW64_64KEY", 0)) as k:
            return str(winreg.QueryValueEx(k, "MachineGuid")[0])
    except Exception:
        pass
    for p in ("/etc/machine-id", "/var/lib/dbus/machine-id"):
        try:
            with open(p) as f:
                v = f.read().strip()
                if v:
                    return v
        except Exception:
            pass
    return f"{uuid.getnode():012x}-{platform.node()}"


def machine_code():
    h = hashlib.sha256((_SALT + _raw_machine_id()).encode()).hexdigest().upper()[:12]
    return f"ZS-{h[0:4]}-{h[4:8]}-{h[8:12]}"


def normalize_machine(code):
    s = re.sub(r"[^0-9A-Za-z]", "", str(code or "")).upper()
    if s.startswith("ZS"):
        s = s[2:]
    return f"ZS-{s[0:4]}-{s[4:8]}-{s[8:12]}" if len(s) == 12 else ""


def _b32(data):
    s = base64.b32encode(data).decode().rstrip("=")
    return "-".join(s[i:i + 6] for i in range(0, len(s), 6))


def _unb32(key):
    s = re.sub(r"[^A-Za-z2-7]", "", str(key or "")).upper()
    return base64.b32decode(s + "=" * (-len(s) % 8))


def make_key(private_key, machine, expires=None, issued=None):
    """Dùng trong công cụ Tạo Key. expires: datetime.date hoặc None (vĩnh viễn)."""
    m = normalize_machine(machine)
    if not m:
        raise ValueError("Mã máy không hợp lệ (dạng ZS-XXXX-XXXX-XXXX)")
    issued = issued or datetime.date.today()
    payload = f"{m}|{expires.strftime('%Y%m%d') if expires else FOREVER}|{issued.strftime('%Y%m%d')}|PRO".encode()
    return _b32(payload + private_key.sign(payload))


def check_key(key, machine=None):
    """Trả về dict: ok (bool), reason, machine, expires (date|None), issued (date)."""
    res = {"ok": False, "reason": "", "machine": "", "expires": None, "issued": None}
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        from cryptography.exceptions import InvalidSignature
    except ImportError:
        res["reason"] = "Thiếu thư viện 'cryptography'. Hãy chạy lại CAI_DAT.bat."
        return res
    try:
        raw = _unb32(key)
        payload, sig = raw[:-64], raw[-64:]
        if len(raw) <= 64:
            raise ValueError
        Ed25519PublicKey.from_public_bytes(base64.b64decode(PUBLIC_KEY_B64)).verify(sig, payload)
    except InvalidSignature:
        res["reason"] = "Key không hợp lệ (sai chữ ký)."
        return res
    except Exception:
        res["reason"] = "Key không đúng định dạng. Hãy dán lại đầy đủ Key."
        return res
    try:
        m, exp, issued, edition = payload.decode().split("|")
        res["machine"] = m
        res["issued"] = datetime.datetime.strptime(issued, "%Y%m%d").date()
        res["expires"] = None if exp == FOREVER else datetime.datetime.strptime(exp, "%Y%m%d").date()
    except Exception:
        res["reason"] = "Key không đúng định dạng."
        return res
    if edition != "PRO":
        res["reason"] = "Key không dành cho bản PRO."
        return res
    if m != (machine or machine_code()):
        res["reason"] = f"Key này cấp cho máy khác ({m}), không dùng được trên máy này."
        return res
    if res["expires"] and datetime.date.today() > res["expires"]:
        res["reason"] = f"Key đã hết hạn ngày {res['expires']:%d/%m/%Y}."
        return res
    res["ok"] = True
    return res


class License:
    """Trạng thái bản quyền của ứng dụng (đọc từ ban_quyen.json)."""

    def __init__(self):
        self.key = ""
        self.info = {"ok": False, "reason": "Chưa kích hoạt"}
        try:
            with open(LICENSE_FILE, encoding="utf-8") as f:
                self.key = json.load(f).get("key", "")
        except Exception:
            self.key = ""
        if self.key:
            self.info = check_key(self.key)

    @property
    def is_pro(self):
        return bool(self.info.get("ok"))

    @property
    def edition(self):
        return "PRO" if self.is_pro else "Standard"

    def expiry_text(self):
        if not self.is_pro:
            return ""
        exp = self.info.get("expires")
        if not exp:
            return "Vĩnh viễn"
        days = (exp - datetime.date.today()).days
        return f"đến {exp:%d/%m/%Y} (còn {days} ngày)"

    def activate(self, key):
        info = check_key(key)
        if info["ok"]:
            self.key, self.info = key.strip(), info
            with open(LICENSE_FILE, "w", encoding="utf-8") as f:
                json.dump({"key": self.key, "activated": f"{datetime.datetime.now():%d/%m/%Y %H:%M}"}, f)
        return info

    def deactivate(self):
        self.key, self.info = "", {"ok": False, "reason": "Chưa kích hoạt"}
        try:
            os.remove(LICENSE_FILE)
        except OSError:
            pass


LICENSE = None


def get():
    global LICENSE
    if LICENSE is None:
        LICENSE = License()
    return LICENSE


def is_pro():
    return get().is_pro
