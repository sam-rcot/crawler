import os
import pandas as pd
import sys
import logging
from bs4 import BeautifulSoup

# Setup basic configuration for logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def process_html_table(file_path):
    """Process HTML tables to extract data."""
    try:
        with open(file_path, "r") as file:
            content = file.read()
        soup = BeautifulSoup(content, "html.parser")

        # Find the table
        table = soup.find("table", class_="tableheader-processed")
        if not table:
            logging.warning(f"No valid table found in {file_path}")
            return []

        rows = table.find_all("tr")
        data = [extract_data(row) for row in rows[1:] if len(row.find_all("td")) > 1]
        return data
    except Exception as e:
        logging.error(f"Error processing file {file_path}: {str(e)}")
        return []


def extract_data(row):
    """Extract data from a table row."""
    cols = row.find_all("td")
    return [cols[0].text.strip(), cols[1].text.strip()]


def load_or_create_csv(directory, combined_csv_path):
    """Load or create CSV file from HTML tables."""
    if os.path.exists(combined_csv_path):
        logging.info("Combined CSV already exists. Skipping HTML processing.")
        return pd.read_csv(combined_csv_path)

    all_data = []
    for filename in os.listdir(directory):
        if filename.endswith(".html"):
            file_path = os.path.join(directory, filename)
            all_data.extend(process_html_table(file_path))

    df = pd.DataFrame(all_data, columns=["Alias", "System"])
    df.to_csv(combined_csv_path, index=False)
    logging.info("Combined CSV created.")
    return df


def filter_data(df):
    """Filter out rows where 'System' and 'Alias' columns start with 'file/'."""
    return df[
        ~(df["System"].str.startswith("file/") & df["Alias"].str.startswith("files"))
    ]


def save_sorted_data(df, sort_by, filename):
    """Sort DataFrame and save to CSV."""
    df.sort_values(by=sort_by).to_csv(filename, index=False)


def find_and_save_duplicates(df):
    """Find duplicates in 'System' column and save them."""
    duplicate_systems = df["System"].value_counts()
    duplicates = df[df["System"].isin(duplicate_systems.index[duplicate_systems > 1])]
    duplicates.sort_values(by="System").to_csv(
        "data/aliases/duplicate_URL_aliases.csv", index=False
    )
    return duplicates


def main():
    directory = "data/aliases/tables"
    combined_csv_path = "data/aliases/combined.csv"
    df = load_or_create_csv(directory, combined_csv_path)
    filtered_df = filter_data(df)

    sort_types = ["Alias", "System"]
    for value in sort_types:
        save_sorted_data(
            filtered_df, value, f"data/aliases/URL_aliases_no_files_sortedby_{value}.csv"
        )

    duplicates = find_and_save_duplicates(df)
    duplicates_sorted = duplicates.sort_values(by="System")
    print(duplicates_sorted)
    #print(duplicates)


if __name__ == "__main__":
    main()
