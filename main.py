import logging
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Cấu hình logging để ghi chi tiết hơn
logging.basicConfig(
    level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S'
)

# Đường dẫn đến ChromeDriver
chrome_driver_path = "/usr/bin/chromedriver"

# Cấu hình các tùy chọn của Chrome
chrome_options = Options()
chrome_options.add_argument("--headless")  # Chạy ở chế độ không giao diện
chrome_options.add_argument("--no-sandbox")  # Không dùng sandbox
chrome_options.add_argument("--disable-dev-shm-usage")  # Tắt shared memory

# Thêm User-Agent
chrome_options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.198 Safari/537.36"
)

# Khởi tạo trình điều khiển
service = Service(chrome_driver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

# Truy cập trang phát hành GitHub
release_url = "https://github.com/ReVanced/revanced-patches/releases/latest"
driver.get(release_url)

# Chờ trang tải hoàn toàn
WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "repo-content-pjax-container")))

# Cuộn trang xuống để đảm bảo các phần tử hiển thị
driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

# Sử dụng WebDriverWait để tìm và click vào phần tử "Assets" bằng ID để hiển thị danh sách các assets
try:
    logging.info("Looking for the Assets section...")

    # Tìm phần tử "Assets"
    assets_button = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.ID, "repo-content-pjax-container"))
    )
    assets_button.click()
    logging.info("Clicked on the Assets button.")

    # Tìm tất cả các asset có định dạng tệp .jar hoặc các loại tệp bạn muốn
    asset_links = WebDriverWait(driver, 15).until(
        EC.presence_of_all_elements_located((By.XPATH, "//a[contains(@href, '/releases/download/')]"))
    )

    # Lọc và tải xuống các asset phù hợp
    for link in asset_links:
        asset_url = link.get_attribute('href')
        if asset_url.endswith('.jar') or not asset_url.endswith('.asc') and 'source' not in asset_url.lower():
            # Kiểm tra mã phản hồi của asset
            response = requests.head(asset_url, allow_redirects=True)
            if response.status_code == 200:
                logging.info(f"Downloading asset: {asset_url}")
                # Tiến hành tải xuống tệp với việc theo dõi chuyển hướng
                download_response = requests.get(asset_url, allow_redirects=True)
                if download_response.status_code == 200:
                    filename = asset_url.split('/')[-1]
                    with open(filename, 'wb') as file:
                        file.write(download_response.content)
                    logging.info(f"Downloaded {filename} successfully.")
                else:
                    logging.error(f"Failed to download {asset_url}. Status code: {download_response.status_code}")
            else:
                logging.error(f"Asset URL is not reachable: {asset_url}. Status code: {response.status_code}")

except Exception as e:
    logging.error(f"An error occurred: {e}", exc_info=True)

finally:
    driver.quit()
    logging.info("Browser closed.")
