"""Điều khiển Zalo Web (https://chat.zalo.me) bằng Playwright + Google Chrome có sẵn trên máy.

Trình duyệt dùng một thư mục hồ sơ riêng (zalo_profile/) nên chỉ cần quét QR đăng nhập lần đầu.
Giao diện Zalo có thể thay đổi theo thời gian -> chỉnh các bộ chọn (selector) trong config.json.
"""
import json
import os
import re
import time
import unicodedata
from collections import Counter

from playwright.sync_api import TimeoutError as PWTimeout
from playwright.sync_api import sync_playwright

import core

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
import datadir  # noqa: E402

PROFILE_DIR = datadir.path("zalo_profile")
ZALO_URL = "https://chat.zalo.me/"

DEFAULT_SELECTORS = {
    # Ô tìm kiếm ở cột bên trái
    "search_input": "#contact-search-input",
    # Kết quả tìm kiếm (thử lần lượt từng bộ chọn)
    "search_result": [
        "#global_search_list .gridv2",
        "[id^='friend-item']",
        "#global_search_list [data-id]",
        ".global-search .conv-item",
    ],
    "no_result_text": ["Không tìm thấy", "Số điện thoại chưa đăng ký", "not found"],
    # Ô soạn tin nhắn
    "message_input": "#richInput",
    # Tiêu đề cuộc trò chuyện đang mở (để kiểm tra mở đúng người / đúng nhóm)
    "chat_title": ["#header .header-title", ".chat-header .title", "header .truncate"],
    # Đính kèm file
    "attach_button": ["[title*='Đính kèm File']", "[title*='Attach file']", "[data-translate-title*='ATTACH']"],
    "attach_menu_text": r"^(Chọn File|Chọn tệp|Choose file)",
    "file_needs_enter": False,
    # Lấy danh sách nhóm
    "messages_tab": ["[title='Tin nhắn']", "[title='Messages']", "[data-translate-title='STR_TAB_MESSAGE']"],
    "contacts_tab": ["[title='Danh bạ']", "[title='Contacts']", "[data-translate-title='STR_TAB_CONTACT']"],
    "group_list_text": r"^(Danh sách nhóm|Group list)",
    "group_member_regex": r"^\d[\d.,]*\+?\s*(thành viên|members?)$",
    "friend_list_text": r"^(Danh sách bạn bè|Friend list|Friends list)",
    "friend_total_regex": r"Bạn bè\s*\((\d+)\)|Friends\s*\((\d+)\)",
    "friend_header_regex": r"^(Bạn mới|New friends|[A-ZĐ#]|0-9)$",
    "friend_skip_text": ["Bạn mới", "New friends", "Tìm bạn", "Danh sách bạn bè", "Tên (A-Z)", "Tất cả"],
    "group_total_regex": r"(Nhóm và cộng đồng|Nhóm|Groups?[^()]*)\s*\((\d+)\)",
}


def load_selectors():
    sel = dict(DEFAULT_SELECTORS)
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, encoding="utf-8") as f:
                sel.update(json.load(f).get("selectors", {}))
        except Exception:
            pass
    return sel


class ZaloError(Exception):
    pass


class ZaloAmbiguous(ZaloError):
    """Có nhiều người/nhóm trùng tên -> DỪNG, không thử cách khác (tránh gửi nhầm người)."""


# Nhận diện dòng "96 thành viên" (chuẩn hóa Unicode NFC vì chữ tiếng Việt có thể mã hóa kiểu tổ hợp),
# lấy phần tử SÂU NHẤT chứa đúng dòng đó, rồi lấy tên nhóm là dòng NGAY PHÍA TRÊN
# (bỏ qua các dòng chỉ có số như "12", "5" in trên ảnh đại diện).
_JS_HELPERS = r"""
  const norm = s => (s || '').normalize('NFC').replace(/\s+/g, ' ').trim();
  const re = new RegExp(pattern.normalize('NFC'), 'iu');
  const memberEls = () => {
    const res = [];
    for (const el of document.querySelectorAll('body *')) {
      const t = norm(el.textContent);
      if (!t || t.length > 40 || !re.test(t)) continue;
      if ([...el.children].some(c => re.test(norm(c.textContent)))) continue;
      res.push(el);
    }
    return res;
  };
"""

_JS_COLLECT_GROUPS = "(pattern) => {" + _JS_HELPERS + r"""
  const out = [];
  for (const el of memberEls()) {
    let row = el.parentElement;
    for (let i = 0; i < 6 && row; i++) {
      const lines = (row.innerText || '').split('\n').map(norm).filter(Boolean);
      const k = lines.findIndex(l => re.test(l));
      let name = null;
      for (let j = k - 1; j >= 0; j--) {
        if (!/^[\d+.,]+$/.test(lines[j]) && !re.test(lines[j])) { name = lines[j]; break; }
      }
      if (name) { out.push({name: name, members: lines[k]}); break; }
      row = row.parentElement;
    }
  }
  return out;
}"""

_JS_SCROLL_GROUPS = "(pattern) => {" + _JS_HELPERS + r"""
  const els = memberEls();
  if (!els.length) return false;
  let p = els[els.length - 1].parentElement;
  while (p && !(p.scrollHeight > p.clientHeight + 5 && /(auto|scroll)/.test(getComputedStyle(p).overflowY)))
    p = p.parentElement;
  if (!p) return false;
  const before = p.scrollTop;
  p.scrollTop = before + p.clientHeight * 0.8;
  return p.scrollTop > before;
}"""


_JS_MARK_TEXT = r"""(args) => {
  const norm = s => (s || '').normalize('NFC').replace(/\s+/g, ' ').trim().toLowerCase();
  const t = norm(args.target);
  const inp = document.querySelector(args.searchSel);
  const sr = inp ? inp.getBoundingClientRect() : {left: 0, right: 380, bottom: 0};
  document.querySelectorAll('[data-zs-hit]').forEach(e => e.removeAttribute('data-zs-hit'));
  const hits = [];
  for (const el of document.querySelectorAll('body *')) {
    if (/^(INPUT|TEXTAREA|SCRIPT|STYLE)$/.test(el.tagName)) continue;
    if (norm(el.textContent) !== t) continue;
    if ([...el.children].some(c => norm(c.textContent) === t)) continue;  // lấy phần tử sâu nhất
    const r = el.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) continue;
    const cs = getComputedStyle(el);
    if (cs.visibility === 'hidden' || cs.display === 'none' || cs.opacity === '0') continue;
    let ok = false;
    if (args.area === 'left') ok = r.left < sr.right + 30 && r.top > sr.bottom - 5;
    else if (args.area === 'right') ok = r.left > sr.right + 20 && r.top > 120;
    else if (args.area === 'header') ok = r.left > sr.right + 20 && r.top < 230;
    if (ok) hits.push({el: el, top: r.top});
  }
  hits.sort((a, b) => a.top - b.top);
  if (hits.length) hits[0].el.setAttribute('data-zs-hit', '1');
  return hits.length;
}"""

_JS_FRIEND_SNAPSHOT = r"""(args) => {
  const norm = s => (s || '').normalize('NFC').replace(/\s+/g, ' ').trim();
  const inp = document.querySelector(args.searchSel);
  const sr = inp ? inp.getBoundingClientRect() : {right: 380};
  // khung danh sách = phần tử cuộn được lớn nhất ở bên phải
  let box = null;
  for (const el of document.querySelectorAll('div,ul,section')) {
    const r = el.getBoundingClientRect();
    if (r.left <= sr.right + 20 || r.width < 200) continue;
    const cs = getComputedStyle(el);
    if (!/(auto|scroll)/.test(cs.overflowY) || el.scrollHeight <= el.clientHeight + 5) continue;
    if (!box || el.scrollHeight > box.scrollHeight) box = el;
  }
  if (!box) return {ok: false};
  const br = box.getBoundingClientRect();
  const headRe = new RegExp(args.header.normalize('NFC'), 'u');
  const skip = new Set(args.skip.map(norm));
  const rows = [], headers = [];
  for (const el of box.querySelectorAll('*')) {
    if (el.children.length && [...el.children].some(c => norm(c.textContent))) continue;  // chỉ lấy lá có chữ
    const t = norm(el.textContent);
    if (!t || t === '...' || t === '…') continue;
    const r = el.getBoundingClientRect();
    if (r.height <= 0 || r.bottom < br.top || r.top > br.bottom) continue;
    const y = Math.round(box.scrollTop + r.top - br.top);
    if (headRe.test(t)) { headers.push({y: y, text: t}); continue; }
    if (skip.has(t) || /^(Bạn bè|Friends|Nhóm và cộng đồng)\s*\(\d+\)$/i.test(t)) continue;
    // bỏ chữ viết tắt trong ảnh đại diện (ô vuông nhỏ, chữ ngắn)
    if (t.length <= 3 && t === t.toUpperCase() && r.width >= 28 && r.width <= 72 && r.height >= 28 && r.height <= 72
        && Math.abs(r.width - r.height) < 16) continue;
    rows.push({y: y, name: t});
  }
  const before = box.scrollTop;
  box.scrollTop = before + box.clientHeight * 0.7;
  return {ok: true, rows: rows, headers: headers, scrolled: box.scrollTop > before};
}"""

_JS_MARK_LIST_SEARCH = r"""(searchSel) => {
  const inp = document.querySelector(searchSel);
  const sr = inp ? inp.getBoundingClientRect() : {right: 380};
  document.querySelectorAll('[data-zs-input]').forEach(e => e.removeAttribute('data-zs-input'));
  for (const el of document.querySelectorAll('input')) {
    const r = el.getBoundingClientRect();
    if (r.width > 0 && r.height > 0 && r.left > sr.right + 20) { el.setAttribute('data-zs-input', '1'); return true; }
  }
  return false;
}"""


class ZaloWebSender:
    def __init__(self, log=print):
        self.log = log
        self.sel = load_selectors()
        self._pw = None
        self._ctx = None
        self.page = None

    # ---------- vòng đời ----------
    def start(self):
        self._pw = sync_playwright().start()
        try:
            self._ctx = self._pw.chromium.launch_persistent_context(
                PROFILE_DIR,
                channel="chrome",  # dùng Google Chrome đã cài trên máy
                headless=False,
                viewport={"width": 1280, "height": 800},
                locale="vi-VN",
            )
        except Exception as e:
            self._pw.stop()
            self._pw = None
            msg = str(e)
            if "chrome" in msg.lower() and ("not found" in msg.lower() or "distribution" in msg.lower()):
                raise ZaloError("Không tìm thấy Google Chrome. Hãy cài Chrome tại https://www.google.com/chrome/")
            if "user data directory is already in use" in msg.lower() or "lock" in msg.lower():
                raise ZaloError("Cửa sổ Chrome của ứng dụng đang mở. Hãy đóng nó rồi thử lại.")
            raise
        try:  # v1.6: cho phép dán tin nhắn qua bộ nhớ tạm (clipboard)
            self._ctx.grant_permissions(["clipboard-read", "clipboard-write"], origin="https://chat.zalo.me")
        except Exception:
            pass
        self.page = self._ctx.pages[0] if self._ctx.pages else self._ctx.new_page()
        self.page.goto(ZALO_URL)

    def close(self):
        try:
            if self._ctx:
                self._ctx.close()
        finally:
            if self._pw:
                self._pw.stop()

    def wait_for_login(self, timeout_s=300, should_stop=lambda: False):
        """Chờ người dùng quét QR (nếu chưa đăng nhập). Trả về False nếu bị dừng."""
        search = self.page.locator(self.sel["search_input"])
        deadline = time.time() + timeout_s
        told = False
        while time.time() < deadline:
            if should_stop():
                return False
            try:
                if search.is_visible():
                    self.page.wait_for_timeout(1500)
                    return True
            except Exception:
                pass
            if not told:
                self.log("Chưa đăng nhập: hãy quét mã QR trên cửa sổ Chrome bằng app Zalo điện thoại...")
                told = True
            time.sleep(1)
        raise ZaloError("Hết thời gian chờ đăng nhập Zalo.")

    # ---------- tiện ích ----------
    def _visible_all(self, selectors, limit=30):
        if isinstance(selectors, str):
            selectors = [selectors]
        for s in selectors:
            loc = self.page.locator(s)
            try:
                n = loc.count()
            except Exception:
                continue
            items = [loc.nth(i) for i in range(min(n, limit))]
            items = [it for it in items if it.is_visible()]
            if items:
                return items
        return []

    def _visible_first(self, selectors):
        items = self._visible_all(selectors, limit=5)
        return items[0] if items else None

    @staticmethod
    def _first_line(loc):
        try:
            for line in loc.inner_text(timeout=2000).split("\n"):
                if line.strip():
                    return line.strip()
        except Exception:
            pass
        return ""

    def _type_search(self, text):
        page = self.page
        page.keyboard.press("Escape")
        search = page.locator(self.sel["search_input"])
        search.click()
        search.fill("")
        search.type(text, delay=60)
        return search

    def _cancel_search(self, search):
        try:
            search.fill("")
            self.page.keyboard.press("Escape")
        except Exception:
            pass

    def _no_result_shown(self):
        body = self.page.locator("body").inner_text().lower()
        return any(t.lower() in body for t in self.sel["no_result_text"])

    def _wait_message_box(self):
        msg = self.page.locator(self.sel["message_input"])
        try:
            msg.wait_for(state="visible", timeout=8000)
        except PWTimeout:
            raise ZaloError("Không mở được ô soạn tin (có thể nhóm chỉ cho trưởng nhóm nhắn tin)")
        self.page.wait_for_timeout(800)
        return msg

    def _check_title(self, expected_name):
        """Nếu đọc được tiêu đề cuộc trò chuyện thì bắt buộc phải khớp tên."""
        el = self._visible_first(self.sel["chat_title"])
        if not el:
            return
        title = self._first_line(el)
        if title and core.norm_name(title) != core.norm_name(expected_name):
            raise ZaloError(f"Mở nhầm cuộc trò chuyện '{title}' -> đã hủy để tránh gửi nhầm")

    # ---------- mở cuộc trò chuyện ----------
    def open_chat_by_phone(self, phone: str):
        search = self._type_search(phone)
        result, no_hits = None, 0
        for _ in range(16):
            self.page.wait_for_timeout(500)
            result = self._visible_first(self.sel["search_result"])
            if result:
                break
            # chỉ kết luận "không tìm thấy" khi thông báo đó giữ nguyên >= 2 giây
            no_hits = no_hits + 1 if self._no_result_shown() else 0
            if no_hits >= 4:
                break
        if not result:
            self._cancel_search(search)
            # KHÔNG nhấn Enter "đại" để tránh gửi nhầm vào cuộc trò chuyện đang mở
            raise ZaloError("Không tìm thấy tài khoản Zalo của số này")
        self.page.wait_for_timeout(400)
        result.click()
        return self._wait_message_box()

    # ---------- v1.5: tìm theo CHỮ HIỂN THỊ (không phụ thuộc cấu trúc trang Zalo) ----------
    def _mark_text(self, name, area):
        """Đánh dấu phần tử hiển thị có chữ TRÙNG KHỚP HOÀN TOÀN với tên (đã ghép các mảnh tô đậm,
        chuẩn hóa Unicode, không phân biệt hoa thường). area: 'left' = cột kết quả tìm kiếm bên trái,
        'right' = khung bên phải, 'header' = tiêu đề khung chat. Trả về số kết quả khớp."""
        return self.page.evaluate(_JS_MARK_TEXT, {"target": name, "area": area,
                                                  "searchSel": self.sel["search_input"]})

    def _click_marked(self):
        self.page.locator("[data-zs-hit='1']").first.click(force=True, timeout=5000)

    def _header_is(self, name, wait_s=4):
        for _ in range(int(wait_s * 2)):
            if self._mark_text(name, "header"):
                return True
            self.page.wait_for_timeout(500)
        return False

    def _verify_opened(self, name):
        """Kiểm tra trước khi gửi: tiêu đề khung chat phải đúng tên. Không xác minh được -> không gửi."""
        box = self._wait_message_box()
        if self._header_is(name):
            return box
        self._check_title(name)  # đọc được tiêu đề khác tên -> báo "mở nhầm"
        raise ZaloError("Đã bấm vào kết quả nhưng không xác minh được tiêu đề khung chat là '" + name + "'")

    def _goto_messages_tab(self):
        tab = self._visible_first(self.sel["messages_tab"])
        if tab:
            try:
                tab.click(timeout=3000)
                self.page.wait_for_timeout(600)
            except Exception:
                pass

    def _diag(self, tag):
        """Lưu file chẩn đoán (tối đa 3 lần mỗi đợt gửi để không đầy thư mục)."""
        self._diag_count = getattr(self, "_diag_count", 0) + 1
        if self._diag_count <= 3:
            folder = self.save_diagnostics(tag)
            self.log(f"   (đã lưu file chẩn đoán vào {folder})")

    def _open_via_search(self, name):
        self._goto_messages_tab()
        search = self._type_search(name)
        no_hits = 0
        for _ in range(16):
            self.page.wait_for_timeout(500)
            if self._mark_text(name, "left"):
                self.page.wait_for_timeout(300)
                self._mark_text(name, "left")  # đánh dấu lại sau khi danh sách ổn định
                self._click_marked()
                return True
            no_hits = no_hits + 1 if self._no_result_shown() else 0
            if no_hits >= 4:
                break
        self._diag("tim_kiem_khong_thay")
        self._cancel_search(search)
        return False

    def _open_via_friend_list(self, name):
        return self._open_via_group_list(name, self.sel["friend_list_text"])

    def _open_via_group_list(self, name, list_text=None):
        """Dự phòng: Danh bạ -> Danh sách nhóm (hoặc bạn bè) -> ô tìm kiếm của danh sách -> bấm đúng tên.
        Danh sách bạn bè: nếu có >1 người trùng tên khớp -> từ chối (không đoán)."""
        page = self.page
        page.keyboard.press("Escape")
        tab = self._visible_first(self.sel["contacts_tab"])
        if not tab:
            return False
        tab.click()
        page.wait_for_timeout(1200)
        try:
            page.get_by_text(re.compile(list_text or self.sel["group_list_text"], re.I)).first.click(timeout=8000)
        except PWTimeout:
            return False
        page.wait_for_timeout(1500)
        if page.evaluate(_JS_MARK_LIST_SEARCH, self.sel["search_input"]):
            box = page.locator("[data-zs-input='1']").first
            box.click()
            box.fill("")
            box.type(name, delay=50)
        for _ in range(16):
            page.wait_for_timeout(500)
            n = self._mark_text(name, "right")
            if n:
                if list_text and n > 1:
                    page.wait_for_timeout(800)
                    if self._mark_text(name, "right") > 1:
                        raise ZaloAmbiguous(f"Có {n} người trong danh sách bạn bè trùng tên '{name}' — không đoán")
                self._click_marked()
                page.wait_for_timeout(1500)
                return True
        return False

    def open_chat_by_name(self, name: str, kind: str = None):
        """Tìm theo tên Zalo / tên nhóm / tên bạn bè. Chỉ gửi khi tên trùng khớp hoàn toàn VÀ tiêu đề khung chat
        đúng tên. kind: 'nhom' | 'ban' | None (thử cả hai cách dự phòng)."""
        name = " ".join(str(name).split())  # bỏ khoảng trắng thừa
        errors = []
        search = (self._open_via_search, "ô tìm kiếm")
        if kind == "ban":  # bạn bè: đi qua danh sách bạn bè TRƯỚC để phát hiện người trùng tên
            methods = [(self._open_via_friend_list, "danh sách bạn bè"), search]
        elif kind == "nhom":
            methods = [search, (self._open_via_group_list, "danh sách nhóm")]
        else:
            methods = [search, (self._open_via_group_list, "danh sách nhóm"),
                       (self._open_via_friend_list, "danh sách bạn bè")]
        for method, label in methods:
            try:
                if method(name):
                    return self._verify_opened(name)
                errors.append(f"{label}: không thấy tên trùng khớp")
            except ZaloAmbiguous:
                self._goto_messages_tab()
                raise
            except ZaloError as e:
                errors.append(f"{label}: {e}")
            except Exception as e:
                errors.append(f"{label}: {str(e).splitlines()[0][:120]}")
        self._diag("khong_mo_duoc_nhom")
        self._goto_messages_tab()
        raise ZaloError("Không mở được cuộc trò chuyện '" + name + "' (" + "; ".join(errors) + ")")

    # ---------- gửi ----------
    # ---------- v1.6: đưa tin nhắn vào ô soạn tin + KIỂM TRA trước khi gửi ----------
    @staticmethod
    def _lines(text):
        """Các dòng có chữ (bỏ dòng trống, chuẩn hóa Unicode & khoảng trắng) để so sánh."""
        out = []
        for line in unicodedata.normalize("NFC", text or "").replace("\u00a0", " ").splitlines():
            line = " ".join(line.split())
            if line:
                out.append(line)
        return out

    def _composer_text(self):
        try:
            return self.page.locator(self.sel["message_input"]).inner_text(timeout=3000)
        except Exception:
            return ""

    def _clear_composer(self):
        msg = self.page.locator(self.sel["message_input"])
        msg.click()
        for _ in range(3):
            self.page.keyboard.press("Control+A")
            self.page.keyboard.press("Delete")
            self.page.wait_for_timeout(300)
            if not self._lines(self._composer_text()):
                return True
        return False

    def _paste(self, message):
        """Dán cả tin nhắn một lần (giống người dùng nhấn Ctrl+V)."""
        page = self.page
        ok = False
        try:
            page.evaluate("t => navigator.clipboard.writeText(t)", message)
            ok = page.evaluate("() => navigator.clipboard.readText()") == message
        except Exception:
            ok = False
        page.locator(self.sel["message_input"]).click()
        if ok:
            page.keyboard.press("Control+V")
        else:  # không dùng được clipboard -> gửi sự kiện "dán" trực tiếp vào ô soạn tin
            page.evaluate("""([sel, t]) => {
                const el = document.querySelector(sel); el.focus();
                const dt = new DataTransfer(); dt.setData('text/plain', t);
                el.dispatchEvent(new ClipboardEvent('paste', {clipboardData: dt, bubbles: true, cancelable: true}));
            }""", [self.sel["message_input"], message])
        page.wait_for_timeout(1200)

    def _type_slowly(self, message):
        """Dự phòng: gõ từng dòng, chờ Zalo xử lý xong mỗi lần xuống dòng."""
        page = self.page
        page.locator(self.sel["message_input"]).click()
        for i, line in enumerate(message.split("\n")):
            if i:
                page.keyboard.press("Shift+Enter")
                page.wait_for_timeout(350)
            if line:
                page.keyboard.insert_text(line)
                page.wait_for_timeout(250)
        page.wait_for_timeout(800)

    def _matches(self, message):
        return self._lines(self._composer_text()) == self._lines(message)

    def send_text(self, message: str, dry_run=False):
        """Đưa tin nhắn vào ô soạn tin; CHỈ nhấn gửi khi nội dung trong ô khớp từng dòng với tin đã soạn.
        Không khớp -> xóa ô soạn tin và báo lỗi (không gửi gì)."""
        if not self._clear_composer():
            raise ZaloError("Ô soạn tin đang có sẵn nội dung và không xóa được")
        how = None
        for name, method in (("dán", self._paste), ("gõ chậm", self._type_slowly)):
            method(message)
            if self._matches(message):
                how = name
                break
            self._clear_composer()
        if not how:
            got, want = self._lines(self._composer_text()), self._lines(message)
            self._clear_composer()
            raise ZaloError(f"Nội dung trong ô soạn tin không khớp tin đã soạn ({len(want)} dòng) "
                            f"-> KHÔNG gửi để tránh gửi thiếu")
        if dry_run:
            self._clear_composer()
            return how
        self.page.keyboard.press("Enter")
        self.page.wait_for_timeout(1500)
        if self._lines(self._composer_text()):
            raise ZaloError("Đã nhấn gửi nhưng tin nhắn vẫn nằm trong ô soạn tin")
        return how

    def _file_input(self):
        """Tìm ô chọn file ẩn dành cho 'file' (không phải ô chỉ nhận ảnh/video)."""
        inputs = self.page.locator("input[type=file]")
        best = None
        for i in range(inputs.count()):
            inp = inputs.nth(i)
            accept = (inp.get_attribute("accept") or "").lower()
            if not accept or "*/*" in accept or "pdf" in accept or "application" in accept:
                return inp
            if not accept.startswith("image") and best is None:
                best = inp
        return best

    def send_file(self, path: str):
        page = self.page
        inp = self._file_input()
        if inp is not None:
            # xóa lựa chọn cũ: nếu chọn lại đúng file vừa gửi, trình duyệt sẽ không tải lên lần nữa
            inp.evaluate("el => { try { el.value = ''; } catch (e) {} }")
            inp.set_input_files(path)
        else:
            btn = self._visible_first(self.sel["attach_button"])
            if not btn:
                raise ZaloError("Không tìm thấy nút đính kèm file")
            try:
                with page.expect_file_chooser(timeout=3000) as fc:
                    btn.click()
                fc.value.set_files(path)
            except PWTimeout:
                # nút đính kèm mở ra menu -> chọn "Chọn File"
                item = page.get_by_text(re.compile(self.sel["attach_menu_text"], re.I)).first
                with page.expect_file_chooser(timeout=5000) as fc:
                    item.click()
                fc.value.set_files(path)
        if self.sel.get("file_needs_enter"):
            page.wait_for_timeout(1000)
            page.keyboard.press("Enter")
        # chờ tải lên: 3 giây + 1,5 giây/MB (tối đa 90 giây)
        size_mb = os.path.getsize(path) / 1_000_000
        page.wait_for_timeout(int(min(90, 3 + 1.5 * size_mb) * 1000))

    # ---------- lấy danh sách nhóm ----------
    def fetch_groups(self, should_stop=lambda: False):
        page = self.page
        tab = self._visible_first(self.sel["contacts_tab"])
        if not tab:
            raise ZaloError("Không tìm thấy nút 'Danh bạ' trên Zalo Web. Đã lưu file chẩn đoán vào: "
                            + self.save_diagnostics("khong_thay_danh_ba"))
        tab.click()
        page.wait_for_timeout(1500)
        item = page.get_by_text(re.compile(self.sel["group_list_text"], re.I)).first
        try:
            item.click(timeout=8000)
        except PWTimeout:
            raise ZaloError("Không tìm thấy mục 'Danh sách nhóm'. Đã lưu file chẩn đoán vào: "
                            + self.save_diagnostics("khong_thay_danh_sach_nhom"))
        page.wait_for_timeout(2500)

        pattern = self.sel["group_member_regex"]
        # chờ danh sách tải xong (tối đa ~10 giây)
        for _ in range(20):
            if page.evaluate(_JS_COLLECT_GROUPS, pattern):
                break
            page.wait_for_timeout(500)
        total = self._group_total()
        if total:
            self.log(f"Zalo báo có {total} nhóm, đang đọc...")

        groups, stale = {}, 0
        for _ in range(400):
            if should_stop():
                break
            before = len(groups)
            for g in page.evaluate(_JS_COLLECT_GROUPS, pattern):
                groups.setdefault((g["name"], g["members"]), g)
            self.log(f"Đã đọc {len(groups)}{'/' + str(total) if total else ''} nhóm...")
            if total and len(groups) >= total:
                break
            if not page.evaluate(_JS_SCROLL_GROUPS, pattern):
                # dự phòng: cuộn bằng con lăn chuột ở khung danh sách bên phải
                vp = page.viewport_size or {"width": 1280, "height": 800}
                page.mouse.move(vp["width"] * 0.65, vp["height"] * 0.6)
                page.mouse.wheel(0, 500)
            page.wait_for_timeout(700)
            stale = stale + 1 if len(groups) == before else 0
            if stale >= 6:
                break

        result = list(groups.values())
        if not result:
            folder = self.save_diagnostics("khong_doc_duoc_nhom")
            raise ZaloError("Không đọc được nhóm nào. Đã lưu file chẩn đoán vào thư mục: " + folder
                            + " — hãy gửi các file trong đó cho người hỗ trợ.")
        if total and len(result) < total:
            folder = self.save_diagnostics("doc_thieu_nhom")
            self.log(f"⚠ Chỉ đọc được {len(result)}/{total} nhóm. Đã lưu file chẩn đoán: {folder}")
        return result

    def _group_total(self):
        try:
            text = unicodedata.normalize("NFC", self.page.locator("body").inner_text())
            m = re.search(unicodedata.normalize("NFC", self.sel["group_total_regex"]), text, re.I)
            return int(m.group(m.lastindex)) if m else 0
        except Exception:
            return 0

    def save_diagnostics(self, tag):
        """Lưu ảnh chụp màn hình + cấu trúc trang để người hỗ trợ sửa lỗi."""
        folder = datadir.path("chan_doan")
        os.makedirs(folder, exist_ok=True)
        stamp = time.strftime("%Y%m%d_%H%M%S")
        try:
            self.page.screenshot(path=os.path.join(folder, f"{tag}_{stamp}.png"), full_page=False)
        except Exception:
            pass
        try:
            # bỏ các thẻ script/style/ảnh cho gọn, chỉ giữ cấu trúc
            html = self.page.evaluate("""() => {
                const c = document.body.cloneNode(true);
                c.querySelectorAll('script,style,img,svg,canvas,video').forEach(e => e.remove());
                return c.outerHTML; }""")
            with open(os.path.join(folder, f"{tag}_{stamp}.html"), "w", encoding="utf-8") as f:
                f.write(html)
        except Exception:
            pass
        return folder


    # ---------- v1.8: lấy danh sách BẠN BÈ ----------
    def fetch_friends(self, should_stop=lambda: False):
        """Danh bạ -> Danh sách bạn bè. Mỗi dòng: ảnh + tên (không có dòng phụ). Bỏ qua mục 'Bạn mới'
        (bị lặp lại ở mục chữ cái). Định danh mỗi dòng bằng VỊ TRÍ trong danh sách -> phát hiện được 2 người trùng tên."""
        page = self.page
        tab = self._visible_first(self.sel["contacts_tab"])
        if not tab:
            raise ZaloError("Không tìm thấy nút 'Danh bạ'. Đã lưu file chẩn đoán: "
                            + self.save_diagnostics("ban_be_khong_thay_danh_ba"))
        tab.click()
        page.wait_for_timeout(1500)
        try:
            page.get_by_text(re.compile(self.sel["friend_list_text"], re.I)).first.click(timeout=8000)
        except PWTimeout:
            raise ZaloError("Không tìm thấy mục 'Danh sách bạn bè'. Đã lưu file chẩn đoán: "
                            + self.save_diagnostics("ban_be_khong_thay_muc"))
        page.wait_for_timeout(2500)
        args = {"searchSel": self.sel["search_input"], "header": self.sel["friend_header_regex"],
                "skip": self.sel["friend_skip_text"]}
        total = 0
        try:
            text = unicodedata.normalize("NFC", page.locator("body").inner_text())
            m = re.search(self.sel["friend_total_regex"], text, re.I)
            total = int(next(g for g in m.groups() if g)) if m else 0
        except Exception:
            total = 0
        if total:
            self.log(f"Zalo báo có {total} bạn bè, đang đọc...")
        rows, headers, stale = {}, {}, 0
        for _ in range(1500):
            if should_stop():
                break
            snap = page.evaluate(_JS_FRIEND_SNAPSHOT, args)
            if not snap["ok"]:
                break
            before = len(rows)
            for h in snap["headers"]:
                headers[h["y"]] = h["text"]
            for r in snap["rows"]:
                rows.setdefault(r["y"], r["name"])
            self.log(f"Đã đọc {len(rows)} dòng...")
            if not snap["scrolled"]:
                stale += 1
                if stale >= 3:
                    break
            else:
                stale = 0 if len(rows) > before else stale + 1
                if stale >= 8:
                    break
            page.wait_for_timeout(500)
        # gán mỗi dòng vào mục gần nhất phía trên; bỏ mục "Bạn mới"
        hy = sorted(headers)
        friends = []
        for y in sorted(rows):
            sec = None
            for h in hy:
                if h <= y:
                    sec = headers[h]
                else:
                    break
            if sec and re.match(r"^(Bạn mới|New friends)$", sec, re.I):
                continue
            friends.append(rows[y])
        if not friends:
            raise ZaloError("Không đọc được bạn bè nào. Đã lưu file chẩn đoán: "
                            + self.save_diagnostics("khong_doc_duoc_ban_be"))
        cnt = Counter(core.norm_name(n) for n in friends)
        out, seen = [], set()
        for n in friends:
            k = core.norm_name(n)
            if k in seen:
                continue
            seen.add(k)
            out.append({"name": n, "same_name": cnt[k]})
        if total and len(friends) != total:
            folder = self.save_diagnostics("doc_ban_be_lech_so")
            self.log(f"⚠ Đọc được {len(friends)}/{total} bạn. Đã lưu file chẩn đoán: {folder}")
        return out
