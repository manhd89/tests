from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import logging

# Cấu hình logging
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

# Cuộn trang xuống để đảm bảo các phần tử hiển thị
driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
time.sleep(3)

# Sử dụng WebDriverWait để tìm và nhấn vào phiên bản mới nhất hoặc prerelease
try:
    logging.info("Looking for the latest release or prerelease section...")

    # Tìm tất cả các phần tử có thể là phiên bản latest hoặc prerelease
    releases = WebDriverWait(driver, 15).until(
        EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@class, 'Box-body')]"))
    )

    latest_release = None
    prerelease = None

    for release in releases:
        if "Pre-release" in release.text:
            prerelease = release
            break
        elif "Latest" in release.text:
            latest_release = release
            break

    # Nhấn vào phiên bản mới nhất nếu có, hoặc prerelease nếu không có latest
    if latest_release:
        latest_release_link = latest_release.find_element(By.TAG_NAME, 'a')
        latest_release_link.click()
        logging.info("Clicked on the latest release.")
    elif prerelease:
        prerelease_link = prerelease.find_element(By.TAG_NAME, 'a')
        prerelease_link.click()
        logging.info("Clicked on the prerelease.")
    else:
        logging.error("No latest or prerelease found.")
        driver.quit()
        exit()

    # Tìm và click vào phần tử "Assets" để hiển thị các assets
    assets_button = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.XPATH, "//summary[contains(text(), 'Assets')]"))
    )
    assets_button.click()
    logging.info("Assets section expanded.")

    # Tìm tệp patches.json và revanced-patches-*.jar
    json_link = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.XPATH, "//a[contains(@href, 'patches.json')]"))
    )
    jar_link = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.XPATH, "//a[contains(@href, 'revanced-patches') and contains(@href, '.jar')]"))
    )

    # Lấy URL của hai tệp
    patches_json_url = json_link.get_attribute('href')
    revanced_patches_jar_url = jar_link.get_attribute('href')

    logging.info(f"Found patches.json: {patches_json_url}")
    logging.info(f"Found revanced-patches-*.jar: {revanced_patches_jar_url}")

    # Tải xuống các tệp bằng cách điều hướng đến các URL này
    driver.get(patches_json_url)
    logging.info("patches.json download initiated.")

    time.sleep(3)  # Đợi tệp được tải

    driver.get(revanced_patches_jar_url)
    logging.info("revanced-patches-*.jar download initiated.")

    time.sleep(3)  # Đợi tệp được tải

except Exception as e:
    logging.error(f"An error occurred: {e}", exc_info=True)

finally:
    driver.quit()
    logging.info("Browser closed.")
