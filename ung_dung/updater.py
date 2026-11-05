"""v1.10: Cập nhật phiên bản mới qua GitHub Releases.

- Ứng dụng đọc file phien_ban.json ở bản phát hành MỚI NHẤT:
  https://github.com/NCTNCHQ/ZaloSender/releases/latest/download/phien_ban.json
- File có CHỮ KÝ SỐ (Ed25519, cùng cặp khóa với Key PRO): chỉ bản do tác giả phát hành mới được cài.
- File zip tải về phải đúng mã SHA-256 ghi trong phien_ban.json.
- Việc thay file do cap_nhat.py làm SAU KHI ứng dụng đã đóng (sao lưu, thay, cài thư viện, mở lại, lỗi thì quay về).
"""
import base64
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request

import datadir
import license as lic
from version import APP_VERSION

REPO = "NCTNCHQ/ZaloSender"
MANIFEST_URL = f"https://github.com/{REPO}/releases/latest/download/phien_ban.json"
RELEASES_PAGE = f"https://github.com/{REPO}/releases"
APP_DIR = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "ZaloSender-Updater"}


def vtuple(v):
    """'1.10' -> (1, 10); '1.9.1' -> (1, 9, 1). So sánh đúng: 1.10 > 1.9.1."""
    return tuple(int(x) for x in re.findall(r"\d+", str(v or "0")))


def is_newer(remote, local=APP_VERSION):
    return vtuple(remote) > vtuple(local)


def canonical(data):
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def verify_manifest(manifest):
    """Trả về dữ liệu phiên bản nếu chữ ký hợp lệ, nếu không -> ValueError."""
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    from cryptography.exceptions import InvalidSignature
    data, sig = manifest.get("data"), manifest.get("sig", "")
    if not isinstance(data, dict) or not sig:
        raise ValueError("File phiên bản không đúng định dạng")
    try:
        Ed25519PublicKey.from_public_bytes(base64.b64decode(lic.PUBLIC_KEY_B64)).verify(
            base64.b64decode(sig), canonical(data))
    except (InvalidSignature, ValueError):
        raise ValueError("Chữ ký số của bản cập nhật KHÔNG hợp lệ — đã từ chối (có thể bị giả mạo)")
    for k in ("version", "url", "sha256"):
        if not data.get(k):
            raise ValueError(f"File phiên bản thiếu '{k}'")
    if not str(data["url"]).startswith("https://"):
        raise ValueError("Đường dẫn tải không an toàn")
    return data


def fetch_json(url=None, timeout=8):
    req = urllib.request.Request(url or MANIFEST_URL, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def check(timeout=8):
    """Trả về dict thông tin bản mới (đã kiểm chữ ký) hoặc None nếu đang dùng bản mới nhất.
    Lỗi mạng / chưa có bản phát hành -> ném lỗi (người gọi tự xử lý im lặng hoặc báo)."""
    data = verify_manifest(fetch_json(timeout=timeout))
    return data if is_newer(data["version"]) else None


def download(data, progress=lambda done, total: None, should_stop=lambda: False):
    """Tải file zip về thư mục tạm, kiểm SHA-256. Trả về đường dẫn file zip."""
    folder = datadir.path("tai_ve")
    os.makedirs(folder, exist_ok=True)
    dest = os.path.join(folder, os.path.basename(data["url"].split("?")[0]) or "cap_nhat.zip")
    h = hashlib.sha256()
    req = urllib.request.Request(data["url"], headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r, open(dest + ".part", "wb") as f:
        total = int(r.headers.get("Content-Length") or 0)
        done = 0
        while True:
            if should_stop():
                raise RuntimeError("Đã hủy tải")
            chunk = r.read(64 * 1024)
            if not chunk:
                break
            f.write(chunk)
            h.update(chunk)
            done += len(chunk)
            progress(done, total)
    if h.hexdigest().lower() != str(data["sha256"]).lower():
        os.remove(dest + ".part")
        raise ValueError("File tải về bị sai (mã SHA-256 không khớp) — đã hủy cập nhật")
    os.replace(dest + ".part", dest)
    return dest


def launch_installer(zip_path, new_version):
    """Chép cap_nhat.py ra thư mục tạm (để nó tự thay được chính nó) rồi chạy; ứng dụng phải thoát ngay sau đó."""
    tmp = os.path.join(tempfile.gettempdir(), "zalosender_cap_nhat.py")
    shutil.copy2(os.path.join(APP_DIR, "cap_nhat.py"), tmp)
    py = sys.executable
    pyw = os.path.join(os.path.dirname(py), "pythonw.exe")
    if sys.platform.startswith("win") and os.path.isfile(pyw):
        py = pyw
    args = [py, tmp, "--zip", zip_path, "--app", APP_DIR, "--pid", str(os.getpid()),
            "--old", APP_VERSION, "--new", str(new_version), "--data", datadir.DATA_DIR, "--python", sys.executable]
    flags = 0x00000008 if sys.platform.startswith("win") else 0  # DETACHED_PROCESS
    return subprocess.Popen(args, cwd=tempfile.gettempdir(), creationflags=flags, close_fds=True,
                            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
