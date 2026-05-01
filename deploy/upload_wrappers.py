import paramiko
import os

scripts = {
    '/opt/stockmoney/scripts/run_monitor.sh': '''#!/bin/bash
cd /opt/stockmoney
source venv/bin/activate
python scripts/investment_monitor.py > /tmp/stockmoney_monitor.log 2>&1
cat /tmp/stockmoney_monitor.log
''',
    '/opt/stockmoney/scripts/run_strategy.sh': '''#!/bin/bash
cd /opt/stockmoney
source venv/bin/activate
python scripts/strategy_engine.py --decision > /tmp/stockmoney_strategy.log 2>&1
cat /tmp/stockmoney_strategy.log
''',
    '/opt/stockmoney/scripts/run_policy.sh': '''#!/bin/bash
cd /opt/stockmoney
source venv/bin/activate
python scripts/policy_analyzer.py --summary > /tmp/stockmoney_policy.log 2>&1
cat /tmp/stockmoney_policy.log
''',
    '/opt/stockmoney/scripts/run_full_report.sh': '''#!/bin/bash
cd /opt/stockmoney
source venv/bin/activate
python scripts/strategy_engine.py --report > /tmp/stockmoney_report.log 2>&1
cat /tmp/stockmoney_report.log
''',
}

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('192.168.50.6', username='yinlin', password='Aaaaa8888%', timeout=10, look_for_keys=False, allow_agent=False)
sftp = client.open_sftp()

for remote_path, content in scripts.items():
    with sftp.file(remote_path, 'w') as f:
        f.write(content)
    client.exec_command(f'chmod +x {remote_path}')
    print(f"Created: {os.path.basename(remote_path)}")

sftp.close()
client.close()
print("All wrapper scripts created.")
