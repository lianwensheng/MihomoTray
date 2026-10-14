// TUN 解析（只看最外层 tun 对象的 enable）与悬停提示映射的单元测试
using System; using MihomoTray;
class TunTest {
  static int fails=0;
  static void Check(bool c,string m){ Console.WriteLine((c?"PASS ":"FAIL ")+m); if(!c) fails++; }
  static int Main(){
    Loc.Apply("zh");
    // 提示映射
    string tipOn=TrayTip.For(true,"rule",true,"info");
    Check(tipOn=="模式 : 规则模式\n日志级别 : 信息\n虚拟网卡 : 开启","connected + tun on tip");
    Check(TrayTip.For(true,"global",false,"debug")=="模式 : 全局模式\n日志级别 : 调试\n虚拟网卡 : 关闭","connected + tun off tip");
    string off=TrayTip.For(false,null,true,null);
    Check(off.StartsWith("模式 : 未连接") && off.Contains("日志级别 : —"),"unreachable -> offline tip");
    Check(TrayTip.LogLabel("silent")=="静默" && TrayTip.LogLabel("warn")=="警告","log labels");
    Loc.Apply("en"); Check(TrayTip.LogLabel("warning")=="Warn" && TrayTip.LogLabel("warn")=="Warn","en warn label"); Loc.Apply("zh");
    Check(TrayTip.LogLabel("")=="—" && TrayTip.LogLabel("trace")=="—" && TrayTip.LogLabel(null)=="—","unknown log -> —");
    Loc.Apply("en");
    Check(TrayTip.For(true,"rule",true,"info")=="Mode : Rule\nLog Level : Info\nTUN Mode : On","en tip");
    Check(TrayTip.For(false,null,false,null).StartsWith("Mode : Disconnected"),"en offline tip");
    Loc.Apply("zh");
    Check(tipOn.Length<=63 && off.Length<=63,"tooltip length <=63");
    // tun.enable 解析
    string real="{\"port\":0,\"socks-port\":7891,\"mixed-port\":7890,\"tun\":{\"enable\":true,\"device\":\"Meta\",\"stack\":\"Mixed\",\"dns-hijack\":[\"any:53\"],\"auto-route\":true,\"route-address\":[],\"file-descriptor\":0},\"tuic-server\":{\"enable\":false,\"listen\":\"\"},\"mode\":\"rule\"}";
    Check(MihomoClient.ParseTunEnabled(real),"realistic GetGeneral: tun on");
    Check(!MihomoClient.ParseTunEnabled(real.Replace("\"enable\":true,\"device\"","\"enable\":false,\"device\"")),"realistic: tun off");
    Check(!MihomoClient.ParseTunEnabled("{\"tuic-server\":{\"enable\":true},\"mode\":\"rule\",\"tun\":{\"enable\":false}}"),"tuic-server.enable=true not counted");
    Check(!MihomoClient.ParseTunEnabled("{\"tuic-server\":{\"enable\":true},\"mode\":\"rule\"}"),"no tun object (old core) -> off");
    Check(MihomoClient.ParseTunEnabled("{\"tun\":{\"device\":\"x\",\"inner\":{\"enable\":false},\"enable\" : true }}"),"enable not first, nested enable ignored");
    Check(!MihomoClient.ParseTunEnabled("{\"tun\":{\"device\":\"x\",\"inner\":{\"enable\":true},\"enable\":false}}"),"nested inner enable=true ignored");
    Check(MihomoClient.ParseTunEnabled("{\"note\":\"a \\\"}{\\\" \\\"tun\\\":{\\\"enable\\\":false} b\",\"tun\":{\"enable\":true}}"),"braces/quotes inside strings");
    Check(!MihomoClient.ParseTunEnabled("{\"tun\":null}") && !MihomoClient.ParseTunEnabled("{\"tun\":true}"),"tun not an object -> off");
    Check(!MihomoClient.ParseTunEnabled("") && !MihomoClient.ParseTunEnabled(null) && !MihomoClient.ParseTunEnabled("<html>"),"empty/garbage -> off");
    Check(MihomoClient.ParseTunEnabled("  {\n \"tun\" : {\n  \"enable\" : true\n }\n}"),"whitespace/newlines");
    var st=MihomoClient.ParseStatus(real); Check(st.Mode=="rule" && st.TunEnabled,"ParseStatus mode + tun");
    try { MihomoClient.ParseStatus("<html>"); Check(false,"garbage should throw"); } catch(MihomoException){ Check(true,"ParseStatus garbage -> MihomoException (未连接)"); }
    return fails;
  }
}
