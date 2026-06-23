"""精确绘制一张高密度信息图作为视觉模型横评基准。
标准答案完全可控，便于设计区分度高的评分点。
"""
import math
from PIL import Image, ImageDraw, ImageFont

W, H = 1240, 1640
img = Image.new("RGB", (W, H), "#f4f6f8")
d = ImageDraw.Draw(img)

F = "C:/Windows/Fonts/"
def font(name, size):
    return ImageFont.truetype(F + name, size)

yahei = lambda s: font("msyh.ttc", s)
yaheib = lambda s: font("msyhbd.ttc", s)
arialb = lambda s: font("arialbd.ttf", s)

def text(xy, s, fnt, fill="#1b2733", anchor="la"):
    d.text(xy, s, font=fnt, fill=fill, anchor=anchor)

# ===== 标题栏 =====
d.rectangle([0, 0, W, 110], fill="#10324f")
text((40, 30), "环球物流 2026 年度运营简报", yaheib(40), fill="#ffffff")
text((W - 40, 42), "GLOBAL LOGISTICS 2026", arialb(24), fill="#8fd0ff", anchor="ra")

# ===== KPI 卡片 =====
cards = [
    ("#2563eb", "订单 ORDERS", "1842"),
    ("#16a34a", "营收 REVENUE", "¥5.7M"),
    ("#ea580c", "延误 DELAYS", "37"),
    ("#dc2626", "退货 RETURNS", "12%"),
]
cw, gap, x0, y0, ch = 270, 22, 40, 135, 130
for i, (color, label, val) in enumerate(cards):
    x = x0 + i * (cw + gap)
    d.rounded_rectangle([x, y0, x + cw, y0 + ch], radius=10, fill="#ffffff", outline=color, width=3)
    d.rectangle([x, y0, x + 10, y0 + ch], fill=color)
    text((x + 26, y0 + 20), label, yahei(20), fill="#5b6b7b")
    text((x + 26, y0 + 55), val, arialb(46), fill=color)

# ===== 柱状图 =====
bx, by, bw, bh = 40, 300, 560, 320
d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=10, fill="#ffffff", outline="#d7dee6", width=2)
text((bx + 20, by + 16), "本周运单量（单位：百单）", yaheib(22))
bars = [("周一", 40), ("周二", 65), ("周三", 30), ("周四", 80), ("周五", 55)]
base_y = by + bh - 50
maxv, plot_h = 80, 180
for i, (lab, v) in enumerate(bars):
    bxx = bx + 50 + i * 100
    barh = int(plot_h * v / maxv)
    d.rectangle([bxx, base_y - barh, bxx + 58, base_y], fill="#2563eb")
    text((bxx + 29, base_y - barh - 22), str(v), arialb(20), fill="#10324f", anchor="ma")
    text((bxx + 29, base_y + 10), lab, yahei(18), fill="#5b6b7b", anchor="ma")

# ===== 饼图 =====
px, py, pr = 720, 320, 110
cx, cy = px + pr, py + pr
d.rounded_rectangle([px - 30, py - 30, px + 2 * pr + 240, py + 2 * pr + 30], radius=10, fill="#ffffff", outline="#d7dee6", width=2)
text((px - 10, py - 24), "运输方式占比", yaheib(22))
slices = [("海运", 50, "#0ea5e9"), ("空运", 30, "#f59e0b"), ("陆运", 20, "#22c55e")]
start = -90
for lab, pct, col in slices:
    end = start + pct * 3.6
    d.pieslice([cx - pr, cy - pr, cx + pr, cy + pr], start, end, fill=col)
    start = end
lx = cx + pr + 36
for j, (lab, pct, col) in enumerate(slices):
    ly = cy - 44 + j * 40
    d.rectangle([lx, ly, lx + 22, ly + 22], fill=col)
    text((lx + 32, ly - 2), f"{lab} {pct}%", yahei(22))

# ===== 仪表盘 =====
gx, gy, gr = 90, 700, 95
gcx, gcy = gx + gr, gy + gr + 20
d.rounded_rectangle([gx - 40, gy - 20, gx + 2 * gr + 70, gy + 2 * gr + 40], radius=10, fill="#ffffff", outline="#d7dee6", width=2)
text((gx - 20, gy - 6), "客户满意度", yaheib(20))
d.arc([gcx - gr, gcy - gr, gcx + gr, gcy + gr], 180, 360, fill="#e2e8f0", width=22)
ang = math.radians(180 + 72 / 100 * 180)
d.line([gcx, gcy, gcx + gr * 0.8 * math.cos(ang), gcy + gr * 0.8 * math.sin(ang)], fill="#dc2626", width=6)
text((gcx, gcy - 6), "72", arialb(40), fill="#10324f", anchor="ma")

# ===== 清单 =====
kx, ky, kw, kh = 380, 700, 350, 230
d.rounded_rectangle([kx, ky, kx + kw, ky + kh], radius=10, fill="#ffffff", outline="#d7dee6", width=2)
text((kx + 20, ky + 14), "出库检查清单", yaheib(22))
items = [("扫描条码", True), ("称重复核", True), ("打印面单", True), ("装车签字", False), ("回传回执", False)]
for i, (t, done) in enumerate(items):
    iy = ky + 56 + i * 34
    box = [kx + 22, iy, kx + 44, iy + 22]
    if done:
        d.rectangle(box, fill="#16a34a")
        d.line([kx + 26, iy + 11, kx + 32, iy + 18], fill="#ffffff", width=3)
        d.line([kx + 32, iy + 18, kx + 40, iy + 5], fill="#ffffff", width=3)
    else:
        d.rectangle(box, outline="#94a3b8", width=2)
    text((kx + 56, iy - 1), t, yahei(20))

# ===== 图标行 =====
ix, iy0, iw = 760, 700, 440
d.rounded_rectangle([ix, iy0, ix + iw, iy0 + 230], radius=10, fill="#ffffff", outline="#d7dee6", width=2)
text((ix + 20, iy0 + 14), "运输与时间", yaheib(22))
# emoji 用 seguiemj
try:
    emo = font("seguiemj.ttf", 40)
except Exception:
    emo = yahei(40)
icons = "🚚 ✈ 🚢 🏭"
text((ix + 24, iy0 + 60), icons, emo)
# 时钟 3:45
clk_cx, clk_cy, clk_r = ix + 80, iy0 + 165, 36
d.ellipse([clk_cx - clk_r, clk_cy - clk_r, clk_cx + clk_r, clk_cy + clk_r], outline="#10324f", width=4, fill="#ffffff")
# 时针指向 3 多一点(3:45)，分针指向 9
d.line([clk_cx, clk_cy, clk_cx + 20, clk_cy + 6], fill="#10324f", width=4)  # 时针 ~3:45
d.line([clk_cx, clk_cy, clk_cx - 26, clk_cy], fill="#dc2626", width=3)       # 分针 -> 9 (45分)
text((clk_cx + clk_r + 10, clk_cy - 14), "3:45", arialb(28), fill="#10324f")
# 日历 26
cal_x, cal_y = ix + 250, iy0 + 130
d.rounded_rectangle([cal_x, cal_y, cal_x + 80, cal_y + 80], radius=8, fill="#ffffff", outline="#dc2626", width=3)
d.rectangle([cal_x, cal_y, cal_x + 80, cal_y + 24], fill="#dc2626")
text((cal_x + 40, cal_y + 4), "六月", yahei(16), fill="#ffffff", anchor="ma")
text((cal_x + 40, cal_y + 30), "26", arialb(40), fill="#10324f", anchor="ma")

# ===== 底部数据表 =====
tx, ty, tw = 40, 960, W - 80
rows = [
    ("区域", "订单", "准时率", "状态"),
    ("华东", "680", "96%", "正常"),
    ("华南", "540", "91%", "正常"),
    ("华北", "410", "88%", "关注"),
    ("西部", "212", "79%", "预警"),
]
rh = 56
d.rounded_rectangle([tx, ty, tx + tw, ty + rh * len(rows)], radius=10, fill="#ffffff", outline="#d7dee6", width=2)
colx = [tx + 30, tx + 330, tx + 640, tx + 950]
for r, row in enumerate(rows):
    ry = ty + r * rh
    if r == 0:
        d.rectangle([tx, ty, tx + tw, ty + rh], fill="#10324f")
    for c, cell in enumerate(row):
        col = "#ffffff" if r == 0 else "#1b2733"
        fnt = yaheib(22) if r == 0 else yahei(22)
        text((colx[c], ry + 14), cell, fnt, fill=col)
    if r > 0:
        d.line([tx, ry, tx + tw, ry], fill="#eef2f6", width=1)

# ===== 底部警示条 =====
wy = ty + rh * len(rows) + 24
d.rounded_rectangle([tx, wy, tx + tw, wy + 130], radius=10, fill="#fff4e5", outline="#ea580c", width=2)
text((tx + 24, wy + 18), "⚠ 风险提示", yaheib(24), fill="#b45309")
text((tx + 24, wy + 60), "西部区域准时率跌破 80%，环比下降 9 个百分点，需在 6 月 30 日前完成整改。", yahei(22), fill="#7c4a03")
text((tx + 24, wy + 92), "联系人：李雷  电话：021-8866-0179  邮箱：ops@global-logi.com", yahei(20), fill="#7c4a03")

# 水印
text((W - 40, H - 36), "INTERNAL USE ONLY · DO NOT DISTRIBUTE", arialb(18), fill="#c2ccd6", anchor="ra")

out = "skills/image-recognition/scripts/_bench_complex.png"
img.save(out)
print("saved", out, img.size)
