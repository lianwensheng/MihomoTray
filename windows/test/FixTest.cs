// 第 2 轮测试报告里 M3 / N4 / N5 / N7 / L1 / L2 的回归测试
using System; using System.Collections.Generic; using MihomoTray;
class FixTest {
  static int fails;
  static void Check(bool ok, string name){ Console.WriteLine((ok?"PASS ":"FAIL ")+name); if(!ok) fails++; }
  static AppConfig P(params string[] l){ var c=new AppConfig(); c.Parse(l); Loc.Apply("zh"); return c; }
  static int Main(){
    Loc.Apply("zh");
    // M3 controller 规范化
    Check(P("controller = :9090").Controller=="http://127.0.0.1:9090", ":9090 -> 127.0.0.1");
    Check(P("controller = 0.0.0.0:9090").Controller=="http://127.0.0.1:9090", "0.0.0.0 -> 127.0.0.1");
    Check(P("controller = [::]:9090").Controller=="http://127.0.0.1:9090", "[::] -> 127.0.0.1");
    Check(P("controller = 127.0.0.1:9090 ; 注释").Controller=="http://127.0.0.1:9090", "controller 行尾 ; 注释");
    Check(P("controller = https://router.lan:9443/").Controller=="https://router.lan:9443", "https 保留");
    var bad=P("controller = 127.0.0.1:abc"); Check(bad.Controller=="http://127.0.0.1:9090" && bad.Errors.Count==1, "非法 controller 保留默认并报错："+string.Join("|",bad.Errors.ToArray()));
    var pi=P("poll_interval = 5 # seconds"); Check(pi.PollSeconds==5 && pi.Errors.Count==0, "poll_interval 行尾 # 注释");
    var pi2=P("poll_interval = abc"); Check(pi2.PollSeconds==3 && pi2.Errors.Count==1, "poll_interval 非数字报错");
    Check(P("secret = \"a;b #c\"").Secret=="a;b #c", "带引号的 secret 保留 ; #");
    Check(P("secret = abc;def").Secret=="abc;def", "secret 中间的 ; 不当注释");
    var pu=P("panel_url = file:///C:/x"); Check(pu.PanelUrl=="http://127.0.0.1:9090/ui/" && pu.Errors.Count==1, "panel_url 非 http 拒绝");
    // N4 switch_program
    var s1=P(@"switch_program = C:\Tools\FlClash.exe ; 我的客户端"); Check(s1.SwitchProgram==@"C:\Tools\FlClash.exe", "switch_program 行尾注释 -> ["+s1.SwitchProgram+"]");
    var s2=P(@"switch_program = ""C:\a b\x.exe"" --min"); Check(s2.SwitchProgram==@"C:\a b\x.exe" && s2.EffectiveSwitchArgs=="--min", "引号路径后跟参数 -> ["+s2.SwitchProgram+"] args=["+s2.EffectiveSwitchArgs+"]");
    var s3=P(@"switch_program = ""C:\a b\x.exe"" --min", "switch_program_args = --tray"); Check(s3.EffectiveSwitchArgs=="--min --tray", "内联参数 + switch_program_args 合并");
    Check(P(@"switch_program = C:\Program Files\FlClash\FlClash.exe").SwitchProgram==@"C:\Program Files\FlClash\FlClash.exe", "不带引号的空格路径");
    // N5 按小节插入
    var old=new List<string>{"[mihomo]","controller = 127.0.0.1:9090","secret = X","","[ui]","menu_style = party"};
    string merged=AppConfig.MergeMissingKeys(old, AppConfig.DefaultIniFor("light"));
    var ml=new List<string>(merged.Replace("\r\n","\n").Split('\n'));
    int sp=ml.FindIndex(x=>x.StartsWith("switch_program =")), ui=ml.IndexOf("[ui]"), ms=ml.FindIndex(x=>x.StartsWith("switch_program_args ="));
    int th=ml.FindIndex(x=>x.StartsWith("theme ="));
    Check(sp>0 && sp<ui && ms<ui && th>ui, "缺的键插到所属小节（switch_program 在 [ui] 之前，theme 在 [ui] 之后）");
    Check(ml.Contains("secret = X"), "原有内容保留");
    Check(AppConfig.MergeMissingKeys(ml, AppConfig.DefaultIniFor("light"))==null, "第二次不再变化（幂等）");
    var noUi=new List<string>{"[mihomo]","controller = 1.2.3.4:9090"};
    string m2=AppConfig.MergeMissingKeys(noUi, AppConfig.DefaultIniFor("light")); Check(m2.Contains("\r\n[ui]\r\n") && m2.IndexOf("theme =")>m2.IndexOf("[ui]"), "缺整个小节时新建小节");
    // N7 只认最外层 mode
    Check(MihomoClient.ParseMode("{\"tun\":{\"enable\":true,\"mode\":\"system\"},\"mode\":\"global\"}")=="global", "嵌套 mode 不干扰");
    try{ MihomoClient.ParseMode("{\"tun\":{\"mode\":\"rule\"}}"); Check(false,"只有嵌套 mode 应失败"); }catch(MihomoException){ Check(true,"只有嵌套 mode -> 解析失败"); }
    // L1 / L2
    var off=new MihomoClient("127.0.0.1:19099","");
    try{ off.SetMode("rule"); Check(false,"PATCH 不可达应失败"); }catch(MihomoException e){ Check(e.Message=="无法连接控制器","PATCH 不可达 -> "+e.Message); }catch(Exception e){ Check(false,"PATCH 不可达抛了 "+e.GetType().Name); }
    int port=int.Parse(Environment.GetEnvironmentVariable("SLOW_PORT")??"0");
    if(port>0){ var slow=new MihomoClient("127.0.0.1:"+port,""); try{ slow.GetMode(); Check(false,"超时应失败"); }catch(MihomoException e){ Check(e.Message=="控制器响应超时","超时 -> "+e.Message); } }
    // ---- 第 3 轮报告 ----
    // R3
    var w=P("controller = ws://127.0.0.1:9090"); Check(w.Controller=="http://127.0.0.1:9090" && w.Errors.Count==1, "ws:// 拒绝并报错");
    var z0=P("controller = 0.0.0.0"); Check(z0.Errors.Count==1 && z0.Controller=="http://127.0.0.1:9090", "0.0.0.0 不带端口：改成 127.0.0.1 后因缺端口报错，保留默认");
    var z6=P("controller = [::]"); Check(z6.Errors.Count==1 && z6.Controller=="http://127.0.0.1:9090", "[::] 不带端口同上");
    var np=P("controller = 127.0.0.1"); Check(np.Errors.Count==1 && np.Controller=="http://127.0.0.1:9090", "不带端口报错");
    Check(P("controller = 127.0.0.1:0").Errors.Count==1, "端口 0 报错");
    Check(P("controller = 127.0.0.1:70000").Errors.Count==1, "端口超范围报错");
    Check(P("controller = [::1]:9090").Controller=="http://[::1]:9090", "IPv6 带端口");
    Check(P("controller = http://127.0.0.1:9090/").Controller=="http://127.0.0.1:9090", "带 http:// 和末尾斜杠");
    // R4
    Check(P("secret = ab ;cd").Secret=="ab ;cd", "老配置未加引号含“空格+;”的 secret 不截断");
    Check(P("secret = \"x y\"").Secret=="x y", "整体加引号的 secret 去引号");
    Check(P("secret = \"ab\"cd").Secret=="\"ab\"cd", "引号后还有内容的 secret 原样保留");
    var q=P("panel_url = \"http://127.0.0.1:9090/ui/\" extra"); Check(q.Errors.Count==1, "引号后多出的内容报错："+string.Join("|",q.Errors.ToArray()));
    // R6
    // .NET Framework 对超出 Latin-1 的请求头会抛 ArgumentException，mono 不抛（直接按 UTF-8 发出），所以只在 .NET 上验证
    try{ new MihomoClient("127.0.0.1:19090","密钥").GetMode(); Check(false,"非 ASCII secret 应失败"); }catch(MihomoException e){ Check(e.Message.StartsWith("secret 含有")||e.Message.StartsWith("secret contains"),"非 ASCII secret -> "+e.Message); }
    // A3
    Check(P("secret = \"a\"b\"").Secret=="a\"b", "首尾都是引号：只去外层引号（与老版本一致）");
    // 面板提示：按 secret 门控；正文末行停提醒；超长只截 URL+...
    Loc.Apply("zh");
    string tipZh = Loc.PanelTipBody("http://127.0.0.1:9090/ui/");
    Check(tipZh.Contains("即将打开 http://127.0.0.1:9090/ui/") && tipZh.EndsWith("\n填入 secret 安全密钥后不再提示"), "ZH tip URL+末行停提醒");
    Check(!tipZh.EndsWith(".") && !tipZh.EndsWith("。"), "ZH tip 无句末句号");
    Loc.Apply("en");
    string tipEn = Loc.PanelTipBody("http://example/ui/");
    Check(tipEn.Contains("Opening http://example/ui/") && tipEn.EndsWith("\nSet secret to stop this tip"), "EN tip URL+末行停提醒");
    string longUrl = "http://127.0.0.1:9090/ui/" + new string('a', 40);
    string truncTip = Loc.PanelTipBody(longUrl);
    Check(truncTip.Contains("Opening http://127.0.0.1:9090/ui/aaa...") && truncTip.EndsWith("\n" + Loc.PanelTipStopLine) && truncTip.Contains("Change panel_url in config.ini"), "URL 超 28 字截前 28+...");
    Check(Loc.PanelTipBody("http://127.0.0.1:9090/ui/mmm").Contains("Opening http://127.0.0.1:9090/ui/mmm\n"), "恰好 28 字不截");
    Check(string.IsNullOrWhiteSpace(P("secret =").Secret) && string.IsNullOrWhiteSpace(P("secret =   ").Secret), "空/纯空格 secret → 提示");
    Check(!string.IsNullOrWhiteSpace(P("secret = abc").Secret), "非空 secret → 不提示");
    Loc.Apply("zh");
    // A1
    string asc=AppConfig.AsciiOnly(AppConfig.MissingKeysBlock(new[]{"[mihomo]","controller = 1.2.3.4:9090"}, AppConfig.DefaultIniFor("light")));
    bool allAscii=true; foreach(char ch in asc) if(ch>127) allAscii=false;
    Check(allAscii && asc.Contains("switch_program =") && asc.Contains("theme ="), "非 UTF-8 文件追加的内容全是 ASCII");
    // R1：UTF-8 LF 文件补键后仍是 LF、BOM 不变；非 UTF-8 文件只在末尾追加，原字节不动
    string dir=System.IO.Path.Combine(System.IO.Path.GetTempPath(),"fixtest"+Environment.TickCount); System.IO.Directory.CreateDirectory(dir);
    string f1=System.IO.Path.Combine(dir,"a.ini");
    System.IO.File.WriteAllBytes(f1, System.Text.Encoding.UTF8.GetBytes("[mihomo]\ncontroller = 127.0.0.1:9090\nsecret = 中文密钥\n\n[ui]\ntheme = system\n"));
    var c1=new AppConfig(); AppConfig.LoadAndUpgrade(c1,f1); byte[] b1=System.IO.File.ReadAllBytes(f1); string t1=System.Text.Encoding.UTF8.GetString(b1);
    Check(c1.Secret=="中文密钥" && t1.Contains("switch_program =") && !t1.Contains("\r\n") && !(b1[0]==0xEF), "UTF-8 + LF：补键后仍是 LF、无 BOM、secret 不变");
    Check(!System.IO.File.Exists(f1+".tmp"), "临时文件已清理");
    string f2=System.IO.Path.Combine(dir,"b.ini");
    byte[] gbk={ (byte)'[',(byte)'m',(byte)'i',(byte)'h',(byte)'o',(byte)'m',(byte)'o',(byte)']',(byte)'\r',(byte)'\n',
      (byte)'s',(byte)'e',(byte)'c',(byte)'r',(byte)'e',(byte)'t',(byte)' ',(byte)'=',(byte)' ',0xC3,0xDC,0xD4,0xBF,(byte)'\r',(byte)'\n' };  // “密钥”的 GBK 字节
    System.IO.File.WriteAllBytes(f2,gbk);
    AppConfig.LoadAndUpgrade(new AppConfig(),f2); byte[] b2=System.IO.File.ReadAllBytes(f2);
    bool prefix=b2.Length>gbk.Length; for(int i=0;i<gbk.Length&&prefix;i++) if(b2[i]!=gbk[i]) prefix=false;
    Check(prefix, "非 UTF-8 文件：原有字节一个不改，只在末尾追加");
    var again=System.IO.File.ReadAllBytes(f2); AppConfig.LoadAndUpgrade(new AppConfig(),f2); Check(System.IO.File.ReadAllBytes(f2).Length==again.Length, "非 UTF-8 文件：第二次不再追加");
    string f3=System.IO.Path.Combine(dir,"ro.ini"); System.IO.File.WriteAllText(f3,"[mihomo]\r\ncontroller = 127.0.0.1:9090\r\n");
    System.IO.File.SetAttributes(f3, System.IO.FileAttributes.ReadOnly); byte[] b3=System.IO.File.ReadAllBytes(f3);
    AppConfig.LoadAndUpgrade(new AppConfig(),f3);
    Check(System.IO.File.ReadAllBytes(f3).Length==b3.Length && (System.IO.File.GetAttributes(f3)&System.IO.FileAttributes.ReadOnly)!=0 && !System.IO.File.Exists(f3+".tmp"), "只读 config.ini 不改动、仍是只读、没有残留 .tmp");
    Console.WriteLine(fails==0?"ALL PASS":fails+" FAIL"); return fails;
  }
}
