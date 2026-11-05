"""Trình cài bản cập nhật — chạy ĐỘC LẬP sau khi ứng dụng đã đóng (được chép ra thư mục tạm trước khi chạy).

1. Đợi ứng dụng cũ thoát hẳn.
2. Giải nén bản mới, SAO LƯU bản cũ vào <thư mục dữ liệu>/ban_cu/v<bản cũ>.
3. Chép bản mới đè lên thư mục ứng dụng; cài thêm thư viện nếu requirements.txt thay đổi.
4. Mở bản mới và chờ bản mới báo "khởi động thành công" (file khoi_dong_ok.json).
5. Nếu bản mới không mở được -> CHÉP LẠI BẢN CŨ, mở lại bản cũ và báo lỗi.
"""
import argparse
import datetime
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile

SKIP = {"__pycache__", "zalo_profile", "bo_nho_dem", "ket_qua", "chan_doan"}  # dữ liệu cũ (trước v1.9.1)


def main():
    ap = argparse.ArgumentParser()
    for a in ("--zip", "--app", "--pid", "--old", "--new", "--data", "--python"):
        ap.add_argument(a, required=True)
    ap.add_argument("--wait", type=int, default=40, help="số giây chờ bản mới báo khởi động thành công")
    a = ap.parse_args()
    log_path = os.path.join(a.data, "cap_nhat.log")

    def log(msg):
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.datetime.now():%d/%m/%Y %H:%M:%S}] {msg}\n")

    def popup(title, text):
        if sys.platform.startswith("win"):
            try:
                import ctypes
                ctypes.windll.user32.MessageBoxW(0, text, title, 0x40 | 0x40000)
                return
            except Exception:
                pass
        print(f"{title}: {text}")

    pyw = os.path.join(os.path.dirname(a.python), "pythonw.exe")
    gui_python = pyw if sys.platform.startswith("win") and os.path.isfile(pyw) else a.python
    marker = os.path.join(a.data, "khoi_dong_ok.json")

    def start_app():
        try:
            os.remove(marker)
        except OSError:
            pass
        return subprocess.Popen([gui_python, os.path.join(a.app, "app.py")], cwd=a.app, stdin=subprocess.DEVNULL,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def started_ok(proc, version):
        deadline = time.time() + a.wait
        while time.time() < deadline:
            try:
                with open(marker, encoding="utf-8") as f:
                    if json.load(f).get("version") == version:
                        return True
            except Exception:
                pass
            if proc.poll() is not None:
                return False
            time.sleep(0.5)
        return False

    def copy_tree(src, dst):
        for root, dirs, files in os.walk(src):
            dirs[:] = [d for d in dirs if d not in SKIP]
            rel = os.path.relpath(root, src)
            os.makedirs(os.path.join(dst, rel), exist_ok=True)
            for fn in files:
                shutil.copy2(os.path.join(root, fn), os.path.join(dst, rel, fn))

    log(f"=== Cập nhật v{a.old} -> v{a.new} ===")
    # 1. đợi ứng dụng cũ thoát
    pid = int(a.pid)
    if sys.platform.startswith("win"):
        try:
            import ctypes
            h = ctypes.windll.kernel32.OpenProcess(0x00100000, False, pid)  # SYNCHRONIZE
            if h:
                ctypes.windll.kernel32.WaitForSingleObject(h, 60000)
                ctypes.windll.kernel32.CloseHandle(h)
        except Exception:
            time.sleep(3)
    else:
        for _ in range(120):
            try:
                os.kill(pid, 0)
                time.sleep(0.5)
            except OSError:
                break
    time.sleep(1)

    # 2. giải nén + sao lưu
    work = tempfile.mkdtemp(prefix="zalosender_moi_")
    backup = os.path.join(a.data, "ban_cu", f"v{a.old}")
    try:
        with zipfile.ZipFile(a.zip) as z:
            z.extractall(work)
        new_root = next((r for r, d, f in os.walk(work) if "app.py" in f and "version.py" in f), None)
        if not new_root:
            raise RuntimeError("File cập nhật không chứa ứng dụng (thiếu app.py)")
        shutil.rmtree(backup, ignore_errors=True)
        copy_tree(a.app, backup)
        log(f"Đã sao lưu bản cũ vào {backup}")
    except Exception as e:
        log(f"LỖI chuẩn bị: {e}")
        popup("Cập nhật thất bại", f"Không cập nhật được: {e}\nỨng dụng vẫn giữ bản v{a.old}.")
        start_app()
        return 1

    # 3. chép bản mới + thư viện
    try:
        def req(p):
            try:
                with open(os.path.join(p, "requirements.txt"), encoding="utf-8") as f:
                    return f.read()
            except OSError:
                return ""
        need_pip = req(new_root) != req(a.app)
        copy_tree(new_root, a.app)
        log("Đã chép bản mới")
        if need_pip:
            log("Đang cài thư viện mới...")
            flags = 0x08000000 if sys.platform.startswith("win") else 0  # CREATE_NO_WINDOW
            r = subprocess.run([a.python, "-m", "pip", "install", "-q", "--disable-pip-version-check",
                                "-r", os.path.join(a.app, "requirements.txt")], creationflags=flags,
                               capture_output=True, text=True)
            log(f"pip -> mã {r.returncode} {r.stderr[-300:] if r.returncode else ''}")
    except Exception as e:
        log(f"LỖI chép bản mới: {e} -> quay về bản cũ")
        copy_tree(backup, a.app)
        popup("Cập nhật thất bại", f"Lỗi khi chép bản mới: {e}\nĐã quay về bản v{a.old}.")
        start_app()
        return 1

    # 4. mở bản mới, 5. lỗi thì quay về
    proc = start_app()
    if started_ok(proc, a.new):
        log(f"✅ Bản v{a.new} đã khởi động thành công")
        shutil.rmtree(work, ignore_errors=True)
        try:
            os.remove(a.zip)
        except OSError:
            pass
        return 0
    log(f"❌ Bản v{a.new} không khởi động được -> quay về v{a.old}")
    try:
        if proc.poll() is None:
            proc.kill()
    except Exception:
        pass
    copy_tree(backup, a.app)
    start_app()
    popup("Cập nhật chưa thành công",
          f"Bản v{a.new} không mở được trên máy này nên ứng dụng đã TỰ QUAY VỀ bản v{a.old}.\n"
          f"Chi tiết: {log_path}\nHãy gửi file này cho tác giả: Congtrung127@gmail.com")
    return 2


if __name__ == "__main__":
    sys.exit(main())
