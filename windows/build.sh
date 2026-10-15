#!/bin/sh
# 在 Linux 上用 mono 的 mcs 编译 Windows exe（.NET Framework 4.x，Win10/11 自带）
# 用法：./build.sh   -> dist/MihomoTray.exe（右键菜单为 Windows 原生菜单）
# 已有的 config.ini（dist 里的和源码根目录的模板）都不会被覆盖，免得冲掉填好的 secret；
# 想按 AppConfig.cs 重新生成模板时设 REGEN_CONFIG=1
set -e
cd "$(dirname "$0")"
if [ $# -gt 0 ]; then echo "build.sh 不需要参数（收到：$*）" >&2; exit 1; fi
FORCE=""
[ "${REGEN_CONFIG:-0}" = 1 ] && FORCE="--force"
python3 tools/make_icons.py

# 生成 config.ini：make_config.py 返回 2 表示文件已存在且内容不同、按约定没有覆盖，其它非 0 是真正的错误
cfg() {
  rc=0
  python3 tools/make_config.py "$@" || rc=$?
  [ $rc -eq 0 ] || [ $rc -eq 2 ] || { echo "生成 $1 失败（退出码 $rc）" >&2; exit $rc; }
}

mkdir -p dist
mcs -nologo -langversion:5 -target:winexe -platform:anycpu -optimize+ -warnaserror- -sdk:4.5 \
  -codepage:utf8 \
  -out:dist/MihomoTray.exe \
  -win32icon:icons/tray_rule.ico \
  -r:System.dll -r:System.Drawing.dll -r:System.Windows.Forms.dll \
  -resource:icons/tray_rule.ico,tray_rule.ico \
  -resource:icons/tray_global.ico,tray_global.ico \
  -resource:icons/tray_direct.ico,tray_direct.ico \
  -resource:icons/tray_offline.ico,tray_offline.ico \
  src/*.cs
# config.ini、MihomoTray.exe.config、Icons 都放在 dist/Data；旧版放在 exe 旁边的 config.ini 挪进去
mkdir -p dist/Data/Icons
[ -f dist/config.ini ] && [ ! -f dist/Data/config.ini ] && mv dist/config.ini dist/Data/config.ini
rm -f dist/config.ini dist/MihomoTray.exe.config
cp src/MihomoTray.exe.config dist/Data/
for m in rule global direct offline; do cp icons/tray_$m.ico dist/Data/Icons/; done
cp README.txt README_en.txt dist/
cfg dist/Data/config.ini light
cfg config.ini light $FORCE
echo "built dist/MihomoTray.exe"

# 本地打包：产品版本 x.y.z；FileVersion 第 4 段 N>0 时 zip 名带 .N（CI 不跑本脚本）
PRODUCT=$(sed -n 's/.*AssemblyInformationalVersion("\([^"]*\)").*/\1/p' src/AssemblyInfo.cs | head -1)
FILEVER=$(sed -n 's/.*AssemblyFileVersion("\([^"]*\)").*/\1/p' src/AssemblyInfo.cs | head -1)
N=$(printf '%s' "$FILEVER" | awk -F. '{print ($4 == "" ? 0 : $4)}')
if [ "$N" -gt 0 ]; then
  ARTIFACT_VER="$FILEVER"
else
  ARTIFACT_VER="$PRODUCT"
fi
ZIP="MihomoTray_windows_${ARTIFACT_VER}.zip"
rm -f "$ZIP"
python3 - "$ZIP" <<'PY'
import sys, zipfile
from pathlib import Path
zip_path = Path(sys.argv[1])
root = Path("dist")
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    for f in sorted(root.rglob("*")):
        if f.is_file():
            z.write(f, f.relative_to(root).as_posix())
print("packed", zip_path)
PY
echo "packed $ZIP (product $PRODUCT file $FILEVER)"
