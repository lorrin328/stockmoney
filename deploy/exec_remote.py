import paramiko
import sys
import re

def clean_text(text):
    """Remove problematic Unicode chars for Windows console"""
    # Remove chars that GBK can't encode
    return text.encode('ascii', 'replace').decode('ascii')

def run_cmd(cmd, timeout=60):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('192.168.50.6', username='yinlin', password='Aaaaa8888%', timeout=10, look_for_keys=False, allow_agent=False)
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout, get_pty=True)
    import time
    out_data = []
    err_data = []
    start = time.time()
    while not stdout.channel.exit_status_ready() and time.time() - start < timeout:
        if stdout.channel.recv_ready():
            out_data.append(stdout.channel.recv(4096).decode('utf-8', errors='replace'))
        if stdout.channel.recv_stderr_ready():
            err_data.append(stdout.channel.recv_stderr(4096).decode('utf-8', errors='replace'))
        time.sleep(0.5)
    while stdout.channel.recv_ready():
        out_data.append(stdout.channel.recv(4096).decode('utf-8', errors='replace'))
    while stdout.channel.recv_stderr_ready():
        err_data.append(stdout.channel.recv_stderr(4096).decode('utf-8', errors='replace'))
    out = ''.join(out_data)
    err = ''.join(err_data)
    client.close()
    return out, err

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'echo hello'
    out, err = run_cmd(cmd)
    print(clean_text(out))
    if err.strip():
        print('STDERR:', clean_text(err))
