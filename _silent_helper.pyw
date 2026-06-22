# -*- coding: utf-8 -*-
"""无窗口启动器 - 双击即运行。用 tk 消息框显示结果，不弹黑色命令窗口。"""

import sys
import os
import subprocess
import time

HERE = os.path.dirname(os.path.abspath(__file__))
LAUNCHER = os.path.join(HERE, "launcher.py")
CMD = sys.argv[1] if len(sys.argv) > 1 else "start"

# 用 pythonw.exe 或 python.exe 运行 launcher.py（传入命令）
# 关键: 让 launcher.py 自己也能无窗口运行，所以不捕获输出
# 但是 launcher.py 的 print 输出到 stdout，pythonw 下没有 stdout → 需要捕获并显示

proc = subprocess.Popen(
    [sys.executable, LAUNCHER, CMD],
    cwd=HERE,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    encoding="utf-8",
    errors="replace",
)

try:
    out, _ = proc.communicate(timeout=45)
except subprocess.TimeoutExpired:
    proc.kill()
    out = "操作超时。请手动查看 .runtime/ 目录下的日志。"

result_lines = out.strip().splitlines() if out else []

# 截断到消息框可显示的长度
title_map = {
    "start": "启动 可米幻工坊",
    "stop": "停止 可米幻工坊",
    "restart": "重启 可米幻工坊",
    "status": "可米幻工坊 运行状态",
}
title = title_map.get(CMD, "可米幻工坊")

# 判断成功与否
all_ok = any("全部服务启动成功" in l or "停止完成" in l or "已运行" in l for l in result_lines)
success_icon = "info" if all_ok or proc.returncode == 0 else "warning"

# 用 tk 消息框显示结果
try:
    import tkinter as tk
    from tkinter import messagebox

    root = tk.Tk()
    root.withdraw()
    msg = "\n".join(result_lines[-25:]) if result_lines else "无输出"
    if success_icon == "info":
        messagebox.showinfo(title, msg)
    else:
        messagebox.showwarning(title, msg)
    root.destroy()
except Exception:
    # tk 不可用时，退回到临时文件通知
    tmp = os.path.join(HERE, f"_result_{int(time.time())}.txt")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(title + "\n\n" + "\n".join(result_lines))
    os.startfile(tmp)  # Windows 专用

sys.exit(proc.returncode)
