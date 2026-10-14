"""界面文案，与 Windows 版 Loc.cs 保持一致（Linux 专属的几条单独标注）。
language = zh / en / system（跟随系统语言：zh 开头用中文，否则英文）。"""
import locale
import os

En = False


def system_is_zh():
    for var in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        v = os.environ.get(var, "")
        if v:
            # LANGUAGE 可以是 zh_CN:en_US 这样的列表，取第一个
            return v.split(":")[0].lower().startswith("zh")
    try:
        v = locale.getlocale()[0] or ""
    except Exception:
        v = ""
    return v.lower().startswith("zh")


def apply(preference):
    global En
    p = (preference or "system").strip().lower()
    if p == "en":
        En = True
    elif p in ("zh", "zh-cn", "zh-tw", "cn"):
        En = False
    else:
        try:
            En = not system_is_zh()
        except Exception:
            En = False


def _(en, zh):
    return en if En else zh


AppTitle = "MihomoTray"
def AlreadyRunning(): return _("MihomoTray is already running (check the system tray)", "MihomoTray 已在运行（请查看任务栏托盘）")
def FatalPrefix(): return _("MihomoTray hit an error and will exit:\n", "MihomoTray 遇到错误，即将退出：\n")
def UnknownError(): return _("Unknown error", "未知错误")

def OpenPanel(): return _("Dashboard", "打开面板")
def SwitchProgram(): return _("Open App", "切换程序")
def Exit(): return _("Exit", "退出")
def ModeRule(): return _("Rule", "规则模式")
def ModeGlobal(): return _("Global", "全局模式")
def ModeDirect(): return _("Direct", "直连模式")

def TipMode(): return _("Mode : ", "模式 : ")
def TipTun(): return _("TUN Mode : ", "虚拟网卡 : ")
def TipLog(): return _("Log Level : ", "日志级别 : ")
def Disconnected(): return _("Disconnected", "未连接")
def On(): return _("On", "开启")
def Off(): return _("Off", "关闭")
Dash = "—"

def LogSilent(): return _("Silent", "静默")
def LogError(): return _("Error", "错误")
def LogWarning(): return _("Warn", "警告")
def LogInfo(): return _("Info", "信息")
def LogDebug(): return _("Debug", "调试")

def BadConfig(): return _("Invalid config.ini", "config.ini 有误")
def SwitchFailed(): return _("Switch failed", "切换失败")
def ControllerLabel(): return _("Controller: ", "控制器：")
def CantOpenPanel(): return _("Couldn't open dashboard", "无法打开面板")
def CantOpenApp(): return _("Couldn't open app", "无法切换程序")
def SwitchNotSet(): return _("switch_program is not set in config.ini", "config.ini 中没有设置 switch_program")
def FileNotFound(path): return _("File not found: " + path + "\nCheck switch_program in config.ini", "找不到文件：" + path + "\n请检查 config.ini 中的 switch_program")

def AuthFailed(): return _("Authentication failed. Check the secret in config.ini", "鉴权失败，请检查 config.ini 中的 secret")
def CantConnect(): return _("Can't connect to the controller", "无法连接控制器")
def ControllerTimeout(): return _("Controller timed out", "控制器响应超时")
def ControllerHttp(code): return _("Controller returned HTTP %d" % code, "控制器返回 HTTP %d" % code)
def ControllerRequestFailed(msg): return _("Controller request failed: " + msg, "请求控制器失败：" + msg)
def InvalidController(addr): return _("Invalid controller address: " + addr, "controller 地址无效：" + addr)
def BadSecretChars(): return _("secret contains characters that can't be used in the request header (use ASCII letters, digits, and symbols only)", "secret 含有请求头不支持的字符（请只用英文字母、数字和符号）")
def CantParseConfigs(): return _("Can't parse /configs response", "无法解析 /configs 返回内容")

def AddrEmpty(): return _("Address is empty", "地址为空")
def OnlyHttp(): return _("Only http:// or https:// is supported (or omit the scheme and use 127.0.0.1:9090)", "只支持 http:// 或 https://（也可以不写，直接写 127.0.0.1:9090）")
def MissingPort(): return _("Missing port or bad format (use 127.0.0.1:9090)", "缺少端口或格式不对，应写成 127.0.0.1:9090 这样")
def PortRange(port): return _("Port %d is not in 1–65535" % port, "端口 %d 不在 1~65535 之间" % port)
def BadAddrFormat(): return _("Bad address format (use 127.0.0.1:9090)", "地址格式不对，应写成 127.0.0.1:9090 这样")
def BadPanelUrl(v): return _("panel_url = " + v + ": must start with http:// or https://", "panel_url = " + v + "：只支持 http:// 或 https:// 开头的网址")
def BadPoll(v, d): return _("poll_interval = %s: not a number, using default %d" % (v, d), "poll_interval = %s：不是数字，已使用默认值 %d" % (v, d))
def ExtraAfterQuote(k, rest): return _(k + ": ignored extra text after the closing quote: \u201c" + rest + "\u201d", k + "：引号后面多出的内容\u201c" + rest + "\u201d已忽略")
def AutostartFailed(): return _("Couldn't update autostart", "无法设置开机自启")

# ---- Linux 专属 ----
def DataDirFailed(path): return _("Could not create or write " + path + "; using defaults. Check folder permissions", "无法创建或写入 " + path + "，已使用默认配置，请检查目录权限")
def NotExecutable(path): return _("Not executable: " + path + "\nRun chmod +x or check switch_program in config.ini", "文件没有执行权限：" + path + "\n请 chmod +x 或检查 config.ini 中的 switch_program")
