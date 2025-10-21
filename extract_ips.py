import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os

def extract_cloudflare_ips(url):
    """
    从 Cloudflare 优选 IP 页面提取 IP 信息。
    """
    try:
        response = requests.get(url)
        response.raise_for_status() # 检查HTTP请求是否成功
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 定位到表格的 tbody
    # 查找 class 为 'table table-striped' 的表格
    table = soup.find('table', class_='table table-striped')
    if not table:
        print("未找到表格元素。")
        return None
    
    tbody = table.find('tbody')
    if not tbody:
        print("未找到表格的 tbody 元素。")
        return None

    ips_data = []
    # 遍历 tbody 中的所有行
    for i, row in enumerate(tbody.find_all('tr')):
        # 提取每一列的数据
        cols = row.find_all('td')
        if len(cols) >= 5: # 确保至少有线路、IP、丢包、延迟、速度等列
            line = cols[0].text.strip()
            ip_address = cols[1].text.strip()
            # 丢包率通常是第三列，这里是第四个<td>元素（索引3）
            # 但是你的HTML示例中，<td>前面是<th>，所以cols[2]是IP，cols[3]是丢包
            # 根据你提供的HTML，是：
            # <td>线路</td> (cols[0])
            # <td>优选IP</td> (cols[1])
            # <td class="asn">丢包</td> (cols[2])
            # <td>延迟</td> (cols[3])
            # <td class="asn">速度</td> (cols[4])
            # <td class="asn">带宽</td> (cols[5])
            # <td class="asn">Colo</td> (cols[6])
            # <td class="asn">时间</td> (cols[7])
            
            # 重新检查 HTML 结构，th scope="row" 是第一列，所以实际数据从第二列开始
            # <th scope="row">1</th>
            # <td>电信</td> # cols[0]
            # <td>172.64.82.114</td> # cols[1]
            # <td class="asn">0.00%</td> # cols[2]
            # <td>136.85ms</td> # cols[3]
            # <td class="asn">6.92mb/s</td> # cols[4]
            # <td class="asn">55.36mb</td> # cols[5]
            # <td class="asn">...</td> # cols[6]
            # <td class="asn">...</td> # cols[7]

            line = cols[0].text.strip()
            ip_address = cols[1].text.strip()
            packet_loss = cols[2].text.strip()
            latency = cols[3].text.strip()
            speed_mbps = cols[4].text.strip()
            bandwidth_mb = cols[5].text.strip()
            colo_link = cols[6].find('a')['href'] if cols[6].find('a') else ''
            update_time = cols[7].text.strip()
            
            # 我们只关心排序前十的IP，这里的“排序”是根据表格的行号
            # 或者你可以根据某个性能指标进行自定义排序，但由于页面本身已经按某种顺序排列，
            # 并且你指定了“排序前十”，我们直接取前十行即可。
            # 注意：此处取的是整个表格的前10行，不区分线路类型。
            # 如果需要每种线路（电信、联通、移动、多线）各取前十，则需要更复杂的逻辑。
            # 假设你指的是整个列表的前十。

            ips_data.append({
                '排序': i + 1,
                '线路': line,
                '优选IP': ip_address,
                '丢包': packet_loss,
                '延迟': latency,
                '速度': speed_mbps,
                '带宽': bandwidth_mb,
                'Colo链接': colo_link,
                '更新时间': update_time
            })
            if len(ips_data) >= 10: # 提取前十行
                break
    return ips_data

def main():
    url = "https://api.uouin.com/cloudflare.html"
    ips = extract_cloudflare_ips(url)

    if ips:
        df = pd.DataFrame(ips)
        print("成功提取到IP数据：")
        print(df)

        # 构建输出文件名，包含日期和时间
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_dir = 'data'
        os.makedirs(output_dir, exist_ok=True) # 创建数据目录如果不存在
        output_filename = os.path.join(output_dir, f"cloudflare_top10_ips_{timestamp}.csv")
        
        df.to_csv(output_filename, index=False, encoding='utf-8-sig')
        print(f"\n数据已保存到 {output_filename}")
    else:
        print("未能提取IP数据。")

if __name__ == "__main__":
    main()
