// exe 属性“详细信息”页显示的版本信息（csc/mcs 会据此生成 Win32 版本资源）
// 发版只动产品版本（InformationalVersion = x.y.z）；本地测试只顺延文件版本第 4 段 N（从 0 起）
// GitHub Actions / Release 标签读的是产品版本，不跟 FileVersion
using System.Reflection;

[assembly: AssemblyTitle("MihomoTray")]                 // 文件说明
[assembly: AssemblyProduct("MihomoTray")]               // 产品名称
[assembly: AssemblyCopyright("Copyright © 2026 WSW")]   // 版权
[assembly: AssemblyVersion("2.1.8.9")]
[assembly: AssemblyFileVersion("2.1.8.9")]              // 文件版本 x.y.z.N（本地小改只加 N）
[assembly: AssemblyInformationalVersion("2.1.8")]       // 产品版本 x.y.z（发版才动；UA 用这个）
