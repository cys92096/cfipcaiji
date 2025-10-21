from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import os
from bs4 import BeautifulSoup # 仍然需要BeautifulSoup来解析页面HTML

def extract_cloudflare_top_10_ips(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # 自动管理ChromeDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    top_ips = []
    try:
        driver.get(url)

        # 显式等待表格内容加载
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'table.table-striped tbody tr'))
        )
        
        # 获取页面的完整HTML内容，并用BeautifulSoup解析
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        table = soup.find('table', class_='table table-striped')
        if not table:
            print("未找到表格元素。")
            return []
        
        tbody = table.find('tbody')
        if not tbody:
            print("未找到表格的 tbody 元素。")
            return []

        # 遍历 tbody 中的所有行，提取IP地址
        # 我们需要找到“优选IP”这一列
        
        # 你的HTML结构是这样的：
        # <tr>
        #   <th scope="row">1</th>
        #   <td>电信</td>  <- 这是第一个 <td> (index 0)
        #   <td>172.64.82.114</td> <- 这是第二个 <td> (index 1)，即IP地址
        #   ...
        # </tr>

        for i, row in enumerate(tbody.find_all('tr')):
            cols = row.find_all('td')
            if len(cols) > 1: # 确保至少有线路和IP两列
                ip_address = cols[1].text.strip() # IP地址在第二个<td>元素
                if ip_address: # 确保IP地址不为空
                    top_ips.append(ip_address)
                    if len(top_ips) >= 10: # 只提取前10个IP
                        break
        return top_ips

    except Exception as e:
        print(f"Selenium 提取失败: {e}")
        return []
    finally:
        driver.quit()

def main():
    url = "https://api.uouin.com/cloudflare.html"
    ips = extract_cloudflare_top_10_ips(url)

    if ips:
        print("成功提取到IP数据：")
        for ip in ips:
            print(ip)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_dir = 'data'
        os.makedirs(output_dir, exist_ok=True) # 创建数据目录如果不存在
        output_filename = os.path.join(output_dir, "cloudflare_top10_ips.txt") # 固定文件名，每次覆盖

        # 将IP地址写入TXT文件，每个IP一行
        with open(output_filename, 'w', encoding='utf-8') as f:
            for ip in ips:
                f.write(f"{ip}\n")
        
        print(f"\n数据已保存到 {output_filename}")
    else:
        print("未能提取IP数据。")

if __name__ == "__main__":
    main()
