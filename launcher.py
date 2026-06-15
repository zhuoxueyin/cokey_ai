# -*- coding: utf-8 -*-
"""
AIGC Platform - Service Launcher
=================================
无窗口、高可靠的服务启动/停止/重启工具。

用法:
    python launcher.py start      启动后端(8000) + 前端(3001)
    python launcher.py stop       停止所有服务
    python launcher.py restart    停止 -> 启动
    python launcher.py status     查看运行状态
    python launcher.py log <name> 查看日志(name=backend|frontend|all)

所有子进程使用 CREATE_NO_WINDOW 启动，不弹出黑色命令窗口。
进程 ID 和日志保存在 .runtime/ 目录下。
"""

import sys
import os
import time
import json
import signal
import subprocess
from pathlib import Path


# ============ 配置 ============

ROOT = Path(__file__).resolve().parent
RUNTIME_DIR = ROOT / ".runtime"
RUNTIME_DIR.mkdir(exist_ok=True)

BACKEND_DIR = ROOT / "backend"
FRONTEND_DIR = ROOT / "frontend"

PYTHON_EXE = sys.executable  # 当前解释器

SERVICES = {
    "backend": {
        "port": 8000,
        "health_url": "http://127.0.0.1:8000/api/health",
        "pid_file": RUNTIME_DIR / "backend.pid",
        "log_file": RUNTIME_DIR / "backend.log",
        "start_timeout": 15,
    },
    "frontend": {
        "port": 3001,
        "health_url": "http://127.0.0.1:3001/",
        "pid_file": RUNTIME_DIR / "frontend.pid",
        "log_file": RUNTIME_DIR / "frontend.log",
        "start_timeout": 45,
    },
}


# ============ 工具函数 ============

def _log(msg):
    """打印带时间戳的状态信息（兼容 GBK 控制台，遇到不可编码字符用 ? 替代）。"""
    ts = time.strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    try:
        print(line)
    except UnicodeEncodeError:
        sys.stdout.write(line.encode("gbk", errors="replace").decode("gbk", errors="replace") + "\n")
    sys.stdout.flush()


def _write_pid(name, pid):
    """写入 PID 文件。"""
    info = {"pid": pid, "started_at": time.time(), "name": name}
    SERVICES[name]["pid_file"].write_text(json.dumps(info, ensure_ascii=False, indent=2))


def _read_pid(name):
    """读取 PID 文件，不存在或无效返回 None。"""
    f = SERVICES[name]["pid_file"]
    if not f.exists():
        return None
    try:
        info = json.loads(f.read_text())
        return int(info.get("pid", 0)) or None
    except (json.JSONDecodeError, ValueError, OSError):
        return None


def _clear_pid(name):
    f = SERVICES[name]["pid_file"]
    if f.exists():
        try:
            f.unlink()
        except OSError:
            pass


def _process_alive(pid):
    """检查进程是否还活着（Windows 兼容方式）。"""
    if not pid:
        return False
    try:
        tasklist = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
            capture_output=True, text=True, timeout=5
        )
        return str(pid) in tasklist.stdout
    except (subprocess.SubprocessError, FileNotFoundError):
        try:
            os.kill(pid, 0)  # signal 0 = 不杀，仅探测
            return True
        except OSError:
            return False


def _port_in_use(port):
    """检查端口是否被占用。"""
    try:
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            return s.connect_ex(("127.0.0.1", port)) == 0
    except OSError:
        return False


def _http_ok(url, timeout=3):
    """简单 HTTP 探测，返回 True 表示服务响应正常。"""
    try:
        import urllib.request
        req = urllib.request.Request(url, headers={"User-Agent": "aigc-launcher"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return 200 <= resp.status < 500
    except Exception:
        return False


def _kill_process_tree(pid):
    """终止进程及其子进程（用 taskkill /T /F 最稳）。"""
    if not _process_alive(pid):
        return False
    try:
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(pid)],
            capture_output=True, timeout=5
        )
        # 二次确认
        for _ in range(5):
            if not _process_alive(pid):
                return True
            time.sleep(0.2)
        return not _process_alive(pid)
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        try:
            os.kill(pid, signal.SIGTERM)
            time.sleep(1)
            os.kill(pid, signal.SIGKILL)
            return True
        except OSError:
            return False


def _detach_subprocess(args, cwd, log_file, extra_env=None, shell=False):
    """
    以完全独立的方式启动子进程（无窗口、脱离调用者进程树）。

    Windows 下关键点:
      - DETACHED_PROCESS | CREATE_NO_WINDOW = 不创建控制台窗口
      - 不继承父进程的控制台
      - stdout/stderr 重定向到日志文件
      - shell=True 时由 cmd.exe 解析命令字符串（用于调用 .cmd/.bat）
    """
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)

    creationflags = 0
    if os.name == "nt":
        DETACHED_PROCESS = 0x00000008
        CREATE_NO_WINDOW = 0x08000000
        creationflags = DETACHED_PROCESS | CREATE_NO_WINDOW

    log_fh = open(log_file, "a", encoding="utf-8", buffering=1)

    try:
        proc = subprocess.Popen(
            args,
            cwd=str(cwd),
            stdout=log_fh,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            env=env,
            creationflags=creationflags,
            close_fds=True,
            shell=shell,
        )
        return proc, log_fh
    except Exception:
        log_fh.close()
        raise


# ============ 服务启动 ============

def start_service(name):
    """启动单个服务，返回 (success, message)。"""
    cfg = SERVICES[name]
    port = cfg["port"]
    pid = _read_pid(name)
    health_url = cfg["health_url"]

    # 1. 检查是否已运行
    if pid and _process_alive(pid) and _http_ok(health_url, timeout=2):
        return True, f"{name:8s} 已运行 (PID={pid}, 端口={port})"

    # 2. 清理旧 PID（僵尸记录）
    if pid and not _process_alive(pid):
        _log(f"{name:8s} 旧 PID={pid} 已失效，清理")
        _clear_pid(name)

    # 3. 检查端口冲突
    if _port_in_use(port):
        return False, f"{name:8s} 端口 {port} 被其他进程占用，请先 stop"

    # 4. 打开日志头
    log_file = cfg["log_file"]
    with open(log_file, "a", encoding="utf-8") as lf:
        lf.write(f"\n===== 启动 {name} | {time.strftime('%Y-%m-%d %H:%M:%S')} =====\n")

    # 5. 按服务类型构造命令
    use_shell = False
    if name == "backend":
        args = [PYTHON_EXE, "-u", str(BACKEND_DIR / "run_server.py")]
        cwd = BACKEND_DIR
        extra_env = {"PYTHONPATH": str(BACKEND_DIR)}
    elif name == "frontend":
        import shutil
        node_exe = shutil.which("node.exe") or shutil.which("node")
        if not node_exe:
            return False, f"{name:8s} 未找到 node.exe，请确保 Node.js 已安装并在 PATH 中"
        # 计算 npm-cli.js 路径（npm.cmd 同级的 node_modules/npm/bin/npm-cli.js）
        node_dir = os.path.dirname(node_exe)
        npm_cli_js = os.path.join(node_dir, "node_modules", "npm", "bin", "npm-cli.js")
        if not os.path.isfile(npm_cli_js):
            # 兜底：找 %APPDATA%/npm/node_modules/npm/bin/npm-cli.js
            appdata_npm = os.path.join(os.environ.get("APPDATA", ""), "npm", "node_modules", "npm", "bin", "npm-cli.js")
            if os.path.isfile(appdata_npm):
                npm_cli_js = appdata_npm
            else:
                return False, f"{name:8s} 未找到 npm-cli.js（在 {node_dir} 中）"
        args = [node_exe, npm_cli_js, "run", "dev"]
        cwd = FRONTEND_DIR
        extra_env = {}
    else:
        return False, f"未知服务: {name}"

    # 6. 启动
    try:
        proc, log_fh = _detach_subprocess(args, cwd, log_file, extra_env, shell=use_shell)
    except FileNotFoundError as e:
        return False, f"{name:8s} 启动失败，可执行文件未找到: {e}"
    except Exception as e:
        return False, f"{name:8s} 启动失败: {e}"

    _write_pid(name, proc.pid)
    _log(f"{name:8s} 已启动 PID={proc.pid}，等待就绪（最多 {cfg['start_timeout']}s）...")

    # 7. 等待健康检查通过
    deadline = time.time() + cfg["start_timeout"]
    while time.time() < deadline:
        if not _process_alive(proc.pid):
            # 进程已退出 → 失败
            try:
                log_text = log_file.read_text(encoding="utf-8", errors="replace")[-600:]
            except OSError:
                log_text = "(无法读取日志文件)"
            try:
                log_fh.close()
            except Exception:
                pass
            return False, f"{name:8s} 启动后退出。日志尾部:\n{log_text}"

        if _http_ok(health_url, timeout=2):
            try:
                log_fh.close()
            except Exception:
                pass
            return True, f"{name:8s} 就绪 ({health_url})"

        time.sleep(1)

    # 超时
    return False, f"{name:8s} 启动超时（{cfg['start_timeout']}s 内未就绪）。查看 .runtime/{name}.log"


def stop_service(name, force=False):
    """停止单个服务。返回 (success, message)。"""
    cfg = SERVICES[name]
    port = cfg["port"]
    pid = _read_pid(name)

    if not pid:
        # PID 文件不存在，再用端口兜底检查
        if _port_in_use(port):
            _log(f"{name:8s} 无 PID 记录，但端口 {port} 仍被占用，尝试通过端口清理")
            return _stop_by_port(name, port)
        return True, f"{name:8s} 未运行"

    if not _process_alive(pid):
        _clear_pid(name)
        return True, f"{name:8s} 进程已不存在（PID={pid} 已失效），清理记录"

    _log(f"{name:8s} 正在终止 PID={pid} ...")
    ok = _kill_process_tree(pid)
    _clear_pid(name)

    # 兜底：端口仍在就继续杀
    if not ok and _port_in_use(port):
        ok2, msg2 = _stop_by_port(name, port)
        if ok2:
            return True, msg2

    if ok:
        return True, f"{name:8s} 已停止"
    return False, f"{name:8s} 停止失败（PID={pid}）"


def _stop_by_port(name, port):
    """通过 netstat 找到占用端口的 PID 并终止。"""
    try:
        out = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True, text=True, timeout=5
        ).stdout
        for line in out.splitlines():
            parts = line.split()
            if len(parts) >= 5 and f":{port}" in parts[1] and parts[-1].isdigit():
                p = int(parts[-1])
                if p > 0 and _process_alive(p):
                    _kill_process_tree(p)
                    return True, f"{name:8s} 通过端口定位已停止 (PID={p})"
    except (subprocess.SubprocessError, FileNotFoundError, ValueError):
        pass
    return False, f"{name:8s} 端口 {port} 仍在占用，但找不到进程"


# ============ 命令 ============

def cmd_start():
    _log("===== 启动 AIGC Platform 服务 =====")
    results = {}
    for name in ["backend", "frontend"]:
        ok, msg = start_service(name)
        results[name] = ok
        _log(f"  -> {msg}")
        # 后端失败就不启前端
        if name == "backend" and not ok:
            _log("后端未就绪，跳过前端启动")
            break

    all_ok = all(results.values()) and len(results) == 2
    if all_ok:
        _log("===== 全部服务启动成功 =====")
        _log(f"  后端 API : http://localhost:8000/api")
        _log(f"  API 文档 : http://localhost:8000/docs")
        _log(f"  前端界面 : http://localhost:3001")
        _log(f"  运行状态 : python {Path(__file__).name} status")
        _log(f"  查看日志 : python {Path(__file__).name} log backend|frontend")
    else:
        _log("===== 部分服务启动失败，查看 .runtime/*.log =====")
    return 0 if all_ok else 1


def cmd_stop():
    _log("===== 停止 AIGC Platform 服务 =====")
    any_fail = False
    for name in ["frontend", "backend"]:  # 先停前端，再停后端
        ok, msg = stop_service(name)
        _log(f"  -> {msg}")
        if not ok:
            any_fail = True

    # 最终确认端口释放
    time.sleep(1)
    for name in ["backend", "frontend"]:
        port = SERVICES[name]["port"]
        if _port_in_use(port):
            _log(f"  [WARN] {name} 端口 {port} 仍被占用，请手动检查")
            any_fail = True

    _log("===== 停止完成 =====")
    return 1 if any_fail else 0


def cmd_restart():
    _log("===== 重启 AIGC Platform 服务 =====")
    cmd_stop()
    time.sleep(2)
    return cmd_start()


def cmd_status():
    _log("===== AIGC Platform Status =====")
    _log(f"  Runtime dir: {RUNTIME_DIR}")
    _log("")
    all_ok = True
    for name in ["backend", "frontend"]:
        cfg = SERVICES[name]
        pid = _read_pid(name)
        alive = pid is not None and _process_alive(pid)
        http_ok = _http_ok(cfg["health_url"], timeout=3)

        if alive and http_ok:
            icon = "[OK]"
        elif alive or _port_in_use(cfg["port"]):
            icon = "[? ]"  # 进程在但API未就绪
            all_ok = False
        else:
            icon = "[--]"
            all_ok = False

        http_text = "OK" if http_ok else "N/A"
        _log(f"  {icon} {name:8s}  PID={pid or '-':<6}  port={cfg['port']}  HTTP={http_text}")

    _log("")
    _log(f"  Log files:")
    for name in ["backend", "frontend"]:
        lf = SERVICES[name]["log_file"]
        size = lf.stat().st_size if lf.exists() else 0
        _log(f"    - {name:8s}: {lf} ({size} bytes)")
    return 0 if all_ok else 1


def cmd_log(target):
    name_map = {"b": "backend", "back": "backend", "backend": "backend",
                "f": "frontend", "front": "frontend", "frontend": "frontend"}
    name = name_map.get(target.lower())
    if not name and target.lower() in ("all", "*", "a", ""):
        _print_log_tail("backend", lines=20)
        print()
        _print_log_tail("frontend", lines=20)
        return 0
    if not name:
        print(f"Usage: python launcher.py log <backend|frontend|all>")
        return 1
    _print_log_tail(name, lines=80)
    return 0


def _print_log_tail(name, lines=50):
    lf = SERVICES[name]["log_file"]
    print(f"===== {name}.log (last {lines} lines) =====")
    if not lf.exists():
        print("  (log file does not exist)")
        return
    try:
        text = lf.read_text(encoding="utf-8", errors="replace")
        out_lines = text.splitlines()[-lines:]
        for line in out_lines:
            try:
                print("  " + line)
            except UnicodeEncodeError:
                safe_line = line.encode("ascii", errors="replace").decode("ascii")
                print("  " + safe_line)
    except OSError as e:
        print(f"  read failed: {e}")


# ============ 入口 ============

def main():
    argv = sys.argv[1:]
    cmd = argv[0].lower() if argv else "start"

    if cmd in ("start", "up", "run"):
        return cmd_start()
    elif cmd in ("stop", "down", "kill"):
        return cmd_stop()
    elif cmd in ("restart", "reload"):
        return cmd_restart()
    elif cmd in ("status", "check", "ps"):
        return cmd_status()
    elif cmd in ("log", "logs", "view"):
        return cmd_log(argv[1] if len(argv) > 1 else "all")
    elif cmd in ("help", "--help", "-h", "?"):
        print(__doc__)
        return 0
    else:
        print(f"未知命令: {cmd}")
        print(__doc__)
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n已中断")
        sys.exit(130)
