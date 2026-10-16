using System;
using System.Collections.Generic;
using System.IO;
using System.Net;
using System.Text;
using System.Text.RegularExpressions;

namespace MihomoTray
{
    /// <summary>mihomo external-controller REST API 的最小封装。</summary>
    public sealed class MihomoClient
    {
        private readonly string _base;
        private readonly string _secret;
        public int TimeoutMs = 2000;

        public MihomoClient(string controller, string secret)
        {
            _base = AppConfig.NormalizeController(controller);
            _secret = secret ?? "";
        }

        private HttpWebRequest Create(string method, string path)
        {
            HttpWebRequest req;
            try { req = (HttpWebRequest)WebRequest.Create(_base + path); }
            catch (Exception ex) { throw new MihomoException(Loc.InvalidController(_base), ex); }
            req.Method = method;
            req.Proxy = null;                 // 不走系统代理（系统代理可能就是 mihomo 自己）
            req.Timeout = TimeoutMs;
            req.ReadWriteTimeout = TimeoutMs;
            req.KeepAlive = false;
            req.UserAgent = "MihomoTray/2.1.9";
            if (_secret.Length > 0)
            {
                for (int i = 0; i < _secret.Length; i++)
                    if (_secret[i] > 127) throw new MihomoException(Loc.BadSecretChars, null);
                try { req.Headers[HttpRequestHeader.Authorization] = "Bearer " + _secret; }
                catch (Exception ex) { throw new MihomoException(Loc.BadSecretChars, ex); }
            }
            return req;
        }

        private static string Send(HttpWebRequest req, string jsonBody)
        {
            try
            {
                if (jsonBody != null)
                {
                    byte[] data = Encoding.UTF8.GetBytes(jsonBody);
                    req.ContentType = "application/json";
                    req.ContentLength = data.Length;
                    using (var s = req.GetRequestStream()) s.Write(data, 0, data.Length);
                }
                using (var resp = (HttpWebResponse)req.GetResponse())
                using (var sr = new StreamReader(resp.GetResponseStream(), Encoding.UTF8))
                    return sr.ReadToEnd();
            }
            catch (WebException ex)
            {
                var r = ex.Response as HttpWebResponse;
                if (r != null)
                {
                    int code = (int)r.StatusCode;
                    r.Close();
                    if (code == 401 || code == 403) throw new MihomoException(Loc.AuthFailed, ex);
                    throw new MihomoException(Loc.ControllerHttp(code), ex);
                }
                if (ex.Status == WebExceptionStatus.Timeout) throw new MihomoException(Loc.ControllerTimeout, ex);
                throw new MihomoException(Loc.CantConnect, ex);
            }
            catch (MihomoException) { throw; }
            catch (Exception ex)   // UriFormatException、非 ASCII 请求头等，统一包装成可读的提示
            {
                throw new MihomoException(Loc.ControllerRequestFailed(ex.Message), ex);
            }
        }

        /// <summary>返回 rule / global / direct（小写）。</summary>
        public string GetMode()
        {
            string body = Send(Create("GET", "/configs"), null);
            return ParseMode(body);
        }

        /// <summary>一次 GET /configs 同时拿到模式和 TUN 开关。</summary>
        public MihomoStatus GetStatus()
        {
            return ParseStatus(Send(Create("GET", "/configs"), null));
        }

        public static MihomoStatus ParseStatus(string json)
        {
            var st = new MihomoStatus();
            st.Mode = ParseMode(json);    // 无法解析时抛 MihomoException（视为未连接）
            st.TunEnabled = ParseTunEnabled(json);
            st.LogLevel = ParseLogLevel(json);
            return st;
        }

        /// <summary>
        /// 读最外层 "tun" 对象自己这一层的 "enable"（mihomo GetGeneral 返回 {"tun":{"enable":true,...},...}）。
        /// 其它对象里的 enable（如 tuic-server）不算；没有 tun 对象（老内核）视为关闭。
        /// </summary>
        public static bool ParseTunEnabled(string json)
        {
            string tun;
            if (!MiniJson.TopLevel(json).TryGetValue("tun", out tun) || !tun.StartsWith("{")) return false;
            string en;
            return MiniJson.TopLevel(tun).TryGetValue("enable", out en) && en == "true";
        }

        /// <summary>读最外层 "log-level"（silent/error/warning/info/debug）。没有或无法识别则返回空串。</summary>
        public static string ParseLogLevel(string json)
        {
            string v;
            if (!MiniJson.TopLevel(json).TryGetValue("log-level", out v) || v.Length < 2 || v[0] != '"') return "";
            return v.Substring(1, v.Length - 2).ToLowerInvariant();
        }

        public static string ParseMode(string json)
        {
            // 只认最外层的 "mode"，嵌套对象里同名字段不算（与 tun.enable 的解析方式一致）
            string v;
            if (!MiniJson.TopLevel(json).TryGetValue("mode", out v) || !Regex.IsMatch(v, "^\"[A-Za-z]+\"$"))
                throw new MihomoException(Loc.CantParseConfigs, null);
            return v.Substring(1, v.Length - 2).ToLowerInvariant();
        }

        public void SetMode(string mode)
        {
            Send(Create("PATCH", "/configs"), "{\"mode\":\"" + mode + "\"}");
        }

        public void CloseAllConnections()
        {
            Send(Create("DELETE", "/connections"), null);
        }
    }

    public sealed class MihomoStatus
    {
        public string Mode = "";
        public bool TunEnabled;
        public string LogLevel = "";
    }

    /// <summary>托盘悬停提示：3 行（模式 / 日志级别 / 虚拟网卡|TUN Mode）。NotifyIcon.Text 最长 63 字符。</summary>
    public static class TrayTip
    {
        public static string Offline { get { return Loc.Disconnected; } }

        public static string ModeLabel(string mode)
        {
            if (mode == "rule") return Loc.ModeRule;
            if (mode == "global") return Loc.ModeGlobal;
            if (mode == "direct") return Loc.ModeDirect;
            return mode ?? "";
        }

        public static string LogLabel(string level)
        {
            if (level == "silent") return Loc.LogSilent;
            if (level == "error") return Loc.LogError;
            if (level == "warning" || level == "warn") return Loc.LogWarning;
            if (level == "info") return Loc.LogInfo;
            if (level == "debug") return Loc.LogDebug;
            return Loc.Dash;  // 空或未知级别统一显示 —
        }

        public static string For(bool connected, string mode, bool tunEnabled, string logLevel)
        {
            string m = connected ? ModeLabel(mode) : Loc.Disconnected;
            string tun = connected ? (tunEnabled ? Loc.On : Loc.Off) : Loc.Dash;
            string log = connected ? LogLabel(logLevel) : Loc.Dash;
            if (connected && m.Length == 0) m = Loc.Dash;
            return Loc.TipMode + m + "\n"
                + Loc.TipLog + log + "\n"
                + Loc.TipTun + tun;
        }
    }

    /// <summary>极简 JSON 扫描：只取一个对象最外层的 key → 原始值文本（字符串带引号，对象/数组为整段子串）。</summary>
    public static class MiniJson
    {
        public static Dictionary<string, string> TopLevel(string json)
        {
            var d = new Dictionary<string, string>();
            if (json == null) return d;
            int i = SkipWs(json, 0);
            if (i >= json.Length || json[i] != '{') return d;
            i++;
            int n = json.Length;
            while (i < n)
            {
                i = SkipWs(json, i);
                if (i >= n || json[i] == '}') break;
                if (json[i] == ',') { i++; continue; }
                if (json[i] != '"') break;                      // 格式不对就停
                int ke = EndOfString(json, i);
                if (ke < 0) break;
                string key = json.Substring(i + 1, ke - i - 2);
                i = SkipWs(json, ke);
                if (i >= n || json[i] != ':') break;
                i = SkipWs(json, i + 1);
                int ve = EndOfValue(json, i);
                if (ve < 0) break;
                d[key] = json.Substring(i, ve - i).Trim();
                i = ve;
            }
            return d;
        }

        private static int SkipWs(string s, int i)
        {
            while (i < s.Length && char.IsWhiteSpace(s[i])) i++;
            return i;
        }

        /// <summary>s[i] 是开头的引号，返回结尾引号之后的位置。</summary>
        private static int EndOfString(string s, int i)
        {
            for (int j = i + 1; j < s.Length; j++)
            {
                if (s[j] == '\\') { j++; continue; }
                if (s[j] == '"') return j + 1;
            }
            return -1;
        }

        private static int EndOfValue(string s, int i)
        {
            if (i >= s.Length) return -1;
            if (s[i] == '"') return EndOfString(s, i);
            if (s[i] == '{' || s[i] == '[')
            {
                int depth = 0;
                for (int j = i; j < s.Length; j++)
                {
                    char c = s[j];
                    if (c == '"') { j = EndOfString(s, j); if (j < 0) return -1; j--; continue; }
                    if (c == '{' || c == '[') depth++;
                    else if (c == '}' || c == ']') { depth--; if (depth == 0) return j + 1; }
                }
                return -1;
            }
            int k = i;
            while (k < s.Length && s[k] != ',' && s[k] != '}' && s[k] != ']') k++;
            return k;
        }
    }

    public sealed class MihomoException : Exception
    {
        public MihomoException(string msg, Exception inner) : base(msg, inner) { }
    }
}
