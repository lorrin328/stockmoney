import paramiko
import os

files = [
    ('scripts/research_driver.py', '/opt/stockmoney/scripts/research_driver.py'),
]

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('192.168.50.6', username='yinlin', password='Aaaaa8888%', timeout=10, look_for_keys=False, allow_agent=False)
sftp = client.open_sftp()

for local, remote in files:
    sftp.put(os.path.join(r'f:\obsidian\生活\coding\stockmoney', local), remote)
    client.exec_command(f'chmod +x {remote}')
    print(f"Uploaded: {os.path.basename(local)}")

sftp.close()
client.close()
print("Done")
