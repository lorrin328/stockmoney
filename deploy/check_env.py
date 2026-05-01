import paramiko
import sys

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('192.168.50.6', username='yinlin', password='Aaaaa8888%', timeout=10, look_for_keys=False, allow_agent=False)

cmd = """
echo "=== SYSTEM INFO ==="
whoami && hostname && uname -a
echo ""
echo "=== OPENCLAW ==="
ls -la /opt/openclaw 2>/dev/null || echo "NO /opt/openclaw"
ls -la ~/openclaw 2>/dev/null || echo "NO ~/openclaw"
ps aux | grep -i openclaw | grep -v grep || echo "NO openclaw process"
echo ""
echo "=== CLAUDE CODE CLI ==="
which claude 2>/dev/null || echo "NO claude"
echo ""
echo "=== NODE ==="
node -v 2>/dev/null || echo "NO node"
npm -v 2>/dev/null || echo "NO npm"
pnpm -v 2>/dev/null || echo "NO pnpm"
echo ""
echo "=== PYTHON ==="
python3 --version 2>/dev/null || echo "NO python3"
pip3 --version 2>/dev/null || echo "NO pip3"
echo ""
echo "=== GIT ==="
git --version 2>/dev/null || echo "NO git"
echo ""
echo "=== TMUX ==="
which tmux 2>/dev/null || echo "NO tmux"
echo ""
echo "=== PORTS ==="
ss -tlnp 2>/dev/null | grep -E '3000|8080|22' || netstat -tlnp 2>/dev/null | grep -E '3000|8080|22' || echo "NO ss/netstat"
echo ""
echo "=== SUDO ==="
sudo -n true 2>/dev/null && echo "HAS sudo" || echo "NO sudo"
"""

stdin, stdout, stderr = client.exec_command(cmd)
out = stdout.read().decode('utf-8', errors='replace')
err = stderr.read().decode('utf-8', errors='replace')
print(out)
if err.strip():
    print('STDERR:', err)
client.close()
