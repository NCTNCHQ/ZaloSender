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


def step(n, text):
    print(f"\n[{n}/4] {text}")


def main():
    print("=" * 60)
    print(f"  CÀI ĐẶT: {APP_NAME} – v{APP_VERSION}")
    print("=" * 60)

    step(1, "Kiểm tra Python...")
    print(f"   Python {sys.version.split()[0]} — OK")
    try:
        import tkinter  # noqa: F401
    except ImportError:
        print("   ❌ Python thiếu thành phần 'tcl/tk'. Hãy cài lại Python từ python.org (để mặc định các tùy chọn).")
        return 1

    step(2, "Kiểm tra Google Chrome...")
    while not find_chrome():
        print("   ❌ Chưa có Google Chrome. Đang mở trang tải Chrome:", CHROME_URL)
        webbrowser.open(CHROME_URL)
        ans = input("   Cài Chrome xong thì nhấn Enter để kiểm tra lại (gõ B rồi Enter để bỏ qua): ").strip().lower()
        if ans == "b":
            print("   ⚠ Bỏ qua. Ứng dụng sẽ không gửi được tin khi chưa có Chrome.")
            break
    else:
        print("   Google Chrome — OK")

    step(3, "Cài thư viện (cần Internet, có thể mất vài phút)...")
    r = subprocess.call([sys.executable, "-m", "pip", "install", "--disable-pip-version-check", "-q",
                         "-r", os.path.join(BASE, "requirements.txt")])
    if r != 0:
        print("   ❌ Cài thư viện thất bại. Kiểm tra kết nối Internet rồi chạy lại CAI_DAT.bat.")
        return 1
    print("   Thư viện — OK")

    step(4, "Tạo biểu tượng trên Desktop...")
    pyw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    if not os.path.isfile(pyw):
        pyw = sys.executable

    ok, where = create_shortcut(pyw)
    if ok:
        print(f"   Đã tạo biểu tượng '{where}' trên Desktop — OK")
    else:
        print("   ⚠ Không tạo được biểu tượng:", where)
        print("     Bạn vẫn mở ứng dụng bằng file chay_ung_dung.bat")

    print("\n✅ CÀI ĐẶT HOÀN TẤT!")
    if input("Mở ứng dụng ngay bây giờ? (C/K): ").strip().lower() in ("c", "co", "có", "y", ""):
        subprocess.Popen([pyw, os.path.join(BASE, "app.py")], cwd=BASE)
    return 0


if __name__ == "__main__":
    try:
        code = main()
    except KeyboardInterrupt:
        code = 1
    sys.exit(code)
