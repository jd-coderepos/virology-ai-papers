import pandas as pd
from metapub import PubMedFetcher
import time
import os

# Prompt the user to enter the path to the CSV file
input_file = input("Enter the path to the CSV file: ")
output_file = input_file.replace(".csv", "_with_abstracts.csv")
log_file = input_file.replace(".csv", "_progress.log")

# Load the CSV file into a DataFrame
df = pd.read_csv(input_file)
df.columns = df.columns.str.strip()  # Ensure no extra whitespace in headers

# Initialize the PubMedFetcher
fetch = PubMedFetcher()

# Check the log file for the last processed PMID and set the start index accordingly
start_index = 0
if os.path.exists(log_file):
    with open(log_file, "r") as log:
        last_pmid = log.read().strip()
        if last_pmid:
            # Find the index of the last written PMID in the DataFrame
            try:
                start_index = df.index[df['PMID'] == int(last_pmid)][0] + 1
                print(f"Resuming from record after PMID {last_pmid} (index {start_index}).")
            except IndexError:
                print("Last PMID from log not found in the dataset. Starting from the beginning.")

# Define a function to fetch the abstract given a PMID
def fetch_abstract(pmid):
    try:
        article = fetch.article_by_pmid(str(pmid))
        return article.abstract if article else "Abstract not found"
    except Exception as e:
        print(f"Error fetching abstract for PMID {pmid}: {e}")
        return "Error fetching abstract"

# Process records in batches of 10
batch_size = 10
for i in range(start_index, len(df), batch_size):
    batch = df.iloc[i:i+batch_size].copy()  # Use .copy() to avoid SettingWithCopyWarning
    
    # Fetch abstracts for each PMID in the current batch and add them as a new column
    batch.loc[:, 'Abstract'] = batch['PMID'].apply(fetch_abstract)
    
    # Append the batch to the output file; create the file and write header only on the first batch
    header = not os.path.exists(output_file) if i == 0 else False
    batch.to_csv(output_file, mode='a', index=False, header=header)
    
    # Update the log file with the last PMID in this batch
    last_pmid = batch['PMID'].iloc[-1]
    with open(log_file, "w") as log:
        log.write(str(last_pmid))

    # Log progress to the console
    print(f"Processed and saved up to record {min(i+batch_size, len(df))} of {len(df)}.")

    # Pause to avoid exceeding 10 requests per second
    #time.sleep(0.1 * batch_size)  # 0.1 seconds per request, 10 requests per batch

print(f"Data with abstracts saved to {output_file}")
print(f"Progress logged in {log_file}")
