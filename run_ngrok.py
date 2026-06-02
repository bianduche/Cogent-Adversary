"""
run_ngrok.py - 使用 ngrok 将本地 Flask 应用暴露到公网
使用方法: pip install pyngrok>=7.0.0 && python run_ngrok.py

启动顺序（关键）：
  1. 先杀残留 ngrok.exe 进程（不通过 pyngrok，避免触发默认配置启动）
  2. 再设置 ngrok config（随机 web_addr，避开 4040 冲突）
  3. 最后启动 Flask + ngrok 隧道
"""

from pyngrok import ngrok, conf
import subprocess
import time
import sys
import os
import json
import socket

# ============ 配置区 ============
NGROK_AUTH_TOKEN = "38n4kXSE9GkQF7j44nUG9Nl4Pos_3EpPnTtJwjuyPagV2Se31"
FLASK_APP = "app.py"
# ================================


def find_free_port() -> int:
    """找一个本机可用的随机端口"""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def load_config_port() -> int:
    """自动从 config.json 读取 Flask 端口"""
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            return int(json.load(f).get("port", 5000))
    except Exception:
        return 5000


def kill_ngrok_processes():
    """
    用系统命令杀 ngrok 进程，不通过 pyngrok API。
    关键：避免 pyngrok 在杀进程时启动新的 ngrok（带默认 4040 配置）。
    """
    print("[INFO] 清理残留 ngrok 进程...")
    # Windows taskkill
    subprocess.run(
        ["taskkill", "/F", "/IM", "ngrok.exe"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=5,
    )
    # 再调一次 pyngrok 的 kill（清理可能残留的 .ngrok 进程记录）
    try:
        ngrok.kill()
    except Exception:
        pass
    time.sleep(3)
    print("[INFO] ngrok 进程清理完成")


def set_ngrok_config():
    """在启动 ngrok 之前，先设置配置（随机 web_addr）"""
    web_port = find_free_port()
    ngrok_config = conf.get_default()
    ngrok_config.web_addr = f"127.0.0.1:{web_port}"
    conf.set_default(ngrok_config)
    print(f"[INFO] ngrok Web 管理端口分配为: {web_port}")


def print_urls(public_url: str):
    """打印三个端的访问网址"""
    print()
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║                  Cogent-Adversary 公网访问地址                       ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print()
    print(f"  👨🏫  教师端：  {public_url}/teacher")
    print()
    print(f"  👨🎓  学生端：  {public_url}/?group=SA&sid=S001")
    print("         参数：group=SA/FA/RA/CA，sid=学号（如 S001）")
    print()
    print(f"  📋  问卷端：  {public_url}/survey?sid=S001&session=1")
    print("         参数：sid=学号，session=课时序号（1-10）")
    print()
    print(f"  🖥️   本地：  http://localhost:{LOCAL_PORT}")
    print()
    print("=" * 72)
    print()


def main():
    global LOCAL_PORT

    # 1. 读取 Flask 端口
    LOCAL_PORT = load_config_port()
    print(f"[INFO] 从 config.json 读取到端口: {LOCAL_PORT}")

    # 2. 【关键顺序】杀残留进程（不通过 pyngrok，避免触发默认配置）
    kill_ngrok_processes()

    # 3. 【关键顺序】先设置 ngrok 配置，再碰任何 ngrok API
    set_ngrok_config()

    # 4. 设置 authtoken（此时 config 已含随机 web_addr）
    ngrok.set_auth_token(NGROK_AUTH_TOKEN)
    print("[INFO] ngrok authtoken 已配置")

    # 5. 断开残留隧道（此时 ngrok 会用正确配置启动）
    try:
        for t in ngrok.get_tunnels():
            try:
                ngrok.disconnect(t.public_url)
                print(f"[INFO] 已断开残留隧道: {t.public_url}")
            except Exception:
                pass
    except Exception:
        pass

    # 6. 启动 Flask 子进程（UTF-8 编码，根治 Windows GBK 解码崩溃）
    flask_cmd = [sys.executable, FLASK_APP]
    print(f"[INFO] 启动 Flask: {' '.join(flask_cmd)}")

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    flask_proc = subprocess.Popen(
        flask_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        env=env,
    )

    time.sleep(4)

    if flask_proc.poll() is not None:
        # 读取错误输出
        err = flask_proc.stdout.read() if flask_proc.stdout else "(无输出)"
        print(f"[ERROR] Flask 启动失败：\n{err}")
        sys.exit(1)

    print(f"[INFO] Flask 已启动，监听端口 {LOCAL_PORT}")

    # 7. 启动 ngrok 隧道
    try:
        tunnel = ngrok.connect(LOCAL_PORT)
        public_url = tunnel.public_url
    except Exception as e:
        print(f"[ERROR] 启动 ngrok 失败: {e}")
        flask_proc.terminate()
        sys.exit(1)

    # 8. 打印三个端的网址
    print_urls(public_url)

    # 9. 保持运行，转发 Flask 日志
    try:
        for line in flask_proc.stdout:
            print(line, end="", flush=True)
    except KeyboardInterrupt:
        print("\n[INFO] 收到停止信号，正在关闭...")
    finally:
        flask_proc.terminate()
        try:
            ngrok.kill()
        except Exception:
            pass
        print("[INFO] Flask 和 ngrok 已停止")


if __name__ == "__main__":
    main()
