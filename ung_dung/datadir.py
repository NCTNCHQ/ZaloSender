"""v1.9.1: Thư mục DỮ LIỆU cố định, tách khỏi thư mục ứng dụng.

Windows: %APPDATA%\\ZaloSender  (vd C:\\Users\\<tên>\\AppData\\Roaming\\ZaloSender)
-> cài lại / chuyển thư mục / cập nhật bản mới đều KHÔNG mất dữ liệu (Key PRO, mẫu tin, ghép nhóm, đã gửi, đăng nhập Zalo).
"""
import os
import shutil

APP_DIR = os.path.dirname(os.path.abspath(__file__))


def _data_dir():
    env = os.environ.get("ZALOSENDER_DATA")  # dùng khi kiểm thử
    if env:
        return env
    base = os.environ.get("APPDATA") or os.path.join(os.path.expanduser("~"), ".config")
    return os.path.join(base, "ZaloSender")


DATA_DIR = _data_dir()
os.makedirs(DATA_DIR, exist_ok=True)

# Các file / thư mục dữ liệu (trước v1.9.1 nằm trong thư mục ứng dụng)
DATA_ITEMS = ["ban_quyen.json", "cai_dat_ung_dung.json", "mau_tin_nhan.json", "ghep_nhom.json",
              "nhom_zalo.json", "ban_be_zalo.json", "bo_nho_dem", "ket_qua", "chan_doan", "zalo_profile"]


def path(*parts):
    return os.path.join(DATA_DIR, *parts)


def migrate_old_data(log=print):
    """Chép dữ liệu cũ (nếu có) từ thư mục ứng dụng sang thư mục dữ liệu. Không ghi đè dữ liệu đã có."""
    moved = []
    for name in DATA_ITEMS:
        old, new = os.path.join(APP_DIR, name), path(name)
        if not os.path.exists(old) or os.path.exists(new):
            continue
        try:
            if os.path.isdir(old):
                shutil.copytree(old, new, ignore=shutil.ignore_patterns("Singleton*", "*.lock", "lockfile"))
            else:
                shutil.copy2(old, new)
            moved.append(name)
        except Exception as e:  # vd: Chrome đang mở hồ sơ zalo_profile
            log(f"Không chép được {name}: {e}")
    if moved:
        try:
            with open(os.path.join(APP_DIR, "DU_LIEU_DA_CHUYEN.txt"), "w", encoding="utf-8") as f:
                f.write("Từ v1.9.1, dữ liệu của ứng dụng được lưu ở:\n" + DATA_DIR + "\n\n"
                        "Đã chép sang: " + ", ".join(moved) + "\n"
                        "Các file cũ trong thư mục này không còn được dùng, có thể xóa.\n")
        except Exception:
            pass
    return moved
