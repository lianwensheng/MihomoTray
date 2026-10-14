// 开机自启：config.ini 解析和注册表同步的决策逻辑（注册表本身只能在 Windows 上测）
using System; using MihomoTray;
class AutostartTest {
  static int fails=0;
  static void Check(bool c,string m){ Console.WriteLine((c?"PASS ":"FAIL ")+m); if(!c) fails++; }
  static int Main(){
    Check(!new AppConfig().Autostart,"default autostart = false");
    var ini=AppConfig.DefaultIniFor(AppConfig.DefaultTheme);
    Check(ini.Contains("autostart = false\r\n"),"template has autostart = false");
    foreach(var v in new[]{"true","TRUE","1","yes","on"}){ var c=new AppConfig(); c.Parse(new[]{"autostart = "+v}); Check(c.Autostart,"autostart = "+v+" -> on"); }
    foreach(var v in new[]{"false","0","no","off","","maybe"}){ var c=new AppConfig(); c.Parse(new[]{"autostart = "+v}); Check(!c.Autostart,"autostart = "+v+" -> off"); }
    var c2=new AppConfig(); c2.Parse(new[]{"autostart = true ; 我要自启"}); Check(c2.Autostart,"inline comment stripped");
    string exe=@"C:\Program Files\MihomoTray\MihomoTray.exe", q="\""+exe+"\"";
    Check(Autostart.CommandFor(exe)==q,"command is quoted exe path");
    Check(Autostart.Decide(true,null,exe)==Autostart.Action.Write,"on + missing -> write");
    Check(Autostart.Decide(true,q,exe)==Autostart.Action.None,"on + same -> none");
    Check(Autostart.Decide(true,q.ToLowerInvariant(),exe)==Autostart.Action.None,"on + same (case) -> none");
    Check(Autostart.Decide(true,"\"D:\\old\\MihomoTray.exe\"",exe)==Autostart.Action.Write,"on + moved exe -> rewrite");
    Check(Autostart.Decide(false,null,exe)==Autostart.Action.None,"off + missing -> none");
    Check(Autostart.Decide(false,q,exe)==Autostart.Action.Delete,"off + present -> delete own value");
    // 旧配置升级：缺 autostart 时补到 [ui] 末尾
    var old=AppConfig.DefaultIniFor("light").Replace("; 开机自启：true（开启）/ false（关闭，默认）；每次启动时按这里同步系统设置\r\n; Start with Windows: true / false (default); synced to the system on every start\r\nautostart = false\r\n","");
    var merged=AppConfig.MergeMissingKeys(old.Replace("\r\n","\n").Split('\n'),ini);
    Check(merged!=null && merged.Contains("theme = light\r\n; 开机自启") && merged.TrimEnd().EndsWith("autostart = false"),"old config gets autostart appended in [ui]");
    Console.WriteLine(fails==0?"ALL PASS":fails+" FAIL"); return fails;
  }
}
