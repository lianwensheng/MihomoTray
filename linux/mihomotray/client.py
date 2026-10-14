"""mihomo external-controller REST API 的最小封装（对应 Windows 版 MihomoClient.cs）。"""
import json
import re
import socket
import urllib.error
import urllib.request

from . import __version__, loc
from .config import normalize_controller


class MihomoError(Exception):
    pass


class MihomoStatus:
    def __init__(self, mode="", tun_enabled=False, log_level=""):
        self.mode, self.tun_enabled, self.log_level = mode, tun_enabled, log_level


# 不走系统代理（系统代理可能就是 mihomo 自己）
_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def _top(body):
    try:
        d = json.loads(body)
    except (ValueError, TypeError):
        return {}
    return d if isinstance(d, dict) else {}


def parse_mode(body):
    v = _top(body).get("mode")
    if not isinstance(v, str) or not re.fullmatch(r"[A-Za-z]+", v):
        raise MihomoError(loc.CantParseConfigs())
    return v.lower()


def parse_tun_enabled(body):
    tun = _top(body).get("tun")
    return isinstance(tun, dict) and tun.get("enable") is True


def parse_log_level(body):
    v = _top(body).get("log-level")
    return v.lower() if isinstance(v, str) else ""


def parse_status(body):
    return MihomoStatus(parse_mode(body), parse_tun_enabled(body), parse_log_level(body))


class MihomoClient:
    def __init__(self, controller, secret, timeout=2.0):
        self.base = normalize_controller(controller)
        self.secret = secret or ""
        self.timeout = timeout

    def _send(self, method, path, body=None):
        headers = {"User-Agent": "MihomoTray/" + __version__}
        if self.secret:
            if any(ord(ch) > 127 for ch in self.secret):
                raise MihomoError(loc.BadSecretChars())
            headers["Authorization"] = "Bearer " + self.secret
        data = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        try:
            req = urllib.request.Request(self.base + path, data=data, method=method, headers=headers)
        except ValueError as e:
            raise MihomoError(loc.InvalidController(self.base)) from e
        try:
            with _opener.open(req, timeout=self.timeout) as r:
                return r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                raise MihomoError(loc.AuthFailed()) from e
            raise MihomoError(loc.ControllerHttp(e.code)) from e
        except urllib.error.URLError as e:
            if isinstance(e.reason, (socket.timeout, TimeoutError)):
                raise MihomoError(loc.ControllerTimeout()) from e
            raise MihomoError(loc.CantConnect()) from e
        except (socket.timeout, TimeoutError) as e:
            raise MihomoError(loc.ControllerTimeout()) from e
        except (ConnectionError, OSError) as e:
            raise MihomoError(loc.CantConnect()) from e
        except Exception as e:  # 统一包装成可读提示
            raise MihomoError(loc.ControllerRequestFailed(str(e))) from e

    def get_mode(self):
        return parse_mode(self._send("GET", "/configs"))

    def get_status(self):
        return parse_status(self._send("GET", "/configs"))

    def set_mode(self, mode):
        self._send("PATCH", "/configs", {"mode": mode})

    def close_all_connections(self):
        self._send("DELETE", "/connections")


def mode_label(mode):
    return {"rule": loc.ModeRule(), "global": loc.ModeGlobal(), "direct": loc.ModeDirect()}.get(mode, mode or "")


def log_label(level):
    return {"silent": loc.LogSilent(), "error": loc.LogError(), "warning": loc.LogWarning(), "warn": loc.LogWarning(),
            "info": loc.LogInfo(), "debug": loc.LogDebug()}.get(level, loc.Dash)


def tray_tip(connected, mode, tun_enabled, log_level):
    """悬停提示 3 行（模式 / 日志级别 / 虚拟网卡），和 Windows 版 TrayTip.For 一样，最长 63 字符。"""
    m = mode_label(mode) if connected else loc.Disconnected()
    tun = (loc.On() if tun_enabled else loc.Off()) if connected else loc.Dash
    log = log_label(log_level) if connected else loc.Dash
    if connected and not m:
        m = loc.Dash
    t = loc.TipMode() + m + "\n" + loc.TipLog() + log + "\n" + loc.TipTun() + tun
    return t[:63]
