import logging
import os
import json
import subprocess
import requests  # Importing requests here
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup  # Make sure to import BeautifulSoup as well

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# Path to ChromeDriver
chrome_driver_path = "/usr/bin/chromedriver"

# Create Chrome driver with headless options
def create_chrome_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Android 13; Mobile; rv:125.0) Gecko/125.0 Firefox/125.0")
    return webdriver.Chrome(service=Service(chrome_driver_path), options=options)

# Click on 'See more' button if necessary
def click_see_more(driver):
    try:
        driver.find_element(By.ID, "button-list-more").click()
    except NoSuchElementException:
        pass

# Get download link for a specific version from Uptodown
def get_download_link(version: str) -> str:
    driver = create_chrome_driver()
    driver.get("https://youtube.en.uptodown.com/android/versions")

    while True:
        soup = BeautifulSoup(driver.page_source, "html.parser")
        for div in soup.find_all("div", {"data-url": True}):
            if div.find("span", class_="version").text.strip() == version:
                driver.get(div["data-url"])
                download_button = BeautifulSoup(driver.page_source, "html.parser").find('button', {'id': 'detail-download-button'})
                if download_button and (data_url := download_button.get('data-url')):
                    driver.quit()
                    return f"https://dw.uptodown.com/dwn/{data_url}"

        click_see_more(driver)

    driver.quit()
    return None

# Download the APK or resource
def download_resource(url: str, filename: str) -> str:
    if not url:
        logging.error(f"Download URL is None. Cannot download {filename}.")
        return None

    filepath = os.path.join("./", filename)
    response = requests.get(url)  # Assuming requests is imported
    if response.status_code == 200:
        with open(filepath, 'wb') as apk_file:
            apk_file.write(response.content)
        logging.info(f"Downloaded {filename} successfully.")
        return filepath
    logging.error(f"Failed to download APK. Status code: {response.status_code}")
    return None

# Main function to download APK from Uptodown based on patches.json versions
# Main function to download APK from Uptodown based on patches.json versions
def download_uptodown():
    with open("./patches.json") as patches_file:
        patches = json.load(patches_file)

        versions = set()
        for patch in patches:
            # Ensure compatiblePackages is a list before iterating
            compatible_packages = patch.get("compatiblePackages", [])
            if isinstance(compatible_packages, list):
                for package in compatible_packages:
                    if (
                        package.get("name") == "com.google.android.youtube" and
                        package.get("versions") is not None and
                        isinstance(package["versions"], list) and
                        package["versions"]
                    ):
                        versions.update(map(str.strip, package["versions"]))
                        
        if versions:
            latest_version = sorted(versions, reverse=True)[0]
            download_link = get_download_link(latest_version)
            return download_resource(download_link, f"youtube-v{latest_version}.apk")

    logging.error("No compatible versions found in patches.json.")
    return None

# Function to run the Java command
def run_java_command(cli_jar, patches_jar, integrations_apk, input_apk, version):
    command = [
        'java', '-jar', cli_jar, 'patch',
        '-b', patches_jar,
        '-m', integrations_apk,
        input_apk,
        '-o', f'youtube-revanced-v{version}.apk'
    ]
    
    try:
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info("Output: %s", result.stdout.decode())
    except subprocess.CalledProcessError as e:
        logging.error("Error: %s", e.stderr.decode())

# Download ReVanced assets from GitHub
def download_assets_from_repo(release_url):
    driver = create_chrome_driver()
    driver.get(release_url)
    
    try:
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "repo-content-pjax-container")))
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        asset_links = WebDriverWait(driver, 15).until(EC.presence_of_all_elements_located((By.XPATH, "//a[contains(@href, '/releases/download/')]")))
        
        for link in asset_links:
            asset_url = link.get_attribute('href')
            if not asset_url.endswith('.asc'):
                response = requests.get(asset_url, allow_redirects=True)
                with open(asset_url.split('/')[-1], 'wb') as file:
                    file.write(response.content)
                logging.info(f"Downloaded {asset_url.split('/')[-1]} successfully.")
    except Exception as e:
        logging.error(f"Error while downloading from {release_url}: {e}")
    finally:
        driver.quit()

# List of repositories to download assets from
repositories = [
    "https://github.com/ReVanced/revanced-patches/releases/latest",
    "https://github.com/ReVanced/revanced-cli/releases/latest",
    "https://github.com/ReVanced/revanced-integrations/releases/latest"
]

# Download the assets
for repo in repositories:
    download_assets_from_repo(repo)

# Find necessary files
def find_files(directory, file_prefix, file_suffix):
    return [os.path.join(root, file) 
            for root, _, files in os.walk(directory) 
            for file in files if file.startswith(file_prefix) and file.endswith(file_suffix)]

# Check for necessary files and run the patch command
cli_jar_files = find_files('.', 'revanced-cli', '.jar')
patches_jar_files = find_files('.', 'revanced-patches', '.jar')
integrations_apk_files = find_files('.', 'revanced-integrations', '.apk')

if cli_jar_files and patches_jar_files and integrations_apk_files:
    cli_jar = cli_jar_files[0]
    patches_jar = patches_jar_files[0]
    integrations_apk = integrations_apk_files[0]
    input_apk = download_uptodown()

    if input_apk:
        version = input_apk.split('-v')[-1].split('.apk')[0]  # Extract version from APK filename
        logging.info(f"Running {cli_jar} with patches and integrations...")
        run_java_command(cli_jar, patches_jar, integrations_apk, input_apk, version)
else:
    logging.error("Required files not found (revanced-cli, revanced-patches, revanced-integrations).")
