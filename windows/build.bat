@echo off
rem 在 Windows 上编译：用系统自带的 .NET Framework 4.x csc，不用装 Visual Studio
rem 用法：双击 build.bat  -> dist\MihomoTray.exe（右键菜单为 Windows 原生菜单）
chcp 65001 >nul
setlocal
rem MihomoTray 2.1.8；CI 环境（GitHub Actions 会设 CI=true）里不 pause，本地双击照旧
set "PAUSE=pause"
if defined CI set "PAUSE=type nul>nul"
cd /d "%~dp0"
set CSC=%WINDIR%\Microsoft.NET\Framework64\v4.0.30319\csc.exe
if not exist "%CSC%" set CSC=%WINDIR%\Microsoft.NET\Framework\v4.0.30319\csc.exe
if not exist "%CSC%" (echo 找不到 csc.exe，请确认已启用 .NET Framework 4.x & %PAUSE% & exit /b 1)

if not exist dist mkdir dist
"%CSC%" /nologo /target:winexe /platform:anycpu /optimize+ /codepage:65001 ^
  /out:dist\MihomoTray.exe ^
  /win32icon:icons\tray_rule.ico ^
  /r:System.dll /r:System.Drawing.dll /r:System.Windows.Forms.dll ^
  /resource:icons\tray_rule.ico,tray_rule.ico ^
  /resource:icons\tray_global.ico,tray_global.ico ^
  /resource:icons\tray_direct.ico,tray_direct.ico ^
  /resource:icons\tray_offline.ico,tray_offline.ico ^
  src\*.cs
if errorlevel 1 (echo 编译失败 & %PAUSE% & exit /b 1)
if not exist dist\Data\Icons mkdir dist\Data\Icons
if exist dist\config.ini if not exist dist\Data\config.ini move /y dist\config.ini dist\Data\config.ini >nul
if exist dist\MihomoTray.exe.config del /q dist\MihomoTray.exe.config
copy /y src\MihomoTray.exe.config dist\Data\ >nul
for %%m in (rule global direct offline) do copy /y icons\tray_%%m.ico dist\Data\Icons\ >nul
copy /y README.txt dist\ >nul
copy /y README_en.txt dist\ >nul
rem 已有的 config.ini 不覆盖，免得冲掉你填好的 secret
if not exist dist\Data\config.ini copy /y config.ini dist\Data\config.ini >nul
echo 编译完成：dist\MihomoTray.exe
rem 本地打包 zip（CI 由 workflow 按产品版本打包，这里跳过）
if defined CI goto :done_pack
for /f "tokens=2 delims=()" %%a in ('findstr /C:"AssemblyInformationalVersion" src\AssemblyInfo.cs') do set "PRODUCT=%%~a"
for /f "tokens=2 delims=()" %%a in ('findstr /C:"AssemblyFileVersion" src\AssemblyInfo.cs') do set "FILEVER=%%~a"
for /f "tokens=1-4 delims=." %%a in ("%FILEVER%") do set "N=%%d"
if not defined N set "N=0"
if "%N%"=="" set "N=0"
set "ARTIFACT_VER=%PRODUCT%"
if not "%N%"=="0" set "ARTIFACT_VER=%FILEVER%"
set "ZIP=MihomoTray_windows_%ARTIFACT_VER%.zip"
if exist "%ZIP%" del /q "%ZIP%"
powershell -NoProfile -Command "Compress-Archive -Path dist\* -DestinationPath '%ZIP%' -Force"
if errorlevel 1 (echo 打包 zip 失败 & %PAUSE% & exit /b 1)
echo 已打包：%ZIP%（产品 %PRODUCT% 文件 %FILEVER%）
:done_pack
%PAUSE%
