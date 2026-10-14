"""Generate macOS menubar icons from Windows CFW tray_*_256.png (read-only).

usage: python3 tools/make_mac_icons.py [<windows icons dir>]

Source resolution order:
  1) argv[1]
  2) env MIHOMO_TRAY_ICONS
  3) sibling ../windows/icons (monorepo) or ../mihomo-tray/icons (legacy)
  4) already-present Assets/tray_*_256.png (or tray_rule_template_256.png + colored 256s)
"""
import os, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "Assets")
SIZES = {18: "", 36: "@2x", 22: "-22", 44: "-22@2x"}


def resolve_src():
    candidates = []
    if len(sys.argv) > 1:
        candidates.append(sys.argv[1])
    env = os.environ.get("MIHOMO_TRAY_ICONS")
    if env:
        candidates.append(env)
    candidates.append(os.path.join(HERE, "..", "..", "windows", "icons"))  # monorepo
    candidates.append(os.path.join(HERE, "..", "..", "mihomo-tray", "icons"))  # legacy sibling
    candidates.append(OUT)
    for c in candidates:
        if os.path.isfile(os.path.join(c, "tray_rule_256.png")) or os.path.isfile(
            os.path.join(c, "tray_rule_template_256.png")
        ):
            return os.path.abspath(c)
    raise SystemExit("no icon source found in: " + ", ".join(candidates))


def load_rgba(path):
    im = Image.open(path).convert("RGBA")
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a and r < 18 and g < 18 and b < 18:
                px[x, y] = (0, 0, 0, 0)
    return im


def to_template(im):
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    px, op = im.load(), out.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a < 20:
                continue
            mx, mn = max(r, g, b), min(r, g, b)
            sat = 0 if mx == 0 else (mx - mn) / mx
            if mx > 180 and sat < 0.25:
                continue  # eye/mouth hole
            op[x, y] = (0, 0, 0, a)
    return out


def fit(im, size):
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    bbox = im.getbbox()
    if bbox:
        im = im.crop(bbox)
    margin = 1 if size <= 22 else 2
    target = size - 2 * margin
    im2 = im.resize((target, target), Image.LANCZOS)
    canvas.paste(im2, ((size - im2.width) // 2, (size - im2.height) // 2), im2)
    return canvas


def pick(src, name):
    """Prefer tray_<name>_256.png; for rule also accept tray_rule_template_256.png."""
    p = os.path.join(src, f"tray_{name}_256.png")
    if os.path.isfile(p):
        return p
    if name == "rule":
        p2 = os.path.join(src, "tray_rule_template_256.png")
        if os.path.isfile(p2):
            return p2
    raise FileNotFoundError(p)


def main():
    src = resolve_src()
    os.makedirs(OUT, exist_ok=True)
    rule_path = pick(src, "rule")
    rule = load_rgba(rule_path)
    # If source is already template (Assets fallback), do not re-template
    if os.path.basename(rule_path) == "tray_rule_template_256.png" or src == os.path.abspath(OUT):
        rule_im = rule if "template" in os.path.basename(rule_path) else to_template(rule)
    else:
        rule_im = to_template(rule)
    variants = {
        "rule": rule_im,
        "global": load_rgba(pick(src, "global")),
        "direct": load_rgba(pick(src, "direct")),
        "offline": load_rgba(pick(src, "offline")),
    }
    for name, im in variants.items():
        for s, suffix in SIZES.items():
            fit(im, s).save(os.path.join(OUT, f"tray_{name}{suffix}.png"))
        if name == "rule":
            im.save(os.path.join(OUT, "tray_rule_template_256.png"))
        else:
            im.save(os.path.join(OUT, f"tray_{name}_256.png"))
    print("ok ->", OUT, "(src:", src + ")")


if __name__ == "__main__":
    main()
