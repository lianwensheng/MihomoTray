using System; using MihomoTray;
class T {
  static int fails=0;
  static void Check(bool c,string m){ Console.WriteLine((c?"PASS ":"FAIL ")+m); if(!c) fails++; }
  static int Main(){
    var cfg=new AppConfig(); cfg.Parse(AppConfig.DefaultIni.Replace("controller = 127.0.0.1:9090","controller = 127.0.0.1:19090").Replace("language = system","language = zh").Split('\n'));
    Loc.Apply("zh");
    Check(cfg.Controller=="http://127.0.0.1:19090","ini controller normalize: "+cfg.Controller);
    Check(cfg.Secret=="" && cfg.PollSeconds==3 && cfg.CloseConnections && cfg.PanelUrl=="http://127.0.0.1:9090/ui/","ini defaults");
    var c=new MihomoClient("127.0.0.1:19090","");
    Check(c.GetMode()=="rule","GET mode = rule");
    foreach(var m in new[]{"global","direct","rule"}){ c.SetMode(m); Check(c.GetMode()==m,"PATCH -> "+m); }
    c.CloseAllConnections(); Check(true,"DELETE /connections");
    Check(MihomoClient.ParseMode("{\"mode\": \"Global\"}")=="global","parse capitalized mode");
    // secret
    var bad=new MihomoClient("http://127.0.0.1:19091","wrong");
    try{ bad.GetMode(); Check(false,"bad secret should fail"); }catch(MihomoException e){ Check(e.Message.Contains("鉴权"),"bad secret -> "+e.Message); }
    var good=new MihomoClient("127.0.0.1:19091","s3cret"); good.SetMode("global"); Check(good.GetMode()=="global","secret auth ok");
    // unreachable
    var off=new MihomoClient("127.0.0.1:19099",""); var t0=DateTime.Now;
    try{ off.GetMode(); Check(false,"unreachable should fail"); }catch(MihomoException e){ Check(true,"unreachable -> "+e.Message+" ("+(int)(DateTime.Now-t0).TotalMilliseconds+"ms)"); }
    // GET /configs -> 模式 + tun.enable；PATCH tun 后变化
    var st=c.GetStatus();
    Check(st.Mode=="rule" && !st.TunEnabled && st.LogLevel=="info","status: rule, tun off, log info");
    Check(TrayTip.For(true,st.Mode,st.TunEnabled,st.LogLevel)=="模式 : 规则模式\n日志级别 : 信息\n虚拟网卡 : 关闭","tip connected tun off");
    var req=(System.Net.HttpWebRequest)System.Net.WebRequest.Create("http://127.0.0.1:19090/configs"); req.Method="PATCH"; req.Proxy=null; req.ContentType="application/json";
    var data=System.Text.Encoding.UTF8.GetBytes("{\"tun\":{\"enable\":true}}"); using(var rs=req.GetRequestStream()) rs.Write(data,0,data.Length); req.GetResponse().Close();
    var st2=c.GetStatus(); Check(st2.TunEnabled && st2.Mode=="rule","after PATCH tun on");
    Check(TrayTip.For(true,st2.Mode,st2.TunEnabled,st2.LogLevel)=="模式 : 规则模式\n日志级别 : 信息\n虚拟网卡 : 开启","tip connected tun on");
    // 把 mock 的 TUN 改回关闭，同一个 mock 可以反复跑
    { var rq=(System.Net.HttpWebRequest)System.Net.WebRequest.Create(req.RequestUri); rq.Method="PATCH"; rq.Proxy=null; rq.ContentType="application/json";
      foreach(string h in req.Headers.AllKeys) if(h=="Authorization") rq.Headers[h]=req.Headers[h];
      var d2=System.Text.Encoding.UTF8.GetBytes("{\"tun\":{\"enable\":false}}"); using(var rs=rq.GetRequestStream()) rs.Write(d2,0,d2.Length); rq.GetResponse().Close(); }
    Check(!c.GetStatus().TunEnabled,"reset tun off");
    try{ off.GetStatus(); Check(false,"unreachable status should fail"); }catch(MihomoException){ Check(TrayTip.For(false,null,false,null).Contains("未连接") && TrayTip.For(false,null,false,null).StartsWith("模式 :"),"unreachable status -> offline tip"); }
    return fails;
  }
}
