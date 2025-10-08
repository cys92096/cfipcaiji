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

# 使用列表存储IP地址，不进行去重和排序
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
            
            # 将找到的IP添加到列表中（不进行去重）
            all_ips.extend(ip_matches) # 使用extend将匹配到的IP列表添加到all_ips中
    except requests.exceptions.RequestException as e:
        print(f'请求 {url} 失败: {e}')
        continue

# 将所有IP地址写入文件（不进行去重和排序）
if all_ips:
    with open('ip.txt', 'w') as file:
        for ip in all_ips:
            file.write(ip + '\n')
    print(f'已保存 {len(all_ips)} 个IP地址到ip.txt文件。')
else:
    print('未找到有效的IP地址。')
