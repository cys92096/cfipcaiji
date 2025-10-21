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
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    top_ips = []
    try:
        driver.get(url)

        # ====== 改进的等待逻辑开始 ======
        
        # 1. 等待“加载中”提示消失
        # 查找加载提示元素
        loading_element_selector = 'fieldset.layui-elem-field b'
        try:
            WebDriverWait(driver, 10).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, loading_element_selector))
            )
            print("加载提示已消失。")
        except Exception as e:
            print(f"警告: 加载提示未在预期时间内消失或未找到: {e}. 继续尝试抓取...")
            # 如果加载提示没有出现或没有消失，也可能是页面直接加载了最终数据

        # 2. 确保表格的 tbody 元素存在且包含数据（例如，等待第一行的第二个td元素出现，即IP地址）
        # 这比仅仅等待任何tr更具体，因为旧的tr可能立即满足。
        # 我们等待一个有内容的IP地址元素出现。
        ip_element_selector = 'table.table-striped tbody tr:nth-child(1) td:nth-child(2)'
        try:
            WebDriverWait(driver, 20).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, ip_element_selector))
            )
            # 也可以尝试等待元素文本非空，但visibility通常足够
            print("表格数据（第一个IP）已加载可见。")
        except Exception as e:
            print(f"错误: 等待表格数据加载超时: {e}. 无法获取实时数据。")
            return [] # 如果关键数据没有加载，直接返回空列表
            
        # ====== 改进的等待逻辑结束 ======
        
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

        for i, row in enumerate(tbody.find_all('tr')):
            cols = row.find_all('td')
            if len(cols) > 1:
                ip_address = cols[1].text.strip()
                if ip_address and ip_address != 'Loading...': # 再次确保IP地址有效，不是加载占位符
                    top_ips.append(ip_address)
                    if len(top_ips) >= 10:
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
