import logging
import requests
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup
import os
import json

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# Path to ChromeDriver
chrome_driver_path = "/usr/bin/chromedriver"

# Create Chrome driver with headless options
def create_chrome_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(
        f"user-agent=Mozilla/5.0 (Android 13; Mobile; rv:125.0) Gecko/125.0 Firefox/125.0"
    )
    service = Service(chrome_driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

# Click on 'See more' button if necessary
def click_see_more(driver):
    try:
        see_more_button = driver.find_element(By.ID, "button-list-more")
        if see_more_button:
            see_more_button.click()
    except NoSuchElementException:
        pass

# Get download link for a specific version from Uptodown
def get_download_link(version: str) -> str:
    url = "https://youtube.en.uptodown.com/android/versions"
    driver = create_chrome_driver()
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, "html.parser")

    while True:
        divs = soup.find_all("div", {"data-url": True})
        for div in divs:
            version_span = div.find("span", class_="version")
            if version_span and version_span.text.strip() == version:
                dl_url = div["data-url"]
                driver.get(dl_url)

                # Parse the download page for the actual download link
                soup = BeautifulSoup(driver.page_source, "html.parser")
                download_button = soup.find('button', {'id': 'detail-download-button'})
                if download_button and download_button.get('data-url'):
                    data_url = download_button.get('data-url')
                    full_url = f"https://dw.uptodown.com/dwn/{data_url}"
                    driver.quit()
                    return full_url

        # If the "See more" button is available, click to load more versions
        click_see_more(driver)
        soup = BeautifulSoup(driver.page_source, "html.parser")

    driver.quit()
    return None

# Download the APK or resource
def download_resource(url: str, filename: str) -> str:
    if not url:
        logging.error(f"Download URL is None. Cannot download {filename}.")
        return None

    filepath = os.path.join("./", filename)
    
    # Add User-Agent header
    headers = {
        'User-Agent': 'Mozilla/5.0 (Android 13; Mobile; rv:125.0) Gecko/125.0 Firefox/125.0'
    }
    
    response = requests.get(url, headers=headers)  # Pass headers with request
    if response.status_code == 200:
        with open(filepath, 'wb') as apk_file:
            apk_file.write(response.content)
        logging.info(f"Downloaded {filename} successfully.")
        return filepath
    else:
        logging.error(f"Failed to download APK. Status code: {response.status_code}")
        return None

# Function to run the Java command
def run_java_command(cli_jar, patches_jar, integrations_apk, input_apk, version):
    output_apk = f'youtube-revanced-v{version}.apk'
    
    command = [
        'java', '-jar', cli_jar, 'patch',
        '-b', patches_jar,      # ReVanced patches
        '-m', integrations_apk, # ReVanced integrations APK
        input_apk,              # Original YouTube APK
        '-o', output_apk        # Output APK
    ]
    
    try:
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info("Output: %s", result.stdout.decode())
    except subprocess.CalledProcessError as e:
        logging.error("Error: %s", e.stderr.decode())

# Main function to download APK from Uptodown based on patches.json versions
def download_uptodown():
    with open("./patches.json", "r") as patches_file:
        patches = json.load(patches_file)

        versions = set()
        for patch in patches:
            compatible_packages = patch.get("compatiblePackages")
            if compatible_packages and isinstance(compatible_packages, list):
                for package in compatible_packages:
                    if (
                        package.get("name") == "com.google.android.youtube" and
                        package.get("versions") is not None and
                        isinstance(package["versions"], list) and
                        package["versions"]
                    ):
                        versions.update(
                            map(str.strip, package["versions"])
                        )
                        
        version = sorted(versions, reverse=True)[0]  # Use the latest version
        download_link = get_download_link(version)
        filename = f"youtube-v{version}.apk"
        
        file_path = download_resource(download_link, filename)
        return file_path, version  # Return both the file path and version

# Download ReVanced assets from GitHub and return the paths of the downloaded files
def download_assets_from_repo(release_url):
    driver = create_chrome_driver()
    driver.get(release_url)
    
    downloaded_files = []
    
    try:
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "repo-content-pjax-container")))
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        asset_links = WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.XPATH, "//a[contains(@href, '/releases/download/')]"))
        )

        for link in asset_links:
            asset_url = link.get_attribute('href')
            if not asset_url.endswith('.asc'):  # Skip signature files
                response = requests.head(asset_url, allow_redirects=True)
                if response.status_code == 200:
                    download_response = requests.get(asset_url, allow_redirects=True)
                    filename = asset_url.split('/')[-1]
                    with open(filename, 'wb') as file:
                        file.write(download_response.content)
                    logging.info(f"Downloaded {filename} successfully.")
                    downloaded_files.append(filename)  # Store downloaded filename
    except Exception as e:
        logging.error(f"Error while downloading from {release_url}: {e}")
    finally:
        driver.quit()
    
    return downloaded_files  # Return the list of downloaded files

# List of repositories to download assets from
repositories = [
    "https://github.com/ReVanced/revanced-patches/releases/latest",
    "https://github.com/ReVanced/revanced-cli/releases/latest",
    "https://github.com/ReVanced/revanced-integrations/releases/latest"
]

# Download the assets
all_downloaded_files = []
for repo in repositories:
    downloaded_files = download_assets_from_repo(repo)
    all_downloaded_files.extend(downloaded_files)  # Combine all downloaded files

# After downloading, find the necessary files
cli_jar_files = [f for f in all_downloaded_files if 'revanced-cli' in f and f.endswith('.jar')]
patches_jar_files = [f for f in all_downloaded_files if 'revanced-patches' in f and f.endswith('.jar')]
integrations_apk_files = [f for f in all_downloaded_files if 'revanced-integrations' in f and f.endswith('.apk')]

# Check if all necessary files are found and proceed to patch the APK
if cli_jar_files and patches_jar_files and integrations_apk_files:
    cli_jar = cli_jar_files[0]  # First found file
    patches_jar = patches_jar_files[0]  # First found file
    integrations_apk = integrations_apk_files[0]  # First found file

    input_apk, version = download_uptodown()  # Download APK from Uptodown and get the version
    if input_apk:
        logging.info(f"Running {cli_jar} with patches and integrations...")
        run_java_command(cli_jar, patches_jar, integrations_apk, input_apk, version)
else:
    logging.error("Required files not found (revanced-cli, revanced-patches, revanced-integrations).")
