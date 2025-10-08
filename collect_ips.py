import requests
import re
import os

# 目标URL列表
urls = [
    'https://api.uouin.com/cloudflare.html',
]

# 正则表达式用于匹配IP地址
ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'

# 检查ip.txt文件是否存在,如果存在则删除它
if os.path.exists('ip.txt'):
    os.remove('ip.txt')

# 用于存储所有找到的IP地址的列表
all_ips = []

for url in urls:
    try:
        # 发送HTTP请求获取网页内容
        response = requests.get(url, timeout=5)
        
        # 确保请求成功
        if response.status_code == 200:
            # 获取网页的文本内容
            html_content = response.text
            
            # 使用正则表达式查找IP地址
            ip_matches = re.findall(ip_pattern, html_content, re.IGNORECASE)
            
            # 将找到的IP添加到列表中
            all_ips.extend(ip_matches)
    except requests.exceptions.RequestException as e:
        print(f'请求 {url} 失败: {e}')
        continue

# 仅保留前10个IP地址
ips_to_save = all_ips[:10]

# 将IP地址写入文件
if ips_to_save:
    with open('ip.txt', 'w') as file:
        for ip in ips_to_save:
            file.write(ip + '\n')
    print(f'已保存 {len(ips_to_save)} 个IP地址到ip.txt文件（取前10个，未去重和排序）。')
else:
    print('未找到有效的IP地址。')
