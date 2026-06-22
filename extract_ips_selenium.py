import time
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

def extract_cloudflare_specific_ips(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")  # 已修正错别字
    chrome_options.add_argument("--disable-gpu")
    
    # 自动管理ChromeDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    target_ips = []
    try:
        driver.get(url)

        # 显式等待表格内容加载
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'table.table-striped tbody tr'))
        )
        
        # 严格等待 5 秒确保数据刷新
        print("等待5秒，确保页面内容更新到最新实时数据...")
        time.sleep(5)
        
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

        # 定义需要提取的行号集合 (1-based index)
        # 包含 1-4, 31-33, 41-43
        target_rows = set(list(range(1, 5)) + list(range(31, 34)) + list(range(41, 44)))

        # 遍历 tbody 中的所有行，start=1 表示行号从 1 开始计算
        for row_num, row in enumerate(tbody.find_all('tr'), start=1):
            
            # 如果当前行号在我们需要的范围内，则进行解析
            if row_num in target_rows:
                cols = row.find_all('td')
                if len(cols) > 1:
                    ip_address = cols[1].text.strip()
                    line_type = cols[0].text.strip()  # 顺便获取线路类型方便调试打印
                    
                    if ip_address:
                        print(f"[行号 {row_num}] 线路: {line_type} -> IP: {ip_address}")
                        target_ips.append(ip_address)
            
            # 优化：如果当前行号已经超过了最大的目标行（43行），可以直接中断循环，节省时间
            if row_num > 43:
                break

        return target_ips

    except Exception as e:
        print(f"Selenium 提取失败: {e}")
        return []
    finally:
        driver.quit()

def main():
    url = "https://api.uouin.com/cloudflare.html"
    ips = extract_cloudflare_specific_ips(url)

    if ips:
        print(f"\n成功提取到特定的 {len(ips)} 个 IP 数据：")
        for ip in ips:
            print(ip)

        # 保存逻辑
        output_dir = 'data'
        os.makedirs(output_dir, exist_ok=True)
        output_filename = os.path.join(output_dir, "cloudflare_specific_ips.txt")

        with open(output_filename, 'w', encoding='utf-8') as f:
            for ip in ips:
                f.write(f"{ip}\n")
        
        print(f"\n数据已保存到 {output_filename}")
    else:
        print("未能提取到指定行号的 IP 数据。")

if __name__ == "__main__":
    main()
