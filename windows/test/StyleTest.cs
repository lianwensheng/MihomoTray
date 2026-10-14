// 检查 theme 的默认值和解析、switch_program 解析、旧配置补键
using System; using System.IO; using System.Text; using MihomoTray;
class StyleTest {
  static int fails=0;
  static void Check(bool c,string m){ Console.WriteLine((c?"PASS ":"FAIL ")+m); if(!c) fails++; }
  static int Main(string[] a){
    var c=new AppConfig();
    Console.WriteLine("default theme="+c.Theme);
    Check(c.Theme=="light","default theme is light (same as FlClash)");
    Check(c.Language=="system","default language is system");
    var ini=AppConfig.DefaultIniFor(AppConfig.DefaultTheme);
    Check(ini.Contains("language = system") && ini.Contains("UI language:"),"template has bilingual language comments");
    var cl=new AppConfig(); cl.Parse(new[]{"language = en"}); Check(cl.Language=="en" && Loc.En,"parse language en");
    var cz=new AppConfig(); cz.Parse(new[]{"language = zh"}); Check(cz.Language=="zh" && !Loc.En,"parse language zh");
    var c2=new AppConfig(); c2.Parse(ini.Split('\n'));
    Check(c2.Theme==AppConfig.DefaultTheme && !ini.Contains("menu_style"),"built-in ini round trip, no menu_style");
    if (a.Length>0) Check(File.ReadAllText(a[0],Encoding.UTF8).TrimStart('\uFEFF')==ini,"shipped "+a[0]+" == built-in default");
    var c3=new AppConfig(); c3.Parse(new[]{"theme = dark"}); Check(c3.Theme=="dark","parse dark");
    var c4=new AppConfig(); c4.Parse(new[]{"menu_style = party","theme = system"}); Check(c4.Theme=="system" && c4.Errors.Count==0,"old menu_style key is ignored silently");
    var c5=new AppConfig(); c5.Parse(new[]{"theme = x"}); Check(c5.Theme==AppConfig.DefaultTheme,"bad theme keeps default");
    // switch_program
    var c6=new AppConfig(); Check(!c6.HasSwitchProgram,"switch_program default empty");
    c6.Parse(new[]{"switch_program = \"/opt/My Apps/Clash Verge.exe\"","switch_program_args = --minimized \"a b\""});
    Check(c6.SwitchProgram=="/opt/My Apps/Clash Verge.exe","quoted path with spaces: "+c6.SwitchProgram);
    Check(c6.SwitchProgramArgs=="--minimized \"a b\"","args keep quotes: "+c6.SwitchProgramArgs);
    var c7=new AppConfig(); c7.Parse(new[]{"switch_program = /opt/My Apps/x.lnk"}); Check(c7.SwitchProgram=="/opt/My Apps/x.lnk","unquoted path with spaces");
    var c8=new AppConfig(); c8.Parse(AppConfig.DefaultIniFor("light").Split('\n')); Check(!c8.HasSwitchProgram && c8.SwitchProgramArgs=="","template leaves switch_program empty");
    Environment.SetEnvironmentVariable("MTEST_DIR","/opt/clients");
    Check(AppConfig.ResolveProgramPath("%MTEST_DIR%/FlClash/FlClash.exe","/base")=="/opt/clients/FlClash/FlClash.exe","env var expand");
    Check(AppConfig.ResolveProgramPath("..\\x\\y.exe".Replace('\\','/'),"/base/tool")=="/base/x/y.exe","relative to exe dir");
    Check(AppConfig.ResolveProgramPath("  ","/base")==null,"blank -> null");
    // 旧 config.ini 自动补键
    if (a.Length>1) {
      var old=File.ReadAllLines(a[1],Encoding.UTF8);
      var add=AppConfig.MissingKeysBlock(old, ini);
      Console.WriteLine("---- append to old config ----\n"+add+"----");
      Check(add.Contains("switch_program = ") && add.Contains("switch_program_args = ") && !add.Contains("controller ="),"old config gets only missing keys");
      var merged=new System.Collections.Generic.List<string>(old); merged.AddRange(add.Replace("\r\n","\n").Split('\n'));
      Check(AppConfig.MissingKeysBlock(merged, ini)=="","idempotent after append");
      var c9=new AppConfig(); c9.Parse(merged); Check(c9.Controller=="http://127.0.0.1:9090" && !c9.HasSwitchProgram,"merged config parses");
    }
    Check(AppConfig.MissingKeysBlock(ini.Split('\n'), ini)=="","fresh config: nothing missing");
    return fails;
  }
}
