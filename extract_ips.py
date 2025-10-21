from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import pandas as pd
from datetime import datetime
import os

def extract_cloudflare_ips_selenium(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless") # 无头模式
    chrome_options.add_argument("--no-sandbox") # 在CI/CD环境中可能需要
    chrome_options.add_argument("--disable-dev-shm-usage") # 解决/dev/shm空间不足问题
    
    # 如果ChromeDriver不在PATH中，需要指定路径
    # service = Service(executable_path='/usr/local/bin/chromedriver') # GitHub Actions runner上的路径
    driver = webdriver.Chrome(options=chrome_options) # service=service

    try:
        driver.get(url)

        # 显式等待表格内容加载
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'table.table-striped tbody tr'))
        )
        
        # 再次获取页面HTML，并用BeautifulSoup解析
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        table = soup.find('table', class_='table table-striped')
        if not table:
            print("未找到表格元素。")
            return None
        
        tbody = table.find('tbody')
        if not tbody:
            print("未找到表格的 tbody 元素。")
            return None

        ips_data = []
        for i, row in enumerate(tbody.find_all('tr')):
            cols = row.find_all('td')
            if len(cols) >= 8: # 确保有足够的列
                line = cols[0].text.strip()
                ip_address = cols[1].text.strip()
                packet_loss = cols[2].text.strip()
                latency = cols[3].text.strip()
                speed_mbps = cols[4].text.strip()
                bandwidth_mb = cols[5].text.strip()
                colo_link = cols[6].find('a')['href'] if cols[6].find('a') else ''
                update_time = cols[7].text.strip()

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
    except Exception as e:
        print(f"Selenium 提取失败: {e}")
        return None
    finally:
        driver.quit()

def main_selenium():
    url = "https://api.uouin.com/cloudflare.html"
    ips = extract_cloudflare_ips_selenium(url)

    if ips:
        df = pd.DataFrame(ips)
        print("成功提取到IP数据：")
        print(df)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_dir = 'data'
        os.makedirs(output_dir, exist_ok=True)
        output_filename = os.path.join(output_dir, f"cloudflare_top10_ips_selenium_{timestamp}.csv")
        
        df.to_csv(output_filename, index=False, encoding='utf-8-sig')
        print(f"\n数据已保存到 {output_filename}")
    else:
        print("未能提取IP数据。")

if __name__ == "__main__":
    main_selenium()
