"""Recolor the original CFW tray icon (tray_normal.ico) into rule/global/direct/offline variants."""
import colorsys, os, struct, io
from PIL import Image
SRC = os.path.join(os.path.dirname(__file__), '..', 'icons', 'cfw_tray_normal_original.ico')
OUT = os.path.join(os.path.dirname(__file__), '..', 'icons')
SIZES = [16, 20, 24, 32, 48, 256]

def frames():
    im = Image.open(SRC)
    res = {}
    for s in im.ico.sizes():
        res[s[0]] = im.ico.getimage(s).convert('RGBA')
    big = res[256]
    for s in SIZES:
        if s not in res:
            res[s] = big.resize((s, s), Image.LANCZOS)
    return {s: res[s] for s in SIZES}

def recolor(img, hue=None, sat_mul=1.0, val_mul=1.0, grey=False):
    img = img.copy(); px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = px[x, y]
            if a == 0: continue
            h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
            if grey:
                s = 0; v = min(1, v*1.25) if s < 0.15 else v
            elif s > 0.12:   # coloured body; leave white eyes / near-grey pixels alone
                h = hue; s = min(1, s*sat_mul); v = min(1, v*val_mul)
            r2, g2, b2 = colorsys.hsv_to_rgb(h, s, v)
            px[x, y] = (round(r2*255), round(g2*255), round(b2*255), a)
    return img

def dib(im):
    """32-bit BGRA DIB + 1-bit AND mask (classic ICO entry; safest for System.Drawing.Icon)."""
    w, h = im.size
    hdr = struct.pack('<IiiHHIIiiII', 40, w, h*2, 1, 32, 0, 0, 0, 0, 0, 0)
    px = im.load(); xor = bytearray(); mask = bytearray()
    row_bytes = ((w + 31)//32)*4
    for y in range(h-1, -1, -1):
        mrow = bytearray(row_bytes)
        for x in range(w):
            r, g, b, a = px[x, y]
            xor += bytes((b, g, r, a))
            if a == 0: mrow[x//8] |= 0x80 >> (x % 8)
        mask += mrow
    return hdr + bytes(xor) + bytes(mask)

def write_ico(path, imgs):
    # PNG-compressed entries for 256, BMP-less PNG for all is supported on Vista+; use PNG for all.
    entries = []; data = b''
    for im in imgs:
        if im.width >= 256:
            buf = io.BytesIO(); im.save(buf, 'PNG'); entries.append((im.width, buf.getvalue()))
        else:
            entries.append((im.width, dib(im)))
    off = 6 + 16*len(entries); hdr = struct.pack('<HHH', 0, 1, len(entries)); dirs = b''
    for w, d in entries:
        dirs += struct.pack('<BBBBHHII', w % 256, w % 256, 0, 0, 1, 32, len(d), off); off += len(d); data += d
    open(path, 'wb').write(hdr + dirs + data)

def main():
    fr = frames()
    variants = {
        'rule':    lambda i: i,
        'global':  lambda i: recolor(i, hue=0/360, sat_mul=1.05, val_mul=1.45),
        'direct':  lambda i: recolor(i, hue=135/360, sat_mul=1.0, val_mul=1.25),
        'offline': lambda i: recolor(i, grey=True),
    }
    for name, fn in variants.items():
        imgs = [fn(fr[s]) for s in SIZES]
        write_ico(os.path.join(OUT, f'tray_{name}.ico'), imgs)
        imgs[-1].save(os.path.join(OUT, f'tray_{name}_256.png'))
    print('ok')
main()
