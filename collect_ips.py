import requests
from bs4 import BeautifulSoup
import re
import os

# 目标URL列表
urls = [
    'https://ip.164746.xyz/',
]

# 正则表达式用于匹配IP地址 (这里我们仍保留，以防万一BeautifulSoup提取的文本中需要二次确认)
ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'

# 检查ip.txt文件是否存在,如果存在则删除它
if os.path.exists('ip.txt'):
    os.remove('ip.txt')

# 使用列表存储IP地址
all_ips = []

for url in urls:
    try:
        # 发送HTTP请求获取网页内容
        response = requests.get(url, timeout=10) # 增加超时时间以提高稳定性
        
        # 确保请求成功
        if response.status_code == 200:
            # 使用BeautifulSoup解析网页内容
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 找到表格的tbody部分
            # 根据你提供的HTML，表格的IP数据在<tbody>标签内，每个IP在<tr>中
            tbody = soup.find('table', class_='table').find('tbody')
            
            if tbody:
                # 遍历tbody中的所有<tr>标签
                rows = tbody.find_all('tr')
                
                # 只处理前10行数据
                for i, row in enumerate(rows):
                    if i >= 10: # 序号从1开始，所以索引0-9对应序号1-10
                        break
                    
                    # 找到每个<tr>中的第三个<td>标签，它包含IP地址
                    # th scope="row" 是序号，第一个td是线路，第二个td是优选IP
                    cols = row.find_all(['th', 'td']) 
                    if len(cols) > 2: # 确保有足够的列
                        ip_cell = cols[2] # IP地址在第三列 (索引2)
                        ip_address = ip_cell.get_text(strip=True)
                        
                        # 再次使用正则表达式验证提取的IP地址是否符合格式
                        if re.match(ip_pattern, ip_address):
                            all_ips.append(ip_address)
            else:
                print(f"在 {url} 中未找到表格或tbody。")
                
    except requests.exceptions.RequestException as e:
        print(f'请求 {url} 失败: {e}')
        continue
    except Exception as e:
        print(f'解析 {url} 时发生错误: {e}')
        continue

# 将所有IP地址写入文件
if all_ips:
    with open('ip.txt', 'w') as file:
        for ip in all_ips:
            file.write(ip + '\n')
    print(f'已保存 {len(all_ips)} 个IP地址（前10个）到ip.txt文件。')
else:
    print('未找到有效的IP地址。')
