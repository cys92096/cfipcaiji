import time # 添加这一行
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import os
from bs4 import BeautifulSoup

def extract_cloudflare_top_10_ips(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev_shm-usage") # 注意这里是 disable-dev-shm-usage
    
    # 自动管理ChromeDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    top_ips = []
    try:
        driver.get(url)

        # 显式等待表格内容加载 (等待 tbody tr 出现)
        # 增加超时时间以应对潜在的网络延迟
        WebDriverWait(driver, 30).until( # 增加到30秒，更稳妥
            EC.presence_of_element_located((By.CSS_SELECTOR, 'table.table-striped tbody tr'))
        )
        
        # ！！！关键改进点！！！
        # 等待额外的5秒，让页面上的JavaScript有时间从旧数据更新到最新数据
        print("等待5秒，确保页面内容更新到最新实时数据...")
        time.sleep(5) # 根据实际观察到的延迟调整这个时间，5秒应该比较合适
        
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
        for i, row in enumerate(tbody.find_all('tr')):
            cols = row.find_all('td')
            # 根据截图，IP地址仍然在第二个<td>元素 (index 1)
            # 线路在第一个<td> (index 0)
            # 时间在最后一个<td> (index -1)
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

        # 时间戳和文件保存逻辑保持不变
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_dir = 'data'
        os.makedirs(output_dir, exist_ok=True)
        output_filename = os.path.join(output_dir, "cloudflare_top10_ips.txt")

        with open(output_filename, 'w', encoding='utf-8') as f:
            for ip in ips:
                f.write(f"{ip}\n")
        
        print(f"\n数据已保存到 {output_filename}")
    else:
        print("未能提取IP数据。")

if __name__ == "__main__":
    main()
