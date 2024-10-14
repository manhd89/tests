from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

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
release_url = "https://github.com/revanced/revanced-patches/releases"
driver.get(release_url)

# Chờ trang tải hoàn toàn (có thể chỉnh sửa thời gian)
time.sleep(3)

# Sử dụng WebDriverWait để chờ phần tử xuất hiện
try:
    download_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//a[contains(@href, 'releases/download')]"))
    )
    download_button.click()
    print("Download button clicked successfully.")

    # Chờ tệp tải về (tùy thuộc vào kích thước tệp)
    time.sleep(10)

except Exception as e:
    print(f"An error occurred: {e}")

finally:
    driver.quit()
