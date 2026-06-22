import time 
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import os
from bs4 import BeautifulSoup

def extract_cloudflare_specific_ips(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    selected_ips = []
    try:
        driver.get(url)

        # 显式等待表格内容加载 (死等 30 秒直到表格出来)
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'table.table-striped tbody tr'))
        )
        
        # 稳定策略：强制等待 5 秒，让所有数据（包括最下方的 IPv6）完全加载完
        print("等待5秒，确保页面内容更新到最新实时数据...")
        time.sleep(5) 
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        table = soup.find('table', class_='table table-striped')
        if not table:
            return []
        
        tbody = table.find('tbody')
        if not tbody:
            return []

        # 精准锁定：1-4 (电信)、31-33 (多线)、41-43 (IPv6)
        target_rows = set(list(range(1, 5)) + list(range(31, 34)) + list(range(41, 44)))

        for row_num, row in enumerate(tbody.find_all('tr'), start=1):
            if row_num in target_rows:
                cols = row.find_all('td')
                if len(cols) > 1:
                    ip_address = cols[1].text.strip()
                    line_type = cols[0].text.strip()
                    
                    if ip_address:
                        print(f"[提取成功] 行号 {row_num} | 线路: {line_type} -> IP: {ip_address}")
                        selected_ips.append(ip_address)
            
            if row_num > 43:
                break
                
        return selected_ips

    except Exception as e:
        print(f"Selenium 提取失败: {e}")
        return []
    finally:
        driver.quit()

def main():
    url = "https://api.uouin.com/cloudflare.html"
    ips = extract_cloudflare_specific_ips(url)

    if ips:
        print(f"\n成功提取到指定的 {len(ips)} 个 IP 数据：")
        for ip in ips:
            print(ip)

        # 【重点】这里直接保存到 cloudflare_specific_ips.txt，彻底抛弃旧名字！
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
