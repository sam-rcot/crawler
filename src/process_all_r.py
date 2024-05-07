import logging
import os
import pandas as pd

# Setup logging configuration
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def load_csv(filepath, headers=None):
    """Load a CSV file, optionally assigning new headers."""
    if not os.path.exists(filepath):
        logging.error(f"File not found: {filepath}")
        return pd.DataFrame()
    df = pd.read_csv(filepath, header=None if headers else 0, names=headers)
    logging.info(f"Loaded CSV from {filepath} with columns: {df.columns.tolist()}")
    return df


def filter_redirects(df, from_prefixes, to_prefixes):
    """Filter rows where 'From URL' and 'To URL' start with specified prefixes."""
    from_condition = ~df["From URL"].str.startswith(tuple(from_prefixes)) & ~df["From URL"].str.contains(r'\?', regex=True)
    to_condition = ~df["To URL"].str.startswith(tuple(to_prefixes))
    return df[from_condition & to_condition]


def save_csv(df, filepath, mode='w', include_header=True):
    """Save a DataFrame to a CSV file, handling headers based on file existence and specified mode."""
    header = include_header if mode == 'w' else False  # Include headers only for 'write' mode if specified
    if mode == 'a' and not os.path.exists(filepath):
        header = True  # Ensure headers are included if appending to a non-existent file

    df.to_csv(filepath, index=False, mode=mode, header=header)
    logging.info(f"Data saved to {filepath} (mode={mode}, header={header})")



def sort_and_save(df, sort_by, filename):
    """Sort a DataFrame by specified columns and save to a CSV file."""
    sorted_df = df.sort_values(by=sort_by)
    save_csv(sorted_df, filename)


def find_and_save_duplicates(df, output_dir, keys):
    """Find duplicates based on specified keys and save them to CSV."""
    os.makedirs(output_dir, exist_ok=True)
    duplicates = pd.concat([df[df.duplicated(key, keep=False)] for key in keys]).drop_duplicates()
    for key in keys:
        sorted_duplicates = duplicates.sort_values(by=key)
        save_csv(sorted_duplicates, os.path.join(output_dir, f"duplicate_redirects_{key.replace(' ', '_')}.csv"))


def load_exclude_urls(filepath):
    """Load a set of 'From URL' values to exclude."""
    df = load_csv(filepath)
    return set(df["From URL"].dropna()) if not df.empty else set()


def apply_exclusions(df, exclude_set):
    """Exclude rows from the DataFrame based on the exclusion set."""
    filtered_df = df[~df["From URL"].isin(exclude_set)]
    logging.info(f"Excluded {len(df) - len(filtered_df)} rows from exclusion list.")
    return filtered_df


def main():
    # Define paths and headers
    data_dir = "data"
    main_csv_path = os.path.join(data_dir, "merged_data_all.csv")
    exclude_csv_path = os.path.join(data_dir, "exclude.csv")
    output_dir = os.path.join(data_dir, "duplicates")
    headers = ["From URL", "To URL", "Alias"]

    # Prefixes for filtering
    from_prefixes = [
        "files/", "events", "news", "occupational-therapy-jobs/", "sites/default/",
        "publication", "system/files/", "suppliers/", "practice-resources/",
        "about-us/specialistsections/", "consultation", "jobs"
    ]
    to_prefixes = ["<front>", "events", "news", "user", "jobs", "taxonomy"]

    # Load main data and exclusion list
    redirects_df = load_csv(main_csv_path, headers)
    exclude_set = load_exclude_urls(exclude_csv_path)

    # Apply filters and exclusions
    filtered_redirects = filter_redirects(redirects_df, from_prefixes, to_prefixes)
    save_csv(filtered_redirects, os.path.join(data_dir, "filtered.csv"))

    final_filtered_redirects = apply_exclusions(filtered_redirects, exclude_set)
    save_csv(final_filtered_redirects, os.path.join(data_dir, "filtered_exclusions_applied.csv"))

    # Sort, save, and identify duplicates
    sort_and_save(final_filtered_redirects, ["From URL", "To URL"], os.path.join(data_dir, "all_sorted.csv"))
    find_and_save_duplicates(final_filtered_redirects, output_dir, ["To URL", "From URL", "Alias"])


if __name__ == "__main__":
    main()
