import argparse
import logging
import os
import re
import sys
from pathlib import Path
from bs4 import BeautifulSoup
from keyring.errors import KeyringLocked
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC, ui as ui
from webdriver_manager.chrome import ChromeDriverManager
import browsercookie

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Directory setup
new_directory_path = Path.cwd() / "data" / "tables"
new_directory_path.mkdir(parents=True, exist_ok=True)


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


def save_table_html(table, count):
    file_path = new_directory_path / f"table{count}.html"
    with open(file_path, "w") as file:
        file.write(str(table) if table else "No table found")


def get_table(driver, count):
    try:
        # Navigate to the page
        driver.get(f"https://www.rcot.co.uk/admin/config/search/path?page={count}")

        # Wait for the table to be loaded
        ui.WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "tableheader-processed"))
        )

        # Extract the table using BeautifulSoup
        soup = BeautifulSoup(driver.page_source, "html.parser")
        table = soup.find("table", class_="tableheader-processed")

        # Save the table to an HTML file
        file_path = new_directory_path / f"table{count}.html"
        with open(file_path, "w") as file:
            file.write(str(table) if table else "No table found")

    except Exception as e:
        logging.error(f"Failed to process page {count}: {str(e)}")


def setup_driver():
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    driver.maximize_window()
    return driver


def main():
    parser = argparse.ArgumentParser(description="Process cookies for site.")
    parser.add_argument(
        "-c", "--cookies", type=str, help="Cookies value to use in the request."
    )
    args = parser.parse_args()

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

    driver = setup_driver()
    driver.get("https://www.rcot.co.uk")
    driver.add_cookie(cookies)
    logging.info("Cookies provided, proceeding with the program.")

    try:
        for i in range(303):
            get_table(driver, i)
    except KeyboardInterrupt:
        logging.info("User interruption detected, closing the driver.")
    finally:
        driver.quit()
        logging.info("Driver closed.")


if __name__ == "__main__":
    main()
