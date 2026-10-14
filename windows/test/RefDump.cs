using System; using System.IO; using System.Reflection;
class R { static void Main(string[] a){
  var asm=Assembly.LoadFile(Path.GetFullPath(a[0])); Console.WriteLine(asm.ImageRuntimeVersion);
  foreach(var r in asm.GetReferencedAssemblies()) Console.WriteLine(r.FullName);
  foreach(var n in asm.GetManifestResourceNames()) Console.WriteLine("res: "+n); } }
