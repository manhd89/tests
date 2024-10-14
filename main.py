from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import logging

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
release_url = "https://github.com/ReVanced/revanced-patches/releases"
driver.get(release_url)

# Chờ trang tải hoàn toàn
time.sleep(5)  # Tăng thời gian chờ để đảm bảo trang tải

# Sử dụng WebDriverWait để tìm liên kết tài sản mới nhất (asset)
try:
    logging.info("Looking for the latest asset link...")

    # Xác định asset đầu tiên trong danh sách tải về (có thể điều chỉnh XPath nếu cần chọn asset cụ thể)
    asset_link = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.XPATH, "//div[@class='Box-body']//a[contains(@href, '/download/')]"))
    )

    # Lấy URL của asset
    asset_url = asset_link.get_attribute('href')
    logging.info(f"Asset found: {asset_url}")

    # Điều hướng đến URL của asset để bắt đầu tải xuống
    driver.get(asset_url)
    logging.info("Asset download initiated.")

    # Chờ cho trang tải và kiểm tra
    time.sleep(5)

except Exception as e:
    logging.error(f"An error occurred: {e}", exc_info=True)

finally:
    driver.quit()
    logging.info("Browser closed.")
