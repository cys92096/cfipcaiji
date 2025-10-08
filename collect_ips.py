import requests
from bs4 import BeautifulSoup
import re
import os # 导入 os 模块用于获取脚本所在目录

def get_fastest_ips_from_html(url):
    """
    从指定的URL获取HTML内容，解析其中的IP地址和速度，
    并返回速度最快的10个IP。
    """
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()  # 检查HTTP错误
        html_content = response.text

        soup = BeautifulSoup(html_content, 'html.parser')

        # 找到包含IP和速度的表格
        # 根据你提供的HTML，数据在 tbody 的 tr 标签中
        table_rows = soup.find('table', class_='table table-striped').find('tbody').find_all('tr')

        ip_speed_list = []
        for row in table_rows:
            # 提取所有td标签
            cols = row.find_all('td')
            # 确保有足够的列来提取IP和速度。
            # 优选IP在第2列 (索引为1)
            # 速度在第5列 (索引为4)
            # 所以至少需要5列 (索引0到4)
            if len(cols) >= 5: 
                ip_address = cols[1].get_text(strip=True)

                speed_text = cols[4].get_text(strip=True)
                
                # 处理 IPv6 地址的显示，移除方括号
                if ip_address.startswith('[') and ip_address.endswith(']'):
                    ip_address = ip_address[1:-1]

                try:
                    # 使用正则表达式提取数字，支持浮点数
                    speed_match = re.search(r'(\d+\.?\d*)\s*mb/s', speed_text, re.IGNORECASE)
                    if speed_match:
                        speed = float(speed_match.group(1))
                    else:
                        speed = 0.0 # 如果未能解析速度，则设为0
                except ValueError:
                    speed = 0.0 # 解析失败也设为0

                # 筛选 IPv4 或 IPv6，这里默认包含所有类型。
                # 如果你想只保留 IPv4，可以添加条件: if ':' not in ip_address:
                ip_speed_list.append((ip_address, speed))

        # 按照速度从大到小排序
        sorted_ips = sorted(ip_speed_list, key=lambda x: x[1], reverse=True)

        return sorted_ips[:10] # 返回速度最快的10个IP
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return []
    except Exception as e:
        print(f"Error parsing HTML: {e}")
        return []

def main():
    url = "https://api.uouin.com/cloudflare.html"
    print(f"正在从 {url} 解析速度最快的IP地址...")
    fastest_ips = get_fastest_ips_from_html(url)

    # 获取当前脚本的目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_filename = os.path.join(script_dir, "ip.txt") # 将ip.txt放在脚本同级目录

    with open(output_filename, "w") as f:
        if fastest_ips:
            print(f"\n速度最快的10个IP地址（已从网页提取）已写入到 {output_filename}：")
            for i, (ip, speed) in enumerate(fastest_ips):
                line = f"{ip} (速度: {speed:.2f} mb/s)"
                print(f"{i+1}. {line}")
                f.write(line + "\n")
        else:
            print("未能提取到有效的IP地址和速度信息。")
            f.write("未能提取到有效的IP地址和速度信息。\n")

    print(f"\n操作完成。")

if __name__ == "__main__":
    main()
