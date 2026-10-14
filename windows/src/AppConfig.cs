using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Windows.Forms;

namespace MihomoTray
{
    /// <summary>读取 exe 同目录 Data 文件夹里的 config.ini（不存在则自动生成默认配置）。</summary>
    public sealed class AppConfig
    {
        public string Controller = "http://127.0.0.1:9090";
        public string Secret = "";
        public string PanelUrl = "http://127.0.0.1:9090/ui/";
        public string SwitchProgram = "";      // 原始配置值（未展开）
        public string SwitchProgramArgs = "";
        public int PollSeconds = 3;
        public bool CloseConnections = true;
        public const string DefaultTheme = "light";   // 与 FlClash 原版一致：不开启深色菜单
        public string Theme = DefaultTheme;             // system | light | dark
        public const string DefaultLanguage = "system"; // system | zh | en
        public string Language = DefaultLanguage;
        public bool Autostart = false;                  // 开机自启，默认关闭，只能在 config.ini 里手动开启
        /// <summary>解析 config.ini 时发现的问题（启动时用气泡提示一次）。</summary>
        public readonly List<string> Errors = new List<string>();

        public const string DefaultIni =
"; MihomoTray 配置文件（修改后重启小工具生效）\r\n" +
"; MihomoTray config (restart the tray app after editing)\r\n" +
"[mihomo]\r\n" +
"; external-controller 地址\r\n" +
"; external-controller address\r\n" +
"controller = 127.0.0.1:9090\r\n" +
"; external-controller 的 secret，没有就留空（请只用 ASCII 字母、数字和符号）\r\n" +
"; secret for external-controller (leave empty if none; ASCII letters/digits/symbols only)\r\n" +
"secret = \r\n" +
"; 点击“打开面板”时打开的网址\r\n" +
"; URL opened by Dashboard / left-click\r\n" +
"panel_url = http://127.0.0.1:9090/ui/\r\n" +
"; 点击“切换程序”时启动的程序（通常是某个 mihomo 内核图形客户端的主程序，.exe 或 .lnk 快捷方式都行），留空则该菜单项变灰\r\n" +
"; Program launched by Open App (usually a mihomo GUI client .exe or .lnk); leave empty to gray out the item\r\n" +
"; 支持带空格/带引号的路径、环境变量（如 %LOCALAPPDATA%）、相对路径（相对本小工具 exe 所在文件夹）\r\n" +
"; Paths may contain spaces/quotes, env vars (e.g. %LOCALAPPDATA%), or be relative to this app's folder\r\n" +
"; 例：switch_program = C:\\Program Files\\FlClash\\FlClash.exe\r\n" +
"; Example: switch_program = C:\\Program Files\\FlClash\\FlClash.exe\r\n" +
";     switch_program = %LOCALAPPDATA%\\Programs\\某客户端\\某客户端.exe\r\n" +
";     switch_program = %LOCALAPPDATA%\\Programs\\SomeClient\\SomeClient.exe\r\n" +
"switch_program = \r\n" +
"; 启动上面程序时附带的命令行参数，一般留空\r\n" +
"; Extra command-line args for the program above (usually empty)\r\n" +
"switch_program_args = \r\n" +
"; 轮询当前模式的间隔（秒）\r\n" +
"; Poll interval for current mode (seconds)\r\n" +
"poll_interval = 3\r\n" +
"; 切换模式后是否断开现有连接，让已建立的连接也立即按新模式走（设为 false 则只影响新连接）\r\n" +
"; Close existing connections after switching mode (false = only new connections use the new mode)\r\n" +
"close_connections = true\r\n" +
"\r\n" +
"[ui]\r\n" +
"; 界面语言：system（跟随系统）/ zh（中文）/ en（英文）\r\n" +
"; UI language: system (follow OS) / zh (Chinese) / en (English)\r\n" +
"language = system\r\n" +
"; 菜单主题：system（跟随系统）/ light（浅色）/ dark（深色）\r\n" +
"; Menu theme: system (follow OS) / light / dark\r\n" +
"; light 与 FlClash 原版一致（原版不启用深色菜单，始终是系统浅色菜单）\r\n" +
"; light matches FlClash (native menu stays light even if the OS is dark)\r\n" +
"theme = {theme}\r\n" +
"; 开机自启：true（开启）/ false（关闭，默认）；每次启动时按这里同步系统设置\r\n" +
"; Start with Windows: true / false (default); synced to the system on every start\r\n" +
"autostart = false\r\n";

        public static string DefaultIniFor(string theme)
        {
            return DefaultIni.Replace("{theme}", theme);
        }

        /// <summary>exe 同目录下的 Data 文件夹：放 config.ini、MihomoTray.exe.config 和 Icons\。</summary>
        public static string DataDir
        {
            get { return Path.Combine(Path.GetDirectoryName(Application.ExecutablePath), "Data"); }
        }

        public static string IconsDir
        {
            get { return Path.Combine(DataDir, "Icons"); }
        }

        public static string IniPath
        {
            get { return Path.Combine(DataDir, "config.ini"); }
        }

        /// <summary>建好 Data 文件夹；旧版本放在 exe 旁边的 config.ini 挪进 Data（Data 里已有就不动）。失败返回 false。</summary>
        public static bool PrepareDataDir()
        {
            try
            {
                Directory.CreateDirectory(DataDir);
                string old = Path.Combine(ExeDir, "config.ini");
                if (File.Exists(old) && !File.Exists(IniPath)) File.Move(old, IniPath);
                return Directory.Exists(DataDir);
            }
            catch { return false; }
        }

        public static AppConfig Load()
        {
            bool dataOk = PrepareDataDir();
            var c = new AppConfig();
            string path = IniPath;
            string legacy = Path.Combine(ExeDir, "config.ini");
            bool usedLegacy = false;
            try
            {
                // C1：Data 写不进时，仍可读 exe 旁旧 config.ini，避免静默丢掉用户配置
                if (!File.Exists(path) && File.Exists(legacy))
                {
                    path = legacy;
                    usedLegacy = true;
                }
                else if (!File.Exists(path))
                {
                    if (dataOk)
                        File.WriteAllText(path, DefaultIniFor(DefaultTheme), new UTF8Encoding(true));
                }
            }
            catch { }
            try
            {
                if (File.Exists(path)) LoadAndUpgrade(c, path);
            }
            catch { }
            Loc.Apply(c.Language);
            if (usedLegacy)
                c.Errors.Insert(0, Loc.DataDirFallback);
            else if (!dataOk && !File.Exists(IniPath) && !File.Exists(legacy))
                c.Errors.Insert(0, Loc.DataDirFailed);
            return c;
        }

        /// <summary>
        /// 读取并解析 config.ini，必要时补上新版本的配置项：
        /// - 能按 UTF-8 严格解码：把缺的键插到所属小节末尾，保留原来的 BOM 和换行风格（CRLF / LF），先写临时文件再替换；
        /// - 解不开（比如记事本另存为 ANSI/GBK）：按系统默认编码读，只在文件末尾追加，原有字节一个都不改。
        /// </summary>
        public static void LoadAndUpgrade(AppConfig c, string path)
        {
            byte[] bytes = File.ReadAllBytes(path);
            bool bom = bytes.Length >= 3 && bytes[0] == 0xEF && bytes[1] == 0xBB && bytes[2] == 0xBF;
            string text; bool utf8 = true;
            try { text = new UTF8Encoding(false, true).GetString(bytes, bom ? 3 : 0, bytes.Length - (bom ? 3 : 0)); }
            catch (DecoderFallbackException) { text = Encoding.Default.GetString(bytes); utf8 = false; }
            string nl = text.Contains("\r\n") || !text.Contains("\n") ? "\r\n" : "\n";
            string[] lines = text.Replace("\r\n", "\n").Split('\n');
            c.Parse(lines);
            string def = DefaultIniFor(DefaultTheme);
            try
            {
                // 用户把 config.ini 设成只读，就不去动它
                if ((File.GetAttributes(path) & FileAttributes.ReadOnly) != 0) return;
                if (utf8)
                {
                    string merged = MergeMissingKeys(lines, def);
                    if (merged == null) return;
                    if (nl == "\n") merged = merged.Replace("\r\n", "\n");
                    byte[] outBytes = new UTF8Encoding(bom).GetPreamble();
                    byte[] body = new UTF8Encoding(false).GetBytes(merged);
                    var all = new byte[outBytes.Length + body.Length];
                    Buffer.BlockCopy(outBytes, 0, all, 0, outBytes.Length);
                    Buffer.BlockCopy(body, 0, all, outBytes.Length, body.Length);
                    SafeWrite(path, all);
                }
                else
                {
                    string add = AsciiOnly(MissingKeysBlock(lines, def));
                    if (add.Length == 0) return;
                    if (nl == "\n") add = add.Replace("\r\n", "\n");
                    string lead = (text.Length == 0 || text.EndsWith("\n")) ? "" : nl;
                    byte[] tail = Encoding.Default.GetBytes(lead + add);
                    var all = new byte[bytes.Length + tail.Length];
                    Buffer.BlockCopy(bytes, 0, all, 0, bytes.Length);
                    Buffer.BlockCopy(tail, 0, all, bytes.Length, tail.Length);
                    SafeWrite(path, all);
                }
            }
            catch { }   // 写不进去（只读目录等）就算了，不影响使用
        }

        /// <summary>
        /// 非 UTF-8 文件追加用：只保留纯 ASCII 的行（中文注释去掉，换成一句英文说明），
        /// 这样不管系统代码页是 GBK、UTF-8 还是别的，追加的字节在原文件的编码下都读得对。
        /// </summary>
        public static string AsciiOnly(string block)
        {
            if (block.Length == 0) return "";
            var sb = new StringBuilder();
            bool any = false;
            foreach (var l in block.Replace("\r\n", "\n").Split('\n'))
            {
                bool ascii = true;
                foreach (char ch in l) if (ch > 127) { ascii = false; break; }
                if (!ascii) continue;
                if (KeyOf(l) != null) any = true;
                if (l.Length > 0) sb.Append(l).Append("\r\n");
            }
            if (!any) return "";
            return "\r\n; ---- added by a newer version, see README.txt ----\r\n" + sb.ToString();
        }

        /// <summary>先写到同目录的临时文件，写完整后再替换原文件，避免中途失败把 config.ini 写坏。</summary>
        private static void SafeWrite(string path, byte[] data)
        {
            string tmp = path + ".tmp";
            try
            {
                File.WriteAllBytes(tmp, data);
                try { File.Replace(tmp, path, null); }
                catch (PlatformNotSupportedException) { File.Copy(tmp, path, true); }
                catch (IOException) { File.Copy(tmp, path, true); }
            }
            finally
            {
                try { if (File.Exists(tmp)) File.Delete(tmp); } catch { }
            }
        }

        public void Parse(IEnumerable<string> lines)
        {
            var list = new List<string>(lines);
            // 先读 language，再生成其它校验文案
            foreach (var raw in list)
            {
                string line = raw.Trim();
                if (line.Length == 0 || line[0] == ';' || line[0] == '#' || line[0] == '[') continue;
                int eq = line.IndexOf('=');
                if (eq <= 0) continue;
                string k = line.Substring(0, eq).Trim().ToLowerInvariant();
                if (k != "language") continue;
                string langRest; string v = Unquote(StripComment(line.Substring(eq + 1).Trim()), out langRest);
                v = v.ToLowerInvariant();
                if (v == "system" || v == "zh" || v == "en") Language = v;
            }
            Loc.Apply(Language);

            foreach (var raw in list)
            {
                string line = raw.Trim();
                if (line.Length == 0 || line[0] == ';' || line[0] == '#' || line[0] == '[') continue;
                int eq = line.IndexOf('=');
                if (eq <= 0) continue;
                string k = line.Substring(0, eq).Trim().ToLowerInvariant();
                string value = line.Substring(eq + 1).Trim();
                // secret 整行都算密钥（兼容老配置里含“空格+;”的密钥）；其它项去掉行尾注释（“ ;”或“ #”之后）
                string rawValue = k == "secret" ? value : StripComment(value);
                string rest;
                string v = Unquote(rawValue, out rest);
                if (k == "secret")
                {
                    // 和老版本一致：首尾都是引号时只去掉最外层引号（"a"b" -> a"b），其余情况整行原样当密钥
                    v = value.Length >= 2 && value[0] == '"' && value[value.Length - 1] == '"'
                        ? value.Substring(1, value.Length - 2) : value;
                    rest = "";
                }
                if (rest.Length > 0 && k != "switch_program" && k != "switch_program_args")
                    Errors.Add(Loc.ExtraAfterQuote(k, rest));
                switch (k)
                {
                    case "controller":
                        if (v.Length > 0)
                        {
                            string err;
                            string norm = TryNormalizeController(v, out err);
                            if (norm != null) Controller = norm;
                            else Errors.Add("controller = " + v + (Loc.En ? ": " : "：") + err);
                        }
                        break;
                    case "secret": Secret = v; break;
                    case "panel_url":
                        if (v.Length > 0)
                        {
                            Uri u;
                            if (Uri.TryCreate(v, UriKind.Absolute, out u) && (u.Scheme == "http" || u.Scheme == "https")) PanelUrl = v;
                            else Errors.Add(Loc.BadPanelUrl(v));
                        }
                        break;
                    case "switch_program":
                        SwitchProgram = v.Trim();
                        // 写成 "C:\a b\x.exe" --min 时，引号后面的部分当作参数
                        if (rest.Length > 0) SwitchProgramArgsInline = rest;
                        break;
                    case "switch_program_args": SwitchProgramArgs = rawValue; break;
                    case "poll_interval":
                        int n;
                        if (int.TryParse(v, out n)) PollSeconds = Math.Max(1, Math.Min(60, n));
                        else Errors.Add(Loc.BadPoll(v, PollSeconds));
                        break;
                    case "close_connections":
                        v = v.ToLowerInvariant();
                        CloseConnections = !(v == "false" || v == "0" || v == "no" || v == "off");
                        break;
                    case "autostart":
                        v = v.ToLowerInvariant();
                        Autostart = v == "true" || v == "1" || v == "yes" || v == "on";
                        break;
                    case "theme":
                        v = v.ToLowerInvariant();
                        if (v == "system" || v == "light" || v == "dark") Theme = v;
                        break;
                    case "language":
                        break; // 已在第一遍处理
                }
            }
        }

        private static string KeyOf(string line)
        {
            line = line.Trim();
            if (line.Length == 0 || line[0] == ';' || line[0] == '#' || line[0] == '[') return null;
            int eq = line.IndexOf('=');
            return eq <= 0 ? null : line.Substring(0, eq).Trim().ToLowerInvariant();
        }

        /// <summary>默认配置里有、existing 里没有的键：返回要追加的文本（每个键带上它前面的注释行），都不缺则返回空串。</summary>
        public static string MissingKeysBlock(IEnumerable<string> existing, string defaultIni)
        {
            var have = new HashSet<string>();
            foreach (var l in existing) { string k = KeyOf(l); if (k != null) have.Add(k); }
            var sb = new StringBuilder();
            var comments = new List<string>();
            foreach (var raw in defaultIni.Replace("\r\n", "\n").Split('\n'))
            {
                string t = raw.Trim();
                if (t.StartsWith(";")) { comments.Add(raw); continue; }
                string k = KeyOf(raw);
                if (k != null && !have.Contains(k))
                {
                    foreach (var cm in comments) sb.Append(cm).Append("\r\n");
                    sb.Append(raw).Append("\r\n");
                }
                comments.Clear();
            }
            if (sb.Length == 0) return "";
            return "\r\n; ---- 以下为新版本增加的配置项（自动追加）----\r\n" + sb.ToString();
        }

        private static string SectionOf(string line)
        {
            string t = line.Trim();
            if (t.Length >= 2 && t[0] == '[' && t[t.Length - 1] == ']') return t.Substring(1, t.Length - 2).Trim().ToLowerInvariant();
            return null;
        }

        /// <summary>
        /// 把默认配置里有、现有文件里没有的键（连同前面的注释）插到现有文件里对应小节的末尾；
        /// 现有文件没有这个小节就在文件末尾新建。都不缺时返回 null。返回的是整个文件的新内容（CRLF）。
        /// </summary>
        public static string MergeMissingKeys(IList<string> existing, string defaultIni)
        {
            var have = new HashSet<string>();
            foreach (var l in existing) { string k = KeyOf(l); if (k != null) have.Add(k); }
            // 默认配置里每个小节缺的内容
            var order = new List<string>();
            var blocks = new Dictionary<string, StringBuilder>();
            string sec = "";
            var comments = new List<string>();
            foreach (var raw in defaultIni.Replace("\r\n", "\n").Split('\n'))
            {
                string s = SectionOf(raw);
                if (s != null) { sec = s; comments.Clear(); continue; }
                if (raw.Trim().StartsWith(";")) { comments.Add(raw); continue; }
                string k = KeyOf(raw);
                if (k != null && !have.Contains(k))
                {
                    StringBuilder b;
                    if (!blocks.TryGetValue(sec, out b)) { b = new StringBuilder(); blocks[sec] = b; order.Add(sec); }
                    foreach (var cm in comments) b.Append(cm).Append("\r\n");
                    b.Append(raw).Append("\r\n");
                }
                comments.Clear();
            }
            if (order.Count == 0) return null;
            var lines = new List<string>(existing);
            while (lines.Count > 0 && lines[lines.Count - 1].Trim().Length == 0) lines.RemoveAt(lines.Count - 1);
            foreach (var s in order)
            {
                string text = blocks[s].ToString().TrimEnd('\r', '\n');
                var add = new List<string>(text.Replace("\r\n", "\n").Split('\n'));
                // 找到这个小节：它最后一个非空行之后插入
                int start = -1;
                for (int i = 0; i < lines.Count; i++) { if (SectionOf(lines[i]) == s) { start = i; break; } }
                if (start < 0 && s.Length > 0)
                {
                    lines.Add("");
                    lines.Add("[" + s + "]");
                    lines.AddRange(add);
                    continue;
                }
                int end = lines.Count;   // 下一个小节开始的位置
                for (int i = start + 1; i < lines.Count; i++) if (SectionOf(lines[i]) != null) { end = i; break; }
                int insertAt = end;
                while (insertAt - 1 > start && lines[insertAt - 1].Trim().Length == 0) insertAt--;
                lines.InsertRange(insertAt, add);
            }
            return string.Join("\r\n", lines.ToArray()) + "\r\n";
        }

        public bool HasSwitchProgram { get { return SwitchProgram.Length > 0; } }
        private string SwitchProgramArgsInline = "";
        /// <summary>最终传给程序的参数：switch_program 引号后面的部分 + switch_program_args。</summary>
        public string EffectiveSwitchArgs
        {
            get
            {
                if (SwitchProgramArgsInline.Length == 0) return SwitchProgramArgs;
                if (SwitchProgramArgs.Length == 0) return SwitchProgramArgsInline;
                return SwitchProgramArgsInline + " " + SwitchProgramArgs;
            }
        }

        /// <summary>去掉不在引号里的行尾注释：前面有空白的 ; 或 # 及其后面的内容。</summary>
        public static string StripComment(string v)
        {
            bool inQ = false;
            for (int i = 0; i < v.Length; i++)
            {
                char c = v[i];
                if (c == '"') inQ = !inQ;
                else if (!inQ && (c == ';' || c == '#') && i > 0 && char.IsWhiteSpace(v[i - 1]))
                    return v.Substring(0, i).TrimEnd();
            }
            return v;
        }

        /// <summary>以引号开头时取引号内的内容，引号后面剩下的放进 rest；否则原样返回。</summary>
        public static string Unquote(string v, out string rest)
        {
            rest = "";
            if (v.Length >= 1 && v[0] == '"')
            {
                int end = v.IndexOf('"', 1);
                if (end > 0)
                {
                    rest = v.Substring(end + 1).Trim();
                    return v.Substring(1, end - 1);
                }
            }
            return v;
        }

        /// <summary>展开环境变量；相对路径按 baseDir（exe 所在文件夹）解析。空值返回 null。</summary>
        public static string ResolveProgramPath(string raw, string baseDir)
        {
            if (raw == null) return null;
            string rest;
            string p = Unquote(raw.Trim(), out rest).Trim().Trim('"').Trim();
            if (p.Length == 0) return null;
            p = Environment.ExpandEnvironmentVariables(p);
            try
            {
                if (!Path.IsPathRooted(p)) p = Path.Combine(baseDir, p);
                p = Path.GetFullPath(p);
            }
            catch { }
            return p;
        }

        public static string ExeDir
        {
            get { return Path.GetDirectoryName(Application.ExecutablePath); }
        }

        public static string NormalizeController(string v)
        {
            string err;
            string r = TryNormalizeController(v, out err);
            return r ?? BasicNormalize(v);
        }

        private static string BasicNormalize(string v)
        {
            v = v.Trim().TrimEnd('/');
            if (!v.StartsWith("http://", StringComparison.OrdinalIgnoreCase) &&
                !v.StartsWith("https://", StringComparison.OrdinalIgnoreCase))
                v = "http://" + v;
            return v;
        }

        /// <summary>
        /// 规范化 controller：补 http://；“:9090”（mihomo 里监听所有地址的写法）、0.0.0.0、[::] 改成 127.0.0.1；
        /// 校验是不是合法地址，不合法返回 null 并给出原因。
        /// </summary>
        public static string TryNormalizeController(string v, out string error)
        {
            error = null;
            v = (v ?? "").Trim();
            if (v.Length == 0) { error = Loc.AddrEmpty; return null; }
            string scheme = "http://";
            if (v.StartsWith("http://", StringComparison.OrdinalIgnoreCase)) v = v.Substring(7);
            else if (v.StartsWith("https://", StringComparison.OrdinalIgnoreCase)) { scheme = "https://"; v = v.Substring(8); }
            else if (v.IndexOf("://", StringComparison.Ordinal) >= 0)
            {
                error = Loc.OnlyHttp;
                return null;
            }
            v = v.TrimEnd('/');
            if (v == "0.0.0.0" || v == "[::]" || v == "::") v = "127.0.0.1";
            else if (v.StartsWith(":")) v = "127.0.0.1" + v;
            else if (v.StartsWith("0.0.0.0:")) v = "127.0.0.1" + v.Substring(7);
            else if (v.StartsWith("[::]:")) v = "127.0.0.1" + v.Substring(4);
            string hostPort = v;
            int slash = hostPort.IndexOf('/');
            if (slash >= 0) hostPort = hostPort.Substring(0, slash);
            var pm = System.Text.RegularExpressions.Regex.Match(hostPort, @"^(\[[0-9A-Fa-f:.]+\]|[^:\[\]]+):(\d{1,5})$");
            if (!pm.Success)
            {
                error = Loc.MissingPort;
                return null;
            }
            int port = int.Parse(pm.Groups[2].Value);
            if (port < 1 || port > 65535) { error = Loc.PortRange(port); return null; }
            string url = scheme + v;
            Uri u;
            if (!Uri.TryCreate(url, UriKind.Absolute, out u) || u.Host.Length == 0 || v.IndexOf(' ') >= 0)
            {
                error = Loc.BadAddrFormat;
                return null;
            }
            return url;
        }
    }
}
