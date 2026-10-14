using System;
using System.Globalization;

namespace MihomoTray
{
    /// <summary>界面文案。language = zh / en / system（跟随系统 UI 语言，非中文则用英文）。</summary>
    public static class Loc
    {
        public static bool En;

        public static void Apply(string preference)
        {
            string p = (preference ?? "system").Trim().ToLowerInvariant();
            if (p == "en") En = true;
            else if (p == "zh" || p == "zh-cn" || p == "zh-tw" || p == "cn") En = false;
            else
            {
                try { En = !CultureInfo.CurrentUICulture.TwoLetterISOLanguageName.Equals("zh", StringComparison.OrdinalIgnoreCase); }
                catch { En = false; }
            }
        }

        public static string AppTitle { get { return "MihomoTray"; } }
        public static string AlreadyRunning { get { return En ? "MihomoTray is already running (check the system tray)" : "MihomoTray 已在运行（请查看任务栏托盘）"; } }
        public static string FatalPrefix { get { return En ? "MihomoTray hit an error and will exit:\n" : "MihomoTray 遇到错误，即将退出：\n"; } }
        public static string UnknownError { get { return En ? "Unknown error" : "未知错误"; } }

        public static string OpenPanel { get { return En ? "Dashboard" : "打开面板"; } }
        public static string SwitchProgram { get { return En ? "Open App" : "切换程序"; } }
        public static string Exit { get { return En ? "Exit" : "退出"; } }
        public static string ModeRule { get { return En ? "Rule" : "规则模式"; } }
        public static string ModeGlobal { get { return En ? "Global" : "全局模式"; } }
        public static string ModeDirect { get { return En ? "Direct" : "直连模式"; } }

        public static string TipMode { get { return En ? "Mode : " : "模式 : "; } }
        public static string TipTun { get { return En ? "TUN Mode : " : "虚拟网卡 : "; } }
        public static string TipLog { get { return En ? "Log Level : " : "日志级别 : "; } }
        public static string Disconnected { get { return En ? "Disconnected" : "未连接"; } }
        public static string On { get { return En ? "On" : "开启"; } }
        public static string Off { get { return En ? "Off" : "关闭"; } }
        public static string Dash { get { return "—"; } }

        public static string LogSilent { get { return En ? "Silent" : "静默"; } }
        public static string LogError { get { return En ? "Error" : "错误"; } }
        public static string LogWarning { get { return En ? "Warn" : "警告"; } }
        public static string LogInfo { get { return En ? "Info" : "信息"; } }
        public static string LogDebug { get { return En ? "Debug" : "调试"; } }

        public static string BadConfig { get { return En ? "Invalid config.ini" : "config.ini 有误"; } }
        public static string SwitchFailed { get { return En ? "Switch failed" : "切换失败"; } }
        public static string ControllerLabel { get { return En ? "Controller: " : "控制器："; } }
        public static string CantOpenPanel { get { return En ? "Couldn't open dashboard" : "无法打开面板"; } }
        public static string CantOpenApp { get { return En ? "Couldn't open app" : "无法切换程序"; } }
        public static string SwitchNotSet { get { return En ? "switch_program is not set in config.ini" : "config.ini 中没有设置 switch_program"; } }
        public static string FileNotFound(string path) { return En ? ("File not found: " + path + "\nCheck switch_program in config.ini") : ("找不到文件：" + path + "\n请检查 config.ini 中的 switch_program"); }
        public static string UacDenied { get { return En ? "Cancelled (UAC elevation was denied)" : "已取消（管理员权限确认被拒绝）"; } }

        public static string AuthFailed { get { return En ? "Authentication failed. Check the secret in config.ini" : "鉴权失败，请检查 config.ini 中的 secret"; } }
        public static string CantConnect { get { return En ? "Can't connect to the controller" : "无法连接控制器"; } }
        public static string ControllerTimeout { get { return En ? "Controller timed out" : "控制器响应超时"; } }
        public static string ControllerHttp(int code) { return En ? ("Controller returned HTTP " + code) : ("控制器返回 HTTP " + code); }
        public static string ControllerRequestFailed(string msg) { return En ? ("Controller request failed: " + msg) : ("请求控制器失败：" + msg); }
        public static string InvalidController(string addr) { return En ? ("Invalid controller address: " + addr) : ("controller 地址无效：" + addr); }
        public static string BadSecretChars { get { return En ? "secret contains characters that can't be used in the request header (use ASCII letters, digits, and symbols only)" : "secret 含有请求头不支持的字符（请只用英文字母、数字和符号）"; } }
        public static string CantParseConfigs { get { return En ? "Can't parse /configs response" : "无法解析 /configs 返回内容"; } }

        public static string AddrEmpty { get { return En ? "Address is empty" : "地址为空"; } }
        public static string OnlyHttp { get { return En ? "Only http:// or https:// is supported (or omit the scheme and use 127.0.0.1:9090)" : "只支持 http:// 或 https://（也可以不写，直接写 127.0.0.1:9090）"; } }
        public static string MissingPort { get { return En ? "Missing port or bad format (use 127.0.0.1:9090)" : "缺少端口或格式不对，应写成 127.0.0.1:9090 这样"; } }
        public static string PortRange(int port) { return En ? ("Port " + port + " is not in 1–65535") : ("端口 " + port + " 不在 1~65535 之间"); }
        public static string BadAddrFormat { get { return En ? "Bad address format (use 127.0.0.1:9090)" : "地址格式不对，应写成 127.0.0.1:9090 这样"; } }
        public static string BadPanelUrl(string v) { return En ? ("panel_url = " + v + ": must start with http:// or https://") : ("panel_url = " + v + "：只支持 http:// 或 https:// 开头的网址"); }
        public static string BadPoll(string v, int def) { return En ? ("poll_interval = " + v + ": not a number, using default " + def) : ("poll_interval = " + v + "：不是数字，已使用默认值 " + def); }
        public static string DataDirFailed { get { return En ? "Could not create or write the Data folder; using defaults. Check folder permissions (e.g. not under Program Files without write access)." : "无法创建或写入 Data 文件夹，已使用默认配置，请检查目录权限（例如不要把程序放在无写权限的 Program Files 下）"; } }
        public static string DataDirFallback { get { return En ? "Could not move config into the Data folder; reading the old config.ini next to the exe. Prefer fixing permissions so Data\\config.ini can be used." : "无法把配置迁入 Data 文件夹，已临时读取 exe 旁旧版 config.ini，建议修好目录权限后使用 Data\\config.ini"; } }
        public static string AutostartFailed { get { return En ? "Couldn't update autostart" : "无法设置开机自启"; } }
        public static string ExtraAfterQuote(string k, string rest) { return En ? (k + ": ignored extra text after the closing quote: \u201c" + rest + "\u201d") : (k + "：引号后面多出的内容\u201c" + rest + "\u201d已忽略"); }
    }
}
