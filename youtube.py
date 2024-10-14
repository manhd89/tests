from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import json
import logging
import os

# Setup logging
logging.basicConfig(level=logging.INFO)

# Create Chrome driver with headless options
def create_chrome_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument(
        f"user-agent=Mozilla/5.0 (Android 13; Mobile; rv:125.0) Gecko/125.0 Firefox/125.0"
    )

    driver = webdriver.Chrome(options=chrome_options)
    return driver

# Click on 'See more' button if necessary
def click_see_more(driver):
    try:
        see_more_button = driver.find_element(By.ID, "button-list-more")
        if see_more_button:
            see_more_button.click()
    except NoSuchElementException:
        pass

# Get download link for a specific version
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

def download_resource(url: str, filename: str) -> str:
    if not url:
        logging.error(f"Download URL is None. Cannot download {filename}.")
        return None

    filepath = os.path.join("./", filename)

    # Using Selenium to initiate download (you can improve this by using requests for direct file download)
    driver = create_chrome_driver()
    driver.get(url)

    # This assumes page source contains the file, but in most cases, you'd want to handle a direct download
    with open(filepath, "wb") as file:
        file.write(driver.page_source.encode('utf-8'))

    driver.quit()

    logging.info(f"Downloaded youtube to {filepath}")
    return filepath

# Main function to download app from Uptodown
def download_uptodown(app_name: str) -> str:
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
        
        return download_resource(download_link, filename)
