"""Đóng gói thư mục ung_dung/ thành phat_hanh/v<số>/ZaloSender_v<số>.zip và tạo phien_ban.json ký số.

    python cong_cu_tac_gia/dong_goi.py --notes-file co_gi_moi.txt [--required] [--key duong_dan/khoa_bi_mat.pem]

Số phiên bản lấy từ ung_dung/version.py. Cần khoa_bi_mat.pem (KHÔNG có trong kho — tác giả cung cấp).
"""
import argparse
import os
import re
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, "ung_dung")
SKIP_DIRS = {"__pycache__", "zalo_profile", "ket_qua", "chan_doan", "bo_nho_dem"}
SKIP_FILES = {"nhom_zalo.json", "ban_be_zalo.json", "loi.txt", "cai_dat_ung_dung.json", "ghep_nhom.json",
              "mau_tin_nhan.json", "ban_quyen.json", "DU_LIEU_DA_CHUYEN.txt"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--notes-file", required=True)
    ap.add_argument("--required", action="store_true")
    ap.add_argument("--key", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "khoa_bi_mat.pem"))
    a = ap.parse_args()
    ver = re.search(r'APP_VERSION\s*=\s*"([^"]+)"', open(os.path.join(APP, "version.py"), encoding="utf-8").read()).group(1)
    out_dir = os.path.join(ROOT, "phat_hanh", f"v{ver}")
    os.makedirs(out_dir, exist_ok=True)
    zp = os.path.join(out_dir, f"ZaloSender_v{ver}.zip")
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(APP):
            dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
            for f in sorted(files):
                if f in SKIP_FILES or f.endswith((".pem", ".tmp", ".pyc")):
                    continue
                p = os.path.join(root, f)
                z.write(p, os.path.join(f"ZaloSender_v{ver}", os.path.relpath(p, APP)))
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import phat_hanh
    phat_hanh.KEY_FILE = a.key
    path, m = phat_hanh.write_manifest(zp, open(a.notes_file, encoding="utf-8").read(), a.required, out_dir)
    print(f"Đã tạo {zp}\nĐã tạo {path} (v{ver}, sha256 {m['data']['sha256'][:16]}...)")


if __name__ == "__main__":
    main()
