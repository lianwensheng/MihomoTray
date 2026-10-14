"""单实例：fcntl 锁文件。进程退出时内核自动释放，崩溃也不会残留。"""
import fcntl
import os


def acquire_lock():
    d = os.environ.get("XDG_RUNTIME_DIR")
    if not d or not os.path.isdir(d):
        from .config import data_dir
        d = data_dir()
        os.makedirs(d, exist_ok=True)
    f = open(os.path.join(d, "MihomoTray.lock"), "a+")
    try:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        f.close()
        return None
    return f
