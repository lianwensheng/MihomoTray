"""preview.png：右键菜单（Windows 原生菜单）的示意图。
原生菜单是 Windows 自己画的，Linux 上没法真实渲染，这里按 Win11 / Win10 原生菜单的尺寸和配色手绘模拟（200% 缩放）。"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
FONT = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
f = lambda s: ImageFont.truetype(FONT, s)
S = 2  # 200%
ITEMS = ['打开面板', '切换程序', None, '规则模式', '全局模式', '直连模式', None, '退出']
CHECKED, HOVER = 3, 4

THEMES = {
    'win11_light': dict(back=(249, 249, 249), text=(0, 0, 0), hover=(240, 240, 240), sep=(215, 215, 215), border=(220, 220, 220),
                        round=8, desk=(206, 222, 240), bar=(238, 238, 238), clock=(20, 20, 20), win11=True),
    'win11_dark': dict(back=(44, 44, 44), text=(255, 255, 255), hover=(61, 61, 61), sep=(70, 70, 70), border=(60, 60, 60),
                       round=8, desk=(40, 44, 52), bar=(32, 32, 32), clock=(255, 255, 255), win11=True),
    'win10_light': dict(back=(242, 242, 242), text=(0, 0, 0), hover=(145, 201, 247, 255), sep=(204, 204, 204), border=(204, 204, 204),
                        round=0, desk=(0, 90, 158), bar=(16, 16, 16), clock=(255, 255, 255), win11=False),
}

def draw_check(d, cx, cy, col):
    w = 1.6 * S
    d.line([(cx - 5 * S, cy), (cx - 1.5 * S, cy + 3.5 * S), (cx + 5.5 * S, cy - 4 * S)], fill=col, width=int(w), joint='curve')

def menu(t):
    item_h, sep_h, pad, gutter, w = (30 if t['win11'] else 22) * S, (9 if t['win11'] else 9) * S, (4 if t['win11'] else 3) * S, 36 * S, 150 * S
    h = pad * 2 + sum(sep_h if i is None else item_h for i in ITEMS)
    m = Image.new('RGBA', (w, h), t['back'] + (255,)); d = ImageDraw.Draw(m, 'RGBA')
    y = pad
    for idx, it in enumerate(ITEMS):
        if it is None:
            x0 = (4 if t['win11'] else gutter // S) * S
            d.line([(x0, y + sep_h // 2), (w - 4 * S, y + sep_h // 2)], fill=t['sep'], width=S // 2 or 1); y += sep_h; continue
        if idx == HOVER:
            if t['win11']: d.rounded_rectangle((4 * S, y + 1 * S, w - 4 * S, y + item_h - 1 * S), 4 * S, fill=t['hover'])
            else: d.rectangle((2 * S, y, w - 3 * S, y + item_h - 1), fill=(204, 232, 255), outline=(153, 209, 255))
        if idx == CHECKED: draw_check(d, 18 * S, y + item_h // 2, t['text'])
        d.text((gutter, y + item_h // 2), it, font=f(12 * S), fill=t['text'], anchor='lm'); y += item_h
    return m

def card(m, t):
    w, h = m.size; r = t['round'] * S; pad = 30
    out = Image.new('RGBA', (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    sh = Image.new('RGBA', out.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((pad, pad + 4, pad + w, pad + h + 4), max(r, 1), fill=(0, 0, 0, 80 if t['win11'] else 60))
    out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10 if t['win11'] else 4)))
    mask = Image.new('L', (w, h), 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=255)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), r, outline=t['border'], width=S // 2 or 1)
    m.putalpha(mask); out.alpha_composite(m, (pad, pad)); return out

W, H = 1300, 760
img = Image.new('RGBA', (W, H), (243, 243, 243, 255)); d = ImageDraw.Draw(img)
d.text((40, 22), '右键菜单 · 示意图（mock）', font=f(30), fill=(30, 30, 30))
d.text((40, 66), '这一版用的是 Windows 原生菜单（和 FlClash v0.8.99 一样调用 TrackPopupMenu），实际外观由 Windows 自己绘制。', font=f(18), fill=(70, 70, 70))
d.text((40, 92), 'Linux 上没法真实渲染原生菜单，下图是按 Win11 / Win10 原生菜单的样子手绘的模拟，200% 缩放；鼠标悬停在“全局模式”上，当前为规则模式。', font=f(18), fill=(70, 70, 70))
labels = {'win11_light': 'Windows 11 · 浅色（默认，与 FlClash 原版一致）', 'win11_dark': 'Windows 11 · 深色（theme = system / dark 时）',
          'win10_light': 'Windows 10 · 浅色'}
for i, k in enumerate(['win11_light', 'win11_dark', 'win10_light']):
    t = THEMES[k]; x0 = 40 + i * 410; y0 = 170; pw, ph = 390, 560
    d.text((x0 + 4, y0 - 34), labels[k], font=f(18), fill=(30, 30, 30))
    panel = Image.new('RGBA', (pw, ph), t['desk'] + (255,)); pd = ImageDraw.Draw(panel)
    pd.rectangle((0, ph - 48, pw, ph), fill=t['bar'] + (255,))
    tray = Image.open('icons/tray_rule.ico'); tray.size = (32, 32)
    panel.alpha_composite(tray.convert('RGBA'), (pw - 130, ph - 40))
    pd.text((pw - 80, ph - 24), '16:42', font=f(16), fill=t['clock'], anchor='lm')
    c = card(menu(t), t)
    # 原生菜单按 TPM_BOTTOMALIGN | TPM_LEFTALIGN 在鼠标处弹出：左下角对准鼠标，空间不够时 Windows 会往左挪
    panel.alpha_composite(c, (pw - c.width - 6, ph - 48 - c.height + 22))
    pm = Image.new('L', (pw, ph), 0); ImageDraw.Draw(pm).rounded_rectangle((0, 0, pw - 1, ph - 1), 14, fill=255)
    img.paste(panel, (x0, y0), pm)
img.convert('RGB').save('preview.png'); print('preview.png')
