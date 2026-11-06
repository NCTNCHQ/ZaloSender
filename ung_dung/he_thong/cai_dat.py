"""Trình cài đặt: kiểm tra Chrome, cài thư viện, tạo biểu tượng trên Desktop.
(Được gọi từ CAI_DAT.bat sau khi đã tìm thấy Python.)"""
import os
import shutil
import subprocess
import tempfile
import sys
import webbrowser

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
from version import APP_NAME, APP_VERSION  # noqa: E402

CHROME_URL = "https://www.google.com/chrome/"
SHORTCUT_NAME = "Gửi tin Zalo"        # tên hiển thị (có dấu)
SHORTCUT_ASCII = "Gui tin Zalo"       # tên tạm (không dấu) vì WScript.Shell không lưu được tên có dấu


def find_chrome():
    paths = [
        os.path.join(os.environ[v], "Google", "Chrome", "Application", "chrome.exe")
        for v in ("ProgramFiles", "ProgramFiles(x86)", "LocalAppData") if os.environ.get(v)
    ]
    return next((p for p in paths if os.path.isfile(p)), None)


def create_shortcut(pyw, icon=None):
    """WScript.Shell không lưu được file .lnk có dấu tiếng Việt trong tên/đường dẫn.
    Cách làm: tạo shortcut tên KHÔNG dấu ở thư mục tạm, rồi Python chuyển ra Desktop
    và đổi sang tên CÓ dấu. Trả về (thành_công, tên_hoặc_lỗi)."""
    def q(s):  # thoát dấu ' cho PowerShell
        return s.replace("'", "''")

    tmp = os.path.join(tempfile.gettempdir(), SHORTCUT_ASCII + ".lnk")
    ps = (
        "[Console]::OutputEncoding=[Text.Encoding]::UTF8;"
        f"$s=(New-Object -ComObject WScript.Shell).CreateShortcut('{q(tmp)}');"
        f"$s.TargetPath='{q(pyw)}';"
        f"$s.Arguments='\"{q(os.path.join(BASE, 'app.py'))}\"';"
        f"$s.WorkingDirectory='{q(BASE)}';"
        f"$s.IconLocation='{q(icon or os.path.join(BASE, 'icon.ico'))},0';"
        f"$s.Description='Zalo Sender v{APP_VERSION}';"
        "$s.Save();"
        "Write-Output ([Environment]::GetFolderPath('Desktop'))"
    )
    r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
                       capture_output=True)
    out = r.stdout.decode("utf-8", "replace").strip().splitlines()
    desktop = out[-1].strip() if out else ""
    if r.returncode != 0 or not os.path.isfile(tmp):
        return False, (r.stderr.decode("utf-8", "replace").strip().splitlines() or ["không rõ lỗi"])[0]
    if not os.path.isdir(desktop):
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    for name in (SHORTCUT_NAME, SHORTCUT_ASCII):  # ưu tiên tên có dấu, lỗi thì dùng tên không dấu
        final = os.path.join(desktop, name + ".lnk")
        try:
            if os.path.exists(final):
                os.remove(final)  # bản cũ
            shutil.move(tmp, final)
            if name == SHORTCUT_NAME:  # xóa shortcut không dấu còn sót từ lần cài trước
                old = os.path.join(desktop, SHORTCUT_ASCII + ".lnk")
                if os.path.exists(old):
                    os.remove(old)
            return True, name
        except OSError as e:
            err = str(e)
    return False, err


# v1.11: cửa sổ cài đặt có màu, các bước rõ ràng
if sys.platform.startswith("win"):
    os.system("")  # bật màu (ANSI) cho cửa sổ cmd trên Windows 10/11
G, R, Y, C, B, W, X = "\033[92m", "\033[91m", "\033[93m", "\033[96m", "\033[1m", "\033[97m", "\033[0m"


def step(n, text):
    print(f"\n{C}{B}  BƯỚC {n}/4 ▸ {text}{X}")


def ok(text):
    print(f"{G}     ✔ {text}{X}")


def bad(text):
    print(f"{R}     ✖ {text}{X}")


def warn(text):
    print(f"{Y}     ⚠ {text}{X}")


def main():
    line = "═" * 62
    print(f"{B}{W}{line}")
    print(f"     CÀI ĐẶT ỨNG DỤNG: {APP_NAME.upper()}")
    print(f"     Phiên bản v{APP_VERSION}   •   Tác giả: Nguyễn Công Trung")
    print(f"{line}{X}")
    print("  Cửa sổ này sẽ tự làm 4 bước. Bạn chỉ cần làm theo chữ màu VÀNG (nếu có).")

    step(1, "Kiểm tra Python")
    try:
        import tkinter  # noqa: F401
    except ImportError:
        bad("Python thiếu thành phần 'tcl/tk'. Hãy cài lại Python từ python.org (để mặc định các tùy chọn).")
        return 1
    ok(f"Python {sys.version.split()[0]}")

    step(2, "Kiểm tra trình duyệt Google Chrome")
    while not find_chrome():
        bad("Máy chưa có Google Chrome. Đang mở trang tải Chrome: " + CHROME_URL)
        webbrowser.open(CHROME_URL)
        ans = input(f"{Y}     ⚠ Cài Chrome xong thì nhấn ENTER để kiểm tra lại (gõ B rồi Enter để bỏ qua): {X}").strip().lower()
        if ans == "b":
            warn("Đã bỏ qua. Ứng dụng sẽ KHÔNG gửi được tin khi chưa có Chrome.")
            break
    else:
        ok("Đã có Google Chrome")

    step(3, "Cài thư viện cần thiết (cần Internet, có thể mất vài phút — vui lòng chờ)")
    r = subprocess.call([sys.executable, "-m", "pip", "install", "--disable-pip-version-check", "-q",
                         "-r", os.path.join(BASE, "requirements.txt")])
    if r != 0:
        bad("Cài thư viện thất bại. Kiểm tra Internet rồi bấm đúp lại file  1-CAI DAT (bam dup vao day).")
        return 1
    ok("Đã cài đủ thư viện")

    step(4, "Tạo biểu tượng trên màn hình Desktop")
    pyw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    if not os.path.isfile(pyw):
        pyw = sys.executable
    done, where = create_shortcut(pyw)
    if done:
        ok(f"Đã tạo biểu tượng  «{where}»  trên Desktop")
    else:
        warn(f"Không tạo được biểu tượng ({where}).")
        warn("Bạn vẫn mở ứng dụng bằng file  2-MO UNG DUNG  trong thư mục cài.")

    print(f"\n{G}{B}{line}")
    print("     ✅  CÀI ĐẶT XONG!")
    print("     Từ nay: bấm đúp biểu tượng  «Gửi tin Zalo»  trên Desktop để dùng.")
    print(f"{line}{X}")
    if input("\n  Mở ứng dụng ngay bây giờ? (C = có / K = không): ").strip().lower() in ("c", "co", "có", "y", ""):
        subprocess.Popen([pyw, os.path.join(BASE, "app.py")], cwd=BASE)
    return 0


if __name__ == "__main__":
    try:
        code = main()
    except KeyboardInterrupt:
        code = 1
    sys.exit(code)
