#!/usr/bin/env python3
"""
StockMoney 三方同步脚本

保持 GitHub <-> 本地 <-> Ubuntu 服务器三方代码同步。

用法:
  python deploy/sync.py push       # 本地 push -> GitHub -> 服务器 pull
  python deploy/sync.py pull       # 服务器修改 -> GitHub -> 本地 pull
  python deploy/sync.py status     # 查看三方状态
  python deploy/sync.py exec "cmd" # 在服务器执行命令

作者: Claude Code
日期: 2026-05-01
"""

import argparse
import os
import subprocess
import sys

SERVER_HOST = "192.168.50.6"
SERVER_USER = "yinlin"
SERVER_PASSWORD = os.environ.get("STOCKMONEY_SERVER_PASSWORD", "")
SERVER_DIR = "/opt/stockmoney"

if not SERVER_PASSWORD:
    print("错误: 请设置环境变量 STOCKMONEY_SERVER_PASSWORD")
    print("  Windows: set STOCKMONEY_SERVER_PASSWORD=your_password")
    print("  Linux/Mac: export STOCKMONEY_SERVER_PASSWORD=your_password")
    sys.exit(1)


def run_local(cmd: str, timeout: int = 60) -> tuple[int, str, str]:
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    return result.returncode, result.stdout, result.stderr


def run_remote(cmd: str, timeout: int = 60) -> tuple[int, str, str]:
    import paramiko
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD,
                   timeout=10, look_for_keys=False, allow_agent=False)
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    client.close()
    return 0 if not err.strip() else 0, out, err


def cmd_status():
    """查看三方状态"""
    print("=" * 60)
    print("StockMoney 三方同步状态")
    print("=" * 60)

    # Local
    code, out, err = run_local("git log --oneline -1 && git status --short")
    print("\n[本地 main]")
    print(out if code == 0 else err)

    # GitHub
    code, out, err = run_local("git log origin/main --oneline -1 2>/dev/null")
    print("\n[GitHub origin/main]")
    print(out if code == 0 else "无法获取")

    # Server
    _, out, err = run_remote(f"cd {SERVER_DIR} && git log --oneline -1 && echo '---' && git status --short")
    print("\n[服务器 /opt/stockmoney]")
    print(out if not err.strip() else err)


def cmd_push():
    """本地修改 -> GitHub -> 服务器更新"""
    print("=" * 60)
    print("Push: 本地 -> GitHub -> 服务器")
    print("=" * 60)

    # 1. Check local status
    code, out, _ = run_local("git status --short")
    if out.strip():
        print("\n[1/4] 本地有未提交修改，请先手动 commit:")
        print(out)
        print("\n建议操作:")
        print("  git add <files>")
        print('  git commit -m "your message"')
        print("  python deploy/sync.py push")
        return False
    print("\n[1/4] 本地工作区干净 ✓")

    # 2. Push to GitHub
    code, out, err = run_local("git push origin main")
    if code != 0:
        print(f"\n[2/4] Push 到 GitHub 失败:")
        print(err or out)
        return False
    print("\n[2/4] Push 到 GitHub 成功 ✓")

    # 3. Server pull
    _, out, err = run_remote(f"cd {SERVER_DIR} && git pull origin main 2>&1")
    if "error" in (out + err).lower():
        print(f"\n[3/4] 服务器 pull 失败:")
        print(out + err)
        return False
    print("\n[3/4] 服务器 pull 成功 ✓")

    # 4. Verify server runs
    _, out, err = run_remote(
        f"cd {SERVER_DIR} && source venv/bin/activate && python scripts/strategy_engine.py --decision 2>&1 | head -5"
    )
    if "error" in (out + err).lower() or "Traceback" in (out + err):
        print(f"\n[4/4] 服务器运行验证失败:")
        print(out + err)
        return False
    print("\n[4/4] 服务器运行验证通过 ✓")

    print("\n" + "=" * 60)
    print("同步完成！")
    print("=" * 60)
    return True


def cmd_pull():
    """获取服务器/GitHub上的更新到本地"""
    print("=" * 60)
    print("Pull: GitHub -> 本地")
    print("=" * 60)

    code, out, err = run_local("git pull origin main")
    print(out if code == 0 else err)

    if code == 0:
        print("\n同步完成 ✓")
    else:
        print("\n同步失败，请解决冲突")
    return code == 0


def cmd_exec(remote_cmd: str):
    """在服务器执行命令"""
    print(f"[服务器执行] {remote_cmd}")
    _, out, err = run_remote(remote_cmd)
    print(out)
    if err.strip():
        print("STDERR:", err)


def main():
    parser = argparse.ArgumentParser(description="StockMoney 三方同步")
    parser.add_argument("action", choices=["push", "pull", "status", "exec"],
                        help="同步操作")
    parser.add_argument("--cmd", type=str, default="",
                        help="exec 模式下要执行的命令")
    args = parser.parse_args()

    if args.action == "status":
        cmd_status()
    elif args.action == "push":
        ok = cmd_push()
        sys.exit(0 if ok else 1)
    elif args.action == "pull":
        ok = cmd_pull()
        sys.exit(0 if ok else 1)
    elif args.action == "exec":
        if not args.cmd:
            print("请提供 --cmd 参数")
            sys.exit(1)
        cmd_exec(args.cmd)


if __name__ == "__main__":
    main()
