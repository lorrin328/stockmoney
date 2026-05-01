import paramiko
import os

def upload_file(local_path, remote_path):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('192.168.50.6', username='yinlin', password='Aaaaa8888%', timeout=10, look_for_keys=False, allow_agent=False)
    sftp = client.open_sftp()
    sftp.put(local_path, remote_path)
    sftp.close()
    client.close()
    print(f"Uploaded: {os.path.basename(local_path)}")

base = r'f:\obsidian\生活\coding\stockmoney'

files = [
    ('scripts/kondratiev_model.py', '/opt/stockmoney/scripts/kondratiev_model.py'),
    ('scripts/cycle_phase_evaluator.py', '/opt/stockmoney/scripts/cycle_phase_evaluator.py'),
    ('scripts/market_indicators.py', '/opt/stockmoney/scripts/market_indicators.py'),
    ('scripts/asset_allocator.py', '/opt/stockmoney/scripts/asset_allocator.py'),
    ('scripts/strategy_engine.py', '/opt/stockmoney/scripts/strategy_engine.py'),
    ('scripts/four_percent_model.py', '/opt/stockmoney/scripts/four_percent_model.py'),
    ('scripts/investment_monitor.py', '/opt/stockmoney/scripts/investment_monitor.py'),
    ('scripts/policy_analyzer.py', '/opt/stockmoney/scripts/policy_analyzer.py'),
    ('scripts/sina_fetcher.py', '/opt/stockmoney/scripts/sina_fetcher.py'),
    ('data/portfolio_config.json', '/opt/stockmoney/data/portfolio_config.json'),
    ('deploy/exec_remote.py', '/opt/stockmoney/deploy/exec_remote.py'),
    ('README.md', '/opt/stockmoney/README.md'),
]

for local, remote in files:
    upload_file(os.path.join(base, local), remote)

print("All files uploaded.")
