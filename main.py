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
release_url = "https://github.com/ReVanced/revanced-patches/releases/latest"
driver.get(release_url)

# Chờ trang tải hoàn toàn
time.sleep(5)  # Tăng thời gian chờ để đảm bảo trang tải

# Cuộn trang xuống để đảm bảo các phần tử hiển thị
driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
time.sleep(3)

# Sử dụng WebDriverWait để tìm và click vào phần tử "Assets" bằng ID để hiển thị danh sách các assets
try:
    logging.info("Looking for the Assets section...")

    # Tìm và click vào phần tử "Assets" bằng ID (nếu có)
    assets_button = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.ID, "repo-content-pjax-container"))
    )
    assets_button.click()
    logging.info("Clicked on the Assets button.")

    # Tìm tất cả các asset có định dạng tệp .jar hoặc các loại tệp bạn muốn
    asset_links = WebDriverWait(driver, 15).until(
        EC.presence_of_all_elements_located((By.XPATH, "//a[contains(@href, '/releases/download/') and contains(@href, '.jar')]"))
    )

    # Lấy URL của asset đầu tiên trong danh sách
    if asset_links:
        asset_url = asset_links[0].get_attribute('href')  # Lấy liên kết của asset đầu tiên
        logging.info(f"Asset found: {asset_url}")

        # Điều hướng đến URL của asset để bắt đầu tải xuống
        driver.get(asset_url)
        logging.info("Asset download initiated.")
    else:
        logging.error("No asset links found.")

    # Chờ cho trang tải và kiểm tra
    time.sleep(5)

except Exception as e:
    logging.error(f"An error occurred: {e}", exc_info=True)

finally:
    driver.quit()
    logging.info("Browser closed.")
