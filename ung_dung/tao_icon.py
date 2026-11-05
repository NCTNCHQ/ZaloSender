"""Vẽ icon ứng dụng (bong bóng chat + máy bay giấy + mũi tên tự động) -> icon.ico / icon.png"""
import math, os
from PIL import Image, ImageDraw

S = 1024
BLUE1, BLUE2 = (0, 104, 255), (45, 150, 255)
PLANE, PLANE_D = (0, 104, 255), (0, 72, 190)
ORANGE = (255, 140, 0)
WHITE = (255, 255, 255, 255)

def build():
    # nền gradient bo góc
    grad = Image.new("RGBA", (S, S))
    gd = ImageDraw.Draw(grad)
    for y in range(S):
        t = y / S
        c = tuple(int(BLUE2[i] * (1 - t) + BLUE1[i] * t) for i in range(3))
        gd.line([(0, y), (S, y)], fill=c + (255,))
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle([24, 24, S - 24, S - 24], radius=230, fill=255)
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    img.paste(grad, (0, 0), mask)
    d = ImageDraw.Draw(img)

    # bong bóng chat
    d.rounded_rectangle([150, 190, 830, 690], radius=170, fill=WHITE)
    d.polygon([(270, 620), (200, 850), (450, 680)], fill=WHITE)

    # máy bay giấy
    T, L, B, F = (700, 300), (300, 470), (540, 620), (470, 505)
    d.polygon([L, T, F], fill=PLANE)
    d.polygon([F, T, B], fill=PLANE_D)
    d.polygon([F, (470, 600), (515, 560)], fill=PLANE_D)

    # huy hiệu "tự động"
    cx, cy = 770, 770
    d.ellipse([cx - 215, cy - 215, cx + 215, cy + 215], fill=WHITE)
    d.ellipse([cx - 180, cy - 180, cx + 180, cy + 180], fill=ORANGE + (255,))
    r, w = 100, 36
    for a0, a1 in ((200, 330), (20, 150)):
        d.arc([cx - r, cy - r, cx + r, cy + r], a0, a1, fill=WHITE, width=w)
        a = math.radians(a1)
        px, py = cx + (r - w / 2) * math.cos(a), cy + (r - w / 2) * math.sin(a)
        tx, ty = -math.sin(a), math.cos(a)          # hướng tiếp tuyến
        nx, ny = math.cos(a), math.sin(a)           # hướng bán kính
        d.polygon([(px + tx * 60, py + ty * 60),
                   (px + nx * 48, py + ny * 48),
                   (px - nx * 48, py - ny * 48)], fill=WHITE)
    return img

def build_pro():
    """Icon bản PRO: icon thường + nhãn 'PRO' màu vàng ở góc trên."""
    from PIL import ImageFont
    img = build()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([520, 40, 1000, 300], radius=70, fill=(255, 196, 0, 255), outline=WHITE, width=24)
    font = None
    for name in ("arialbd.ttf", "DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf"):
        try:
            font = ImageFont.truetype(name, 190)
            break
        except OSError:
            continue
    font = font or ImageFont.load_default()
    box = d.textbbox((0, 0), "PRO", font=font)
    w, h = box[2] - box[0], box[3] - box[1]
    d.text((760 - w / 2 - box[0], 170 - h / 2 - box[1]), "PRO", font=font, fill=(120, 60, 0, 255))
    return img


if __name__ == "__main__":
    out = os.path.dirname(os.path.abspath(__file__))
    big = build()
    big.resize((256, 256), Image.LANCZOS).save(os.path.join(out, "icon.png"))
    big.resize((256, 256), Image.LANCZOS).save(
        os.path.join(out, "icon.ico"),
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    pro = build_pro()
    pro.resize((256, 256), Image.LANCZOS).save(os.path.join(out, "icon_pro.png"))
    pro.resize((256, 256), Image.LANCZOS).save(
        os.path.join(out, "icon_pro.ico"),
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
