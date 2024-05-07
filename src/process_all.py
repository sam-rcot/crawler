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
    logging.info(f"Columns: {df.columns.tolist()}")  # Log DataFrame columns
    return df


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
        "about-us/specialist-sections/", "consultation", "jobs", "node"
    ]
    to_url_prefixes = [
        "<front>", "events", "news", "user", "jobs", "taxonomy"
    ]
    alias_prefixes = [
        "events/",
    ]
    # Define conditions for filtering "From URL"
    from_conditions = (
            ~df["From URL"].str.startswith(tuple(from_url_prefixes)) &
            ~df["From URL"].str.contains(r'\?', regex=True) &
            ~df["From URL"].str.contains(r'\@', regex=True)
            & ~df["From URL"].str.contains(r'-0', regex=True)
            & ~df["From URL"].str.contains(r'-(?!.)', regex=True)
            & ~df["From URL"].str.contains(r'\.', regex=True)
            & ~df["From URL"].str.contains(r'\;', regex=True)
            # & (df["From URL"].str.len() <= 15)
            & (
                    (df["From URL"].str.len() <= 20) |  # If URL length is <= 20
                    (
                            (df["From URL"].str.len() > 20) &  # If URL length is > 20
                            (df["From URL"].str.count('/') <= 2) &  # And contains <= 2 forward slashes
                            (df["From URL"].str.len() < 30)  # And is shorter than 30 characters
                    )
            )
    )

    # Define conditions for filtering "To URL"
    to_conditions = ~df["To URL"].str.startswith(tuple(to_url_prefixes))

    # Define conditions for filtering "Alias"
    alias_conditions = ~df["Alias"].str.startswith(tuple(alias_prefixes))

    # Combine both conditions with logical AND
    conditions = from_conditions & to_conditions & alias_conditions

    return df[conditions]


def sort_and_save(df, sort_by, filename):
    """Sort DataFrame and save to CSV."""
    sorted_df = df.sort_values(by=sort_by)
    # Check if the file already exists
    if not os.path.exists(filename):
        # If the file doesn't exist, save the DataFrame with headers
        sorted_df.to_csv(filename, index=False)
    else:
        # If the file exists, save the DataFrame without headers
        sorted_df.to_csv(filename, index=False, header=False, mode='a')
    logging.info(f"Data sorted by {sort_by} and saved to {filename}")


def find_and_save_duplicates(df):
    """Find duplicates based on 'From URL' or 'To URL' columns and save them."""
    # Concatenate duplicates from both columns
    from_duplicates = df[df.duplicated(subset="From URL", keep=False)]
    to_duplicates = df[df.duplicated(subset="To URL", keep=False)]
    sort_types = ["To URL", "From URL", "Alias"]
    for sort_type in sort_types:
        combined_duplicates = pd.concat([from_duplicates, to_duplicates]).drop_duplicates().sort_values(
            by=sort_type)
        combined_duplicates.to_csv(f"data/duplicate_redirects_{sort_type.replace(' ', '_')}.csv", index=False)

    logging.info("Duplicates found and saved.")

    return combined_duplicates


def load_exclude_urls(exclude_csv_path):
    """Load the list of URLs to exclude from the exclude.csv file."""
    if not os.path.exists(exclude_csv_path):
        logging.error(f"Exclude CSV file not found at {exclude_csv_path}")
        return set()  # Return an empty set if file not found

    exclude_df = pd.read_csv(exclude_csv_path)
    exclude_urls = set(exclude_df["From URL"].dropna().tolist())
    logging.info(f"Loaded {len(exclude_urls)} URLs to exclude.")
    return exclude_urls


def exclude_urls(df, exclude_urls):
    """Exclude rows from df where 'From URL' matches any URL in exclude_urls set."""
    excluded_df = df[~df["From URL"].isin(exclude_urls)]
    logging.info(f"Excluded {len(df) - len(excluded_df)} rows based on exclusion list.")
    return excluded_df


def main():
    csv_path = "data/merged_data_all.csv"
    exclude_csv_path = "data/exclude.csv"
    headers = ["From URL", "To URL", "Alias"]

    # Load the exclusion list
    exclude_urls_list = load_exclude_urls(exclude_csv_path)

    # Load the main CSV data
    redirects_df = load_csv_with_headers(csv_path, headers)

    # Apply the filtering logic
    filtered_redirects = filter_data(redirects_df)
    filtered_redirects.to_csv("data/filtered.csv", index=False, header=False)

    # Exclude rows based on exclusion list
    final_filtered_redirects = exclude_urls(filtered_redirects, exclude_urls_list)

    # Save the result with excluded URLs applied
    final_filtered_redirects.to_csv("data/filtered_exclusions_applied.csv", index=False, header=False)

    # Sort by both "From URL" and "To URL" and then save the sorted DataFrame
    sort_and_save(final_filtered_redirects, ["From URL", "To URL"], "data/all_sorted.csv")

    # Find and save duplicates using the final filtered DataFrame
    find_and_save_duplicates(final_filtered_redirects)


if __name__ == "__main__":
    main()
