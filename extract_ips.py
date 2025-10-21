from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager # 导入 ChromeDriverManager
import pandas as pd
from datetime import datetime
import os

def extract_cloudflare_ips_selenium(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless") # 无头模式
    chrome_options.add_argument("--no-sandbox") # 在CI/CD环境中非常重要
    chrome_options.add_argument("--disable-dev-shm-usage") # 解决/dev/shm空间不足问题
    # 如果GitHub Actions的浏览器设置正确，下面的路径通常不需要手动指定
    # 但为了兼容性和鲁棒性，使用webdriver_manager是好习惯
    
    # 使用webdriver_manager自动管理ChromeDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get(url)

        # 显式等待表格内容加载
        # 等待 tbody 内部至少有一个 tr 元素出现
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
        # 遍历 tbody 中的所有行
        for i, row in enumerate(tbody.find_all('tr')):
            # 提取每一列的数据
            cols = row.find_all('td')
            # 确保有足够的列，根据你提供的HTML，数据列从<td>开始
            if len(cols) >= 8: # 线路, IP, 丢包, 延迟, 速度, 带宽, Colo, 时间
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
                # 如果是直接取页面前十行，且不按线路分类
                if len(ips_data) >= 10:
                    break
        
        # 如果需要按线路分类并取前十，使用下面的逻辑
        if not ips_data:
            return None
        
        df_all_ips = pd.DataFrame(ips_data)

        # 清理和转换“速度”列为数值，以便排序
        # 考虑到速度可能为 'N/A' 或其他非数字值，需要更健壮的转换
        df_all_ips['速度_数值'] = pd.to_numeric(
            df_all_ips['速度'].str.replace('mb/s', ''), 
            errors='coerce' # 无法转换的设置为 NaN
        )
        # 排序时，将 NaN 值放在最后
        
        top_ips_by_line = []
        for line_type in df_all_ips['线路'].unique():
            line_df = df_all_ips[df_all_ips['线路'] == line_type]
            # 按照速度（数值）降序排列，取前10，NaN 放在最后
            top_10_for_line = line_df.sort_values(by='速度_数值', ascending=False, na_position='last').head(10)
            top_ips_by_line.append(top_10_for_line)
        
        if top_ips_by_line:
            final_top_ips = pd.concat(top_ips_by_line)
            final_top_ips = final_top_ips.drop(columns=['速度_数值']).reset_index(drop=True)
            final_top_ips['总排序'] = final_top_ips.index + 1
            return final_top_ips.to_dict('records')
        else:
            return None # 没有提取到任何数据

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
        output_filename = os.path.join(output_dir, f"cloudflare_top_ips_by_line_{timestamp}.csv") # 修改文件名以反映按线路排序
        
        df.to_csv(output_filename, index=False, encoding='utf-8-sig')
        print(f"\n数据已保存到 {output_filename}")
    else:
        print("未能提取IP数据。")

if __name__ == "__main__":
    main_selenium()
