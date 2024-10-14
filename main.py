from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

# Đường dẫn đến ChromeDriver (được cài đặt trên môi trường Ubuntu của GitHub Actions)
chrome_driver_path = "/usr/bin/chromedriver"

# Thiết lập các tùy chọn của Chrome
chrome_options = Options()
chrome_options.add_argument("--headless")  # Chế độ không hiển thị
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Tạo dịch vụ ChromeDriver
service = Service(chrome_driver_path)

# Cấu hình thư mục tải xuống
prefs = {"download.default_directory": "/tmp/downloads"}  # Đặt đường dẫn tải xuống
chrome_options.add_experimental_option("prefs", prefs)

# Khởi động trình duyệt với các tùy chọn
driver = webdriver.Chrome(service=service, options=chrome_options)

# Truy cập trang phát hành GitHub
release_url = "https://github.com/revanced/revanced-patches/releases"
driver.get(release_url)

# Chờ trang tải (tùy chỉnh thời gian nếu cần)
time.sleep(3)

# Tìm và nhấn nút tải tệp (thay đổi XPATH nếu cần)
download_button = driver.find_element(By.XPATH, "//a[contains(@href, 'releases/download')]")
download_button.click()

# Chờ tệp tải về
time.sleep(10)

# Đóng trình duyệt
driver.quit()

# Kiểm tra tệp đã tải về
import os
if os.path.exists("/tmp/downloads/filename"):
    print("File downloaded successfully.")
else:
    print("Failed to download file.")
