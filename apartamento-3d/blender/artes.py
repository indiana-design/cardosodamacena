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
print('ok')
