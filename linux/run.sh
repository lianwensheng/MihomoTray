#!/bin/sh
# 从源码运行。Qt：pip install PySide6-Essentials 后默认或 MIHOMOTRAY_FRONTEND=qt
# GTK：安装 python3-gi / AppIndicator 后 MIHOMOTRAY_FRONTEND=gtk
cd "$(dirname "$0")" && exec python3 -m mihomotray "$@"
