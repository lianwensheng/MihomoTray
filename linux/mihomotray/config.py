"""读取 ~/.config/MihomoTray/config.ini（不存在则生成默认配置），解析规则与 Windows 版 AppConfig.cs 一致。"""
import os
import re
import shlex
import shutil
import sys
from urllib.parse import urlsplit

from . import loc

DEFAULT_INI = (
    "; MihomoTray 配置文件（修改后重启 MihomoTray 生效）\n"
    "; MihomoTray config (restart MihomoTray after editing)\n"
    "\n"
    "[mihomo]\n"
    "; external-controller 地址，自定义地址在 mihomo 配置里查询并更换\n"
    "; external-controller address — look it up in your mihomo config\n"
    "controller = 127.0.0.1:9090\n"
    "\n"
    "; external-controller 的 secret，此安全密钥在 mihomo 配置后查询并填入（请只用 ASCII 字母、数字和符号）\n"
    "; external-controller secret — look it up in your mihomo config and fill it in (ASCII letters, digits, and symbols only)\n"
    "secret = \n"
    "\n"
    "; 点击“打开面板”时打开的网址，自定义网址在 mihomo 配置里查询并更换\n"
    "; URL opened by Dashboard / left-click — look it up in your mihomo config\n"
    "panel_url = http://127.0.0.1:9090/ui/\n"
    "\n"
    "; 点击“切换程序”时启动的程序（可执行文件路径、AppImage 或 PATH 里的命令名），留空则该菜单项变灰\n"
    "; Program launched by Open App (executable path, AppImage or a command on PATH); leave empty to gray out the item\n"
    "; 支持带空格/带引号的路径、~、环境变量（如 $HOME）、相对路径（相对本配置文件所在文件夹）\n"
    "; Paths may contain spaces/quotes, ~, env vars (e.g. $HOME), or be relative to this config's folder\n"
    "; switch_program = ~/Applications/某客户端.AppImage\n"
    "; switch_program = ~/Applications/SomeClient.AppImage\n"
    "; switch_program = some-client\n"
    "switch_program = \n"
    "\n"
    "; 启动上面程序时附带的命令行参数，一般留空\n"
    "; Extra command-line args for the program above (usually empty)\n"
    "switch_program_args = \n"
    "\n"
    "; 轮询当前模式的间隔（秒）\n"
    "; Poll interval for current mode (seconds)\n"
    "poll_interval = 3\n"
    "\n"
    "; 切换模式后是否断开现有连接，让已建立的连接也立即按新模式走（设为 false 则只影响新连接）\n"
    "; Close existing connections after switching mode (false = only new connections use the new mode)\n"
    "close_connections = true\n"
    "\n"
    "[ui]\n"
    "; 界面语言：system（跟随系统）/ zh（中文）/ en（英文）\n"
    "; UI language: system (follow OS) / zh (Chinese) / en (English)\n"
    "language = system\n"
    "\n"
    "; 开机自启：true（开启）/ false（关闭，默认）；每次启动时按这里同步系统设置\n"
    "; Start at login: true / false (default); synced to the system on every start\n"
    "autostart = false\n"
)

def data_dir():
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
    return os.path.join(base, "MihomoTray")


def ini_path():
    return os.path.join(data_dir(), "config.ini")


def icons_dir():
    return os.path.join(data_dir(), "Icons")


def strip_comment(v):
    """去掉不在引号里的行尾注释：前面有空白的 ; 或 # 及其后面的内容。"""
    in_q = False
    for i, c in enumerate(v):
        if c == '"':
            in_q = not in_q
        elif not in_q and c in ";#" and i > 0 and v[i - 1].isspace():
            return v[:i].rstrip()
    return v


def unquote(v):
    """以引号开头时取引号内的内容，返回 (值, 引号后剩下的部分)；否则原样返回。"""
    if v.startswith('"'):
        end = v.find('"', 1)
        if end > 0:
            return v[1:end], v[end + 1:].strip()
    return v, ""


def key_of(line):
    t = line.strip()
    if not t or t[0] in ";#[":
        return None
    eq = t.find("=")
    return None if eq <= 0 else t[:eq].strip().lower()


def section_of(line):
    t = line.strip()
    if len(t) >= 2 and t[0] == "[" and t[-1] == "]":
        return t[1:-1].strip().lower()
    return None


def try_normalize_controller(v):
    """补 http://；“:9090”、0.0.0.0、[::] 改成 127.0.0.1；返回 (url, None) 或 (None, 错误原因)。"""
    v = (v or "").strip()
    if not v:
        return None, loc.AddrEmpty()
    scheme = "http://"
    low = v.lower()
    if low.startswith("http://"):
        v = v[7:]
    elif low.startswith("https://"):
        scheme, v = "https://", v[8:]
    elif "://" in v:
        return None, loc.OnlyHttp()
    v = v.rstrip("/")
    if v in ("0.0.0.0", "[::]", "::"):
        v = "127.0.0.1"
    elif v.startswith(":"):
        v = "127.0.0.1" + v
    elif v.startswith("0.0.0.0:"):
        v = "127.0.0.1" + v[7:]
    elif v.startswith("[::]:"):
        v = "127.0.0.1" + v[4:]
    host_port = v.split("/", 1)[0]
    m = re.match(r"^(\[[0-9A-Fa-f:.]+\]|[^:\[\]]+):(\d{1,5})$", host_port)
    if not m:
        return None, loc.MissingPort()
    port = int(m.group(2))
    if port < 1 or port > 65535:
        return None, loc.PortRange(port)
    url = scheme + v
    try:
        u = urlsplit(url)
        ok = bool(u.hostname) and " " not in v
    except ValueError:
        ok = False
    if not ok:
        return None, loc.BadAddrFormat()
    return url, None


def normalize_controller(v):
    r, _ = try_normalize_controller(v)
    if r:
        return r
    v = v.strip().rstrip("/")
    if not v.lower().startswith(("http://", "https://")):
        v = "http://" + v
    return v


def _bool(v, default):
    v = v.lower()
    if v in ("true", "1", "yes", "on"):
        return True
    if v in ("false", "0", "no", "off"):
        return False
    return default


class AppConfig:
    def __init__(self):
        self.controller = "http://127.0.0.1:9090"
        self.secret = ""
        self.panel_url = "http://127.0.0.1:9090/ui/"
        self.switch_program = ""
        self.switch_program_args = ""
        self._switch_args_inline = ""
        self.poll_seconds = 3
        self.close_connections = True
        self.language = "system"
        self.autostart = False
        self.errors = []

    @property
    def has_switch_program(self):
        return len(self.switch_program) > 0

    @property
    def effective_switch_args(self):
        if not self._switch_args_inline:
            return self.switch_program_args
        if not self.switch_program_args:
            return self._switch_args_inline
        return self._switch_args_inline + " " + self.switch_program_args

    def parse(self, lines):
        lines = list(lines)
        for raw in lines:  # 先读 language，再生成其它校验文案
            if key_of(raw) != "language":
                continue
            line = raw.strip()
            v, _ = unquote(strip_comment(line[line.find("=") + 1:].strip()))
            v = v.lower()
            if v in ("system", "zh", "en"):
                self.language = v
        loc.apply(self.language)

        for raw in lines:
            k = key_of(raw)
            if k is None:
                continue
            line = raw.strip()
            value = line[line.find("=") + 1:].strip()
            # secret 整行都算密钥；其它项去掉行尾注释
            raw_value = value if k == "secret" else strip_comment(value)
            v, rest = unquote(raw_value)
            if k == "secret":
                v = value[1:-1] if len(value) >= 2 and value[0] == '"' and value[-1] == '"' else value
                rest = ""
            if rest and k not in ("switch_program", "switch_program_args"):
                self.errors.append(loc.ExtraAfterQuote(k, rest))
            if k == "controller":
                if v:
                    norm, err = try_normalize_controller(v)
                    if norm:
                        self.controller = norm
                    else:
                        self.errors.append("controller = " + v + (": " if loc.En else "：") + err)
            elif k == "secret":
                self.secret = v
            elif k == "panel_url":
                if v:
                    try:
                        u = urlsplit(v)
                        ok = u.scheme in ("http", "https") and bool(u.netloc)
                    except ValueError:
                        ok = False
                    if ok:
                        self.panel_url = v
                    else:
                        self.errors.append(loc.BadPanelUrl(v))
            elif k == "switch_program":
                self.switch_program = v.strip()
                if rest:
                    self._switch_args_inline = rest
            elif k == "switch_program_args":
                self.switch_program_args = raw_value
            elif k == "poll_interval":
                try:
                    self.poll_seconds = max(1, min(60, int(v)))
                except ValueError:
                    self.errors.append(loc.BadPoll(v, self.poll_seconds))
            elif k == "close_connections":
                self.close_connections = _bool(v, True)
            elif k == "autostart":
                self.autostart = v.lower() in ("true", "1", "yes", "on")
            # language 已在第一遍处理；theme 等 Windows 专属项忽略

    # ---- 切换程序 ----
    def program_command(self, base_dir=None):
        """返回 (argv, 错误文案)。switch_program 可以是路径（支持 ~、$VAR、相对路径）或 PATH 里的命令名。"""
        if not self.has_switch_program:
            return None, loc.SwitchNotSet()
        base_dir = base_dir or data_dir()
        args = shlex.split(self.effective_switch_args) if self.effective_switch_args else []
        path = resolve_program_path(self.switch_program, base_dir)
        if path is None and not self.switch_program.startswith('"') and " " in self.switch_program:
            # 没加引号又带参数的写法：switch_program = clash-verge --minimized
            try:
                parts = shlex.split(self.switch_program)
            except ValueError:
                parts = []
            if parts:
                p0 = resolve_program_path(parts[0], base_dir)
                if p0:
                    path, args = p0, parts[1:] + args
        if path is None:
            return None, loc.FileNotFound(os.path.expandvars(os.path.expanduser(self.switch_program)))
        if not os.access(path, os.X_OK):
            return None, loc.NotExecutable(path)
        return [path] + args, None


def resolve_program_path(raw, base_dir):
    """展开 ~ 和环境变量；含 / 的按路径解析（相对路径基于 base_dir），否则在 PATH 里找。找不到返回 None。"""
    if raw is None:
        return None
    p, _ = unquote(raw.strip())
    p = p.strip().strip('"').strip()
    if not p:
        return None
    p = os.path.expandvars(os.path.expanduser(p))
    if "/" not in p:
        w = shutil.which(p)
        if w:
            return os.path.abspath(w)
    cand = p if os.path.isabs(p) else os.path.join(base_dir, p)
    cand = os.path.abspath(cand)
    return cand if os.path.isfile(cand) else None


def merge_missing_keys(existing, default_ini=DEFAULT_INI):
    """默认配置里有、现有文件里没有的键（连同前面的注释）插到对应小节末尾；都不缺返回 None。"""
    have = {k for k in (key_of(l) for l in existing) if k}
    order, blocks, sec, comments = [], {}, "", []
    for raw in default_ini.split("\n"):
        s = section_of(raw)
        if s is not None:
            sec, comments = s, []
            continue
        if raw.strip().startswith(";"):
            comments.append(raw)
            continue
        k = key_of(raw)
        if k and k not in have:
            if sec not in blocks:
                blocks[sec] = []
                order.append(sec)
            blocks[sec] += comments + [raw]
        comments = []
    if not order:
        return None
    lines = list(existing)
    while lines and not lines[-1].strip():
        lines.pop()
    for s in order:
        add = blocks[s]
        start = next((i for i, l in enumerate(lines) if section_of(l) == s), -1)
        if start < 0 and s:
            lines += ["", "[" + s + "]"] + add
            continue
        end = next((i for i in range(start + 1, len(lines)) if section_of(lines[i]) is not None), len(lines))
        at = end
        while at - 1 > start and not lines[at - 1].strip():
            at -= 1
        lines[at:at] = add
    return "\n".join(lines) + "\n"


def load_and_upgrade(c, path):
    data = open(path, "rb").read()
    bom = data.startswith(b"\xef\xbb\xbf")
    try:
        text = data[3 if bom else 0:].decode("utf-8")
        utf8 = True
    except UnicodeDecodeError:
        text = data.decode("utf-8", "replace")
        utf8 = False
    nl = "\r\n" if "\r\n" in text else "\n"
    lines = text.replace("\r\n", "\n").split("\n")
    c.parse(lines)
    if not utf8 or not os.access(path, os.W_OK):
        return  # 不是 UTF-8 或只读：不动用户文件
    merged = merge_missing_keys(lines)
    if merged is None:
        return
    if nl == "\r\n":
        merged = merged.replace("\n", "\r\n")
    tmp = path + ".tmp"
    try:
        with open(tmp, "wb") as f:
            f.write((b"\xef\xbb\xbf" if bom else b"") + merged.encode("utf-8"))
        os.replace(tmp, path)
    except OSError:
        try:
            os.remove(tmp)
        except OSError:
            pass


def load():
    c = AppConfig()
    d, path = data_dir(), ini_path()
    ok = True
    try:
        os.makedirs(d, exist_ok=True)
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                f.write(DEFAULT_INI)
    except OSError:
        ok = False
    try:
        if os.path.exists(path):
            load_and_upgrade(c, path)
    except OSError:
        pass
    loc.apply(c.language)
    if not ok and not os.path.exists(path):
        c.errors.insert(0, loc.DataDirFailed(d))
    return c
