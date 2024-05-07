import logging
import os

import pandas as pd

# Setup basic configuration for logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def load_csv_with_headers(csv_path, headers):
    """Load a CSV file that lacks headers and assign headers."""
    if not os.path.exists(csv_path):
        logging.error(f"CSV file not found at {csv_path}")
        return pd.DataFrame()  # Return empty DataFrame if file not found

    df = pd.read_csv(csv_path, header=None, names=headers)
    logging.info("CSV loaded with headers.")
    return df


def save_csv_with_headers(df, csv_path, sort_by=None):
    """Save DataFrame to CSV with headers."""
    if sort_by:
        df_sorted = df.sort_values(by=sort_by)
        df_sorted.to_csv(csv_path, index=False)
        logging.info(f"CSV saved with headers at {csv_path} sorted by {sort_by}")
    else:
        df.to_csv(csv_path, index=False)
        logging.info(f"CSV saved with headers at {csv_path}")


def filter_data(df):
    """Filter out rows where 'From URL' and 'To URL' start with any of the specified patterns."""
    # from_url_prefixes = [
    #     "file/", "sites/", "system/files/", "events", "news", "files/", "jobs", "user", "taxonomy",
    #     "occupational-therapy-jobs"
    # ]
    # to_url_prefixes = [
    #     "<front>", "events", "jobs", "user", "taxonomy", "news"
    # ]
    from_url_prefixes = [
        "files/", "events", "news", "occupational-therapy-jobs/", "sites/default/",
        "publication", "system/files/", "suppliers/", "practice-resources/", "about-us/specialistsections/",
        "about-us/specialist-sections/", "consultation"
    ]
    to_url_prefixes = [
        "<front>", "events", "news", "user", "jobs", "taxonomy"
    ]

    # Define conditions for filtering "From URL"
    from_conditions = (
            ~df["From URL"].str.startswith(tuple(from_url_prefixes)) &
            ~df["From URL"].str.contains(r'\?', regex=True)
    )

    # Define conditions for filtering "To URL"
    to_conditions = ~df["To URL"].str.startswith(tuple(to_url_prefixes))

    # Combine both conditions with logical AND
    conditions = from_conditions & to_conditions

    return df[conditions]


def sort_and_save(df, sort_by, filename):
    """Sort DataFrame and save to CSV."""
    sorted_df = df.sort_values(by=sort_by)
    sorted_df.to_csv(filename, index=False)
    logging.info(f"Data sorted by {sort_by} and saved to {filename}")


def find_and_save_duplicates(df):
    """Find duplicates based on 'From URL' or 'To URL' columns and save them."""
    # Concatenate duplicates from both columns
    from_duplicates = df[df.duplicated(subset="From URL", keep=False)]
    to_duplicates = df[df.duplicated(subset="To URL", keep=False)]
    sort_types = ["To URL", "From URL"]
    for sort_type in sort_types:
        combined_duplicates = pd.concat([from_duplicates, to_duplicates]).drop_duplicates().sort_values(
            by=sort_type)
        combined_duplicates.to_csv(f"data/redirects/duplicate_redirects_{sort_type.replace(' ', '_')}.csv", index=False)

    logging.info("Duplicates found and saved.")

    return combined_duplicates


def main():
    csv_path = "data/redirects/redirects.csv"
    headers = ["From URL", "To URL", "Redirect Status", "Redirect Language"]
    redirects_df = load_csv_with_headers(csv_path, headers)

    save_csv_with_headers(redirects_df, "data/redirects/redirects_headers.csv", sort_by="To URL")

    filtered_redirects = filter_data(redirects_df)

    sort_types = ["From URL", "To URL"]
    for sort_by in sort_types:
        sort_and_save(filtered_redirects, sort_by, f"data/redirects/redirects_sorted_by_{sort_by}.csv")

    find_and_save_duplicates(filtered_redirects)  # Use filtered_redirects here


if __name__ == "__main__":
    main()
