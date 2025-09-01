import os
import signal
import sys
import subprocess

print("""
 $$$$$$\  $$$$$$$\  $$$$$$$$\ $$\   $$\       $$$$$$$$\ $$\     $$\ $$$$$$$$\  $$$$$$\  
$$  __$$\ $$  __$$\ $$  _____|$$$\  $$ |      $$  _____|\$$\   $$  |$$  _____|$$  __$$\ 
$$ /  $$ |$$ |  $$ |$$ |      $$$$\ $$ |      $$ |       \$$\ $$  / $$ |      $$ /  \__|
$$ |  $$ |$$$$$$$  |$$$$$\    $$ $$\$$ |      $$$$$\      \$$$$  /  $$$$$\    \$$$$$$\  
$$ |  $$ |$$  ____/ $$  __|   $$ \$$$$ |      $$  __|      \$$  /   $$  __|    \____$$\ 
$$ |  $$ |$$ |      $$ |      $$ |\$$$ |      $$ |          $$ |    $$ |      $$\   $$ |
 $$$$$$  |$$ |      $$$$$$$$\ $$ | \$$ |      $$$$$$$$\     $$ |    $$$$$$$$\ \$$$$$$  |
 \______/ \__|      \________|\__|  \__|      \________|    \__|    \________| \______/ 
"""
)

# 全局变量存储子进程
process = None

def signal_handler(sig, frame):
    print('\n接收到中断信号，正在关闭子进程...')
    if process and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
    print("子进程已关闭，程序退出。")
    sys.exit(0)

# 注册信号处理器
signal.signal(signal.SIGINT, signal_handler)

print("收集中...")
collection_command = """python src/collection/main.py -c configs/collection.json"""
print(f"启动指令：{collection_command}")

# 使用subprocess替代os.system以便更好地控制子进程
process = subprocess.Popen(collection_command, shell=True)
process.wait()

print("收集完成")