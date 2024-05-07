import os
import re
import logging
import sys
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC, ui as ui
from webdriver_manager.chrome import ChromeDriverManager
import browsercookie
from keyring.errors import KeyringLocked
import argparse

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Set the base path to the project root (assuming the script is inside a 'src' directory in the project root)
# This goes up two levels from the current script location to the project root
base_path = Path(__file__).resolve().parent.parent

# Define the download directory using the base path
redirects_directory_path = base_path / "data" / "redirects"
redirects_directory_path.mkdir(parents=True, exist_ok=True)

redirects_csv_path = redirects_directory_path / 'redirects.csv'
if os.path.exists(redirects_csv_path):
    os.remove(redirects_csv_path)
    logging.info("Existing redirects.csv file deleted.")


# Retrieve cookies using browsercookie or manually
def get_cookies():
    try:
        chrome_cookies = browsercookie.chrome()
        cookie_attributes = ["name", "value", "domain", "path", "expires"]
        cookies_dict = {}

        for cookie in chrome_cookies:
            if re.search("SSESS7", cookie.name):
                cookie_details = {
                    attr: getattr(cookie, attr, None) for attr in cookie_attributes
                }
                cookies_dict[cookie.name] = cookie_details
                break

        for cookie_name, details in cookies_dict.items():
            return details
    except KeyringLocked:
        logging.error(
            "Keychain locked. Please provide cookies manually with -c option."
        )
        sys.exit(1)


# Configure WebDriver to download the file to the specified directory
def setup_driver(download_dir):
    options = webdriver.ChromeOptions()
    prefs = {
        "download.default_directory": str(download_dir),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    options.add_experimental_option("prefs", prefs)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.maximize_window()
    return driver


# Add cookies to the driver to bypass restricted access
def add_cookies_to_driver(driver, cookies):
    driver.get("https://www.rcot.co.uk")
    driver.add_cookie(cookies)
    logging.info("Cookies provided, proceeding with the program.")


# Download the redirects.csv file by submitting the form
def download_redirects(driver):
    try:
        driver.get("https://www.rcot.co.uk/admin/config/search/redirect/export")
        ui.WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "path-redirect-import-export-form"))
        )

        submit_button = driver.find_element(By.ID, "edit-submit")
        submit_button.click()

        logging.info("Export form submitted, downloading redirects.csv.")
    except Exception as e:
        logging.error(f"Failed to download redirects.csv: {str(e)}")


# Main function to initialize the driver and handle cookies
def main():
    parser = argparse.ArgumentParser(description="Process cookies for site.")
    parser.add_argument(
        "-c", "--cookies", type=str, help="Cookies value to use in the request."
    )
    args = parser.parse_args()

    # Get cookies manually or retrieve from the browser
    cookie_value = args.cookies or os.getenv("RCOT_COOKIE_VALUE")
    if not cookie_value:
        logging.info("No cookies found, trying to retrieve from browser...")
        cookies = get_cookies()
        if not cookies:
            logging.error("No cookies retrieved and no manual cookie provided.")
            sys.exit(1)
    else:
        cookies = {
            "name": "SSESS700bfdb6c4e8be7624120b9c476eb82b",
            "value": cookie_value,
            "domain": ".www.rcot.co.uk",
            "path": "/",
            "secure": True,
            "httpOnly": True,
            "sameSite": "Strict",
        }

    # Initialize the driver with a specified download directory
    driver = setup_driver(redirects_directory_path)
    add_cookies_to_driver(driver, cookies)

    try:
        download_redirects(driver)
        # Wait for the download to complete
        time.sleep(5)  # Adjust the timing as necessary for your download speed

        # Check for downloaded file and rename it
        latest_file = max(redirects_directory_path.glob('*'), key=os.path.getctime)
        if latest_file.name.startswith('.com.google.Chrome'):
            new_filename = redirects_directory_path / 'redirects.csv'
            latest_file.rename(new_filename)
            logging.info(f"File renamed to {new_filename}")
        else:
            logging.error(f"No expected file to rename was found. Latest file: {latest_file}")

    except KeyboardInterrupt:
        logging.info("User interruption detected, closing the driver.")
    finally:
        driver.quit()
        logging.info("Driver closed.")


if __name__ == "__main__":
    main()
