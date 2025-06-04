import os
import pandas as pd

# Prompt the user for the directory containing CSV files
input_directory = input("Enter the path to the directory containing CSV files: ")

# Define the output file name in the same directory
output_file = os.path.join(input_directory, "aggregated_deduplicated_collection.csv")

# Initialize an empty dictionary to hold unique records by PMID
unique_records = {}

# Traverse the directory and process each CSV file
for filename in os.listdir(input_directory):
    if filename.endswith(".csv"):
        file_path = os.path.join(input_directory, filename)
        
        # Load the CSV file into a DataFrame
        df = pd.read_csv(file_path)
        
        # Process each row and add it to the unique_records dictionary by PMID
        for index, row in df.iterrows():
            pmid = row['PMID']
            if pmid not in unique_records:
                unique_records[pmid] = row
            else:
                # Optionally, add any custom logic here to handle duplicates if needed
                pass

# Convert the dictionary of unique records back to a DataFrame
aggregated_df = pd.DataFrame.from_dict(unique_records, orient="index")

# Save the aggregated, deduplicated DataFrame to a new CSV file in the same directory
aggregated_df.to_csv(output_file, index=False)

print(f"Aggregated and deduplicated data saved to {output_file}")
