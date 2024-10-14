from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import logging

logging.basicConfig(
    level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S'
)

# Đường dẫn đến ChromeDriver
chrome_driver_path = "/usr/bin/chromedriver"

# Cấu hình các tùy chọn của Chrome
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Khởi tạo trình điều khiển
service = Service(chrome_driver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

# Truy cập trang phát hành GitHub
release_url = "https://github.com/ReVanced/revanced-patches/releases"
driver.get(release_url)

# Chờ trang tải hoàn toàn
time.sleep(3)

# Sử dụng WebDriverWait để tìm liên kết phiên bản mới nhất
try:
    download_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//span[contains(@class, 'Label--success')]/../preceding-sibling::span/a"))
    )
    download_button.click()
    logging.info("Navigated to the latest release successfully.")

    # Chờ cho trang tải và kiểm tra
    time.sleep(5)

except Exception as e:
    logging.error(f"An error occurred: {e}")

finally:
    driver.quit()
