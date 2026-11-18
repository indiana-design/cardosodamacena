# Artes abstratas em tons terrosos (geradas aqui) para as molduras do Poly Haven.
from PIL import Image, ImageDraw, ImageFilter
import random, sys
OUT = sys.argv[1]; random.seed(3)
def paper(w, h, base=(239, 233, 222)):
    im = Image.new('RGB', (w, h), base); px = im.load()
    for _ in range(w * h // 3):
        x, y = random.randrange(w), random.randrange(h); d = random.randint(-7, 5)
        r, g, b = px[x, y]; px[x, y] = (r + d, g + d, b + d)
    return im.filter(ImageFilter.GaussianBlur(0.8))
def brushy(im, draw_fn, color, blur=1.2):
    lay = Image.new('L', im.size, 0); draw_fn(ImageDraw.Draw(lay)); lay = lay.filter(ImageFilter.GaussianBlur(blur))
    solid = Image.new('RGB', im.size, color); im.paste(solid, (0, 0), lay)
CLAY, SAGE, SAND, OCHRE, INK = (190, 126, 96), (150, 158, 132), (214, 196, 168), (196, 152, 92), (70, 58, 50)
# 1 — arco de argila e sol de areia
a = paper(900, 1200)
brushy(a, lambda d: d.rectangle([170, 560, 730, 1060], fill=255) or d.pieslice([170, 280, 730, 840], 180, 360, fill=255), CLAY)
brushy(a, lambda d: d.ellipse([520, 180, 760, 420], fill=255), SAND)
brushy(a, lambda d: d.line([(120, 1080), (780, 1080)], fill=255, width=6), INK, 0.6)
a.save(f'{OUT}/arte_1.png')
# 2 — meia-lua sálvia e faixas ocre
b = paper(900, 1200)
brushy(b, lambda d: d.pieslice([140, 300, 760, 920], 0, 180, fill=255), SAGE)
brushy(b, lambda d: d.rectangle([140, 300, 760, 330], fill=255), OCHRE)
brushy(b, lambda d: d.ellipse([300, 160, 420, 280], fill=255), CLAY)
brushy(b, lambda d: d.arc([240, 760, 660, 1180], 200, 340, fill=255, width=10), INK, 0.6)
b.save(f'{OUT}/arte_2.png')
# 3 — horizonte (quarto): faixas de mar, areia e sol
c = paper(1500, 1000)
brushy(c, lambda d: d.rectangle([0, 560, 1500, 700], fill=255), (172, 187, 193))
brushy(c, lambda d: d.rectangle([0, 700, 1500, 1000], fill=255), SAND)
brushy(c, lambda d: d.ellipse([980, 300, 1220, 540], fill=255), CLAY)
brushy(c, lambda d: d.line([(0, 560), (1500, 560)], fill=255, width=3), INK, 0.5)
c.save(f'{OUT}/arte_3.png')
# 4 — ramo de folhas (oliveira) em verde-oliva sobre papel areia
import math
d4 = paper(900, 1200, (236, 228, 214))
def leaf(d, cx, cy, ang, L=170, W=52):
    pts = []
    for i in range(41):
        t = i / 40; w = math.sin(math.pi * t) * W / 2; x = (t - 0.5) * L
        pts.append((x, w))
    pts += [(x, -w) for x, w in reversed(pts)]
    ca, sa = math.cos(ang), math.sin(ang)
    d.polygon([(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in pts], fill=255)
def branch(d):
    d.line([(450, 1080), (455, 860), (470, 620), (440, 380), (470, 160)], fill=255, width=7)
    for i, (y, side) in enumerate([(980, 1), (900, -1), (820, 1), (740, -1), (660, 1), (580, -1), (500, 1), (420, -1), (340, 1), (260, -1), (190, 1)]):
        x = 452 + 8 * math.sin(i); ang = math.radians(-35 if side > 0 else 215) + 0.1 * math.sin(i * 2)
        leaf(d, x + side * 85 * math.cos(math.radians(35)), y - 50, ang)
brushy(d4, branch, (112, 120, 92))
brushy(d4, lambda d: d.ellipse([560, 230, 760, 430], fill=255), CLAY)
d4.save(f'{OUT}/arte_4.png')
# 5 — folha grande em argila com nervuras e meia-lua oliva
d5 = paper(900, 1200, (236, 228, 214))
brushy(d5, lambda d: d.pieslice([120, 640, 780, 1300], 180, 360, fill=255), (124, 132, 104))
brushy(d5, lambda d: leaf(d, 450, 520, math.radians(-70), 720, 330), CLAY)
for k in range(-4, 5):
    brushy(d5, lambda d, k=k: d.line([(450 + 40 * k * 0.34, 520 - 40 * k), (450 + 40 * k * 0.34 + (150 if k % 2 else -150), 520 - 40 * k - 90)], fill=255, width=5), (236, 228, 214), 0.6)
d5.save(f'{OUT}/arte_5.png')
print('ok')
