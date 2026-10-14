"""从 Windows 版的 256px 原色猫（icons/tray_*_256.png）生成 Linux 托盘用的各尺寸 PNG。
usage: python3 tools/make_icons.py [<windows icons dir>]
默认顺序：argv[1] → 环境变量 MIHOMO_TRAY_ICONS → ../windows/icons（合仓）→ ../mihomo-tray/icons（旧旁挂）
→ 本包 mihomotray/icons 里已有的 256px。
"""
import os, sys
from PIL import Image

root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
out = os.path.join(root, 'mihomotray', 'icons')
os.makedirs(out, exist_ok=True)

candidates = []
if len(sys.argv) > 1:
    candidates.append(sys.argv[1])
env = os.environ.get('MIHOMO_TRAY_ICONS')
if env:
    candidates.append(env)
candidates.append(os.path.join(root, '..', 'windows', 'icons'))
candidates.append(os.path.join(root, '..', 'mihomo-tray', 'icons'))
candidates.append(out)

src = None
for c in candidates:
    probe = os.path.join(c, 'tray_rule_256.png')
    if os.path.isfile(probe):
        src = c
        break
if src is None:
    raise SystemExit('no tray_rule_256.png found in: ' + ', '.join(candidates))

for m in ('rule', 'global', 'direct', 'offline'):
    p = os.path.join(src, 'tray_%s_256.png' % m)
    if not os.path.exists(p):
        p = os.path.join(out, 'tray_%s_256.png' % m)
    im = Image.open(p).convert('RGBA')
    for s in (16, 22, 24, 32, 48, 64, 128, 256):
        (im if s == 256 else im.resize((s, s), Image.LANCZOS)).save(
            os.path.join(out, 'tray_%s_%d.png' % (m, s)))
print('icons ->', out, '(src:', src + ')')
