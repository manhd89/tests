import logging
import requests
import version
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from youtube import download_uptodown

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

# Danh sách các repository
repositories = [
    "https://github.com/ReVanced/revanced-patches/releases/latest",
    "https://github.com/ReVanced/revanced-cli/releases/latest",
    "https://github.com/ReVanced/revanced-integrations/releases/latest"
]

# Khởi tạo trình điều khiển
service = Service(chrome_driver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

def download_assets_from_repo(release_url):
    driver.get(release_url)
    
    # Chờ trang tải hoàn toàn
    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "repo-content-pjax-container")))
    
    # Cuộn trang xuống để đảm bảo các phần tử hiển thị
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    
    try:
        logging.info("Looking for the Assets section...")
        
        # Tìm phần tử "Assets"
        assets_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.ID, "repo-content-pjax-container"))
        )
        assets_button.click()
        logging.info("Clicked on the Assets button.")
        
        # Tìm tất cả các asset
        asset_links = WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.XPATH, "//a[contains(@href, '/releases/download/')]"))
        )

        # Lọc và tải xuống các asset phù hợp
        for link in asset_links:
            asset_url = link.get_attribute('href')
            if not asset_url.endswith('.asc'):
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
        logging.error(f"An error occurred while downloading from {release_url}: {e}", exc_info=True)

# Lặp qua từng repository để tải xuống assets
for repo in repositories:
    download_assets_from_repo(repo)

# Đóng trình duyệt
driver.quit()
logging.info("Browser closed.")

import os
import subprocess
import logging

# Cấu hình logging để ghi thông tin ra console
logging.basicConfig(level=logging.INFO)

input_apk = download_uptodown

# Hàm để tìm các file theo tên trong thư mục hiện tại
def find_files(directory, file_prefix, file_suffix):
    files_found = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.startswith(file_prefix) and file.endswith(file_suffix):
                files_found.append(os.path.join(root, file))
    return files_found

# Hàm để chạy lệnh Java với các tham số -b và -m
def run_java_command(cli_jar, patches_jar, integrations_apk):
    command = [
        'java', '-jar', cli_jar, 'patch',
        '-b', patches_jar,         # Thêm flag -b cho revanced-patches
        '-m', integrations_apk,  # Thêm flag -m cho revanced-integrations
        input_apk,
        '-o', f'youtube-revanced-v{download_uptodown.version}.apk'
    ]
    try:
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info("Output: %s", result.stdout.decode())  # Sử dụng format string
    except subprocess.CalledProcessError as e:
        logging.error("Error: %s", e.stderr.decode())  # Sử dụng format string

# Thư mục chứa các file cần thiết
directory = '.'  # Thay đổi thành thư mục bạn muốn tìm kiếm

# Tìm file revanced-cli.jar
cli_jar_files = find_files(directory, 'revanced-cli', '.jar')
# Tìm file revanced-patches.jar
patches_jar_files = find_files(directory, 'revanced-patches', '.jar')
# Tìm file revanced-integrations.apk
integrations_apk_files = find_files(directory, 'revanced-integrations', '.apk')

# Kiểm tra và chạy lệnh nếu tất cả các file đều tồn tại
if cli_jar_files and patches_jar_files and integrations_apk_files:
    cli_jar = cli_jar_files[0]  # Chọn file đầu tiên được tìm thấy
    patches_jar = patches_jar_files[0]  # Chọn file đầu tiên được tìm thấy
    integrations_apk = integrations_apk_files[0]  # Chọn file đầu tiên được tìm thấy

    logging.info(f'Running {cli_jar} with patches and integrations...')
    run_java_command(cli_jar, patches_jar, integrations_apk)
else:
    logging.error("Không tìm thấy đủ file cần thiết (revanced-cli, revanced-patches, revanced-integrations).")
