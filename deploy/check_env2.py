import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('192.168.50.6', username='yinlin', password='Aaaaa8888%', timeout=10, look_for_keys=False, allow_agent=False)

cmd = """
echo "=== FIND OPENCLAW ==="
find / -name "openclaw" -type d 2>/dev/null | head -10
find / -name "openclaw-gateway" -type f 2>/dev/null | head -5
which openclaw 2>/dev/null || echo "NO openclaw in PATH"
echo ""
echo "=== OPENCLAW PROCESS DETAILS ==="
cat /proc/1139293/cmdline 2>/dev/null | tr '\\0' ' ' || echo "NO proc info"
ls -la /proc/1139293/cwd 2>/dev/null || echo "NO cwd"
echo ""
echo "=== OPENCLAW CONFIG ==="
find / -name ".env" -path "*openclaw*" 2>/dev/null | head -5
find / -name "config.yaml" -path "*openclaw*" 2>/dev/null | head -5
find / -name "integrations" -type d -path "*openclaw*" 2>/dev/null | head -5
echo ""
echo "=== FEISHU/WEBHOOK CONFIG ==="
grep -r "feishu\|lark\|webhook\|bot" /opt/openclaw 2>/dev/null | head -10 || true
grep -r "feishu\|lark\|webhook\|bot" ~/.config/openclaw 2>/dev/null | head -10 || true
grep -r "feishu\|lark\|webhook\|bot" ~/openclaw 2>/dev/null | head -10 || true
echo ""
echo "=== NPM GLOBAL ==="
npm list -g --depth=0 2>/dev/null | head -20
echo ""
echo "=== DISK SPACE ==="
df -h /opt /home 2>/dev/null | head -5
echo ""
echo "=== PYTHON PACKAGES ==="
pip3 list 2>/dev/null | grep -iE "numpy|pandas|request|akshare|paramiko" || echo "none installed"
"""

stdin, stdout, stderr = client.exec_command(cmd)
out = stdout.read().decode('utf-8', errors='replace')
err = stderr.read().decode('utf-8', errors='replace')
print(out)
if err.strip():
    print('STDERR:', err)
client.close()
