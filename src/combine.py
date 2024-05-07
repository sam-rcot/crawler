import pandas as pd


def main():
    # Read the CSV files
    df_combined = pd.read_csv('./data/aliases/combined.csv')
    #df_redirect = pd.read_csv('./data/redirects/duplicate_redirects_From_URL.csv')
    df_redirect = pd.read_csv('./data/redirects/redirects_headers.csv')

    # Merge the DataFrames based on 'To URL' and 'System'
    merged_df = pd.merge(df_redirect, df_combined, left_on='To URL', right_on='System', how='inner')

    # Create a new DataFrame with desired columns
    new_df = merged_df[['From URL', 'To URL', 'Alias']]

    # Write the new DataFrame to a CSV file
    new_df.to_csv('./data/merged_data_all.csv', index=False)


if __name__ == '__main__':
    main()
