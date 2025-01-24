import requests
import pandas as pd
import os
import time

#Prompt for input file
input_file = input("Enter the path to the CSV file: ")
output_csv = input_file.replace(".csv", "_complete_fulltext.csv")

# Create output folder for storing full-text
input_directory = os.path.dirname(input_file)
output_folder = os.path.join(input_directory, "xml_outputs")
os.makedirs(output_folder, exist_ok=True)

def convert_doi_to_pmcid(doi):
    """
    Convert a DOI to a PMCID using the NCBI ID Converter API.

    Args:
        doi (str): The DOI to be converted.

    Returns:
        str: The corresponding PMCID if found, or None if not found.
    """
    base_url = "https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/"
    params = {"ids": doi, "format": "json"}

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()

        records = data.get("records", [])
        for record in records:
            if record.get("doi", "").lower() == doi.lower():
                return record.get("pmcid", None)
        return None

    except requests.exceptions.RequestException as e:
        print(f"Error communicating with the ID converter API for DOI '{doi}': {e}")
        return None

def fetch_pmcid_xmls(df, pmcid_column, max_retry=5, timeout=10):
    """
    Fetch and store full-text articles in XML format using PMCIDs.

    Args:
        df (pd.DataFrame): The dataframe containing the PMCIDs.
        pmcid_column (str): The column name containing PMCIDs.
        max_retry (int): Maximum retries for each request.
        timeout (int): Timeout for each request in seconds.

    Returns:
        pd.DataFrame: Dataframe filtered to include only rows with successfully fetched PMCIDs.
    """
    successful_pmcids = []

    for pmcid in df[pmcid_column]:
        retry = 0
        while retry < max_retry:
            try:
                url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id={pmcid}"
                response = requests.get(url, timeout=timeout)

                if response.status_code == 200:
                    output_path = os.path.join(output_folder, f"{pmcid}.xml")
                    with open(output_path, "wb") as file:
                        file.write(response.content)
                    print(f"Successfully saved {pmcid}.xml")
                    successful_pmcids.append(pmcid)
                    break
                else:
                    print(f"Failed to fetch PMCID {pmcid}: HTTP {response.status_code}")
                    retry += 1
                    time.sleep(2)
            except requests.exceptions.RequestException as e:
                print(f"Error fetching PMCID {pmcid}: {e}")
                retry += 1
                time.sleep(2)
        else:
            print(f"Failed to fetch PMCID {pmcid} after {max_retry} retries.")

    print(f"Successfully fetched {len(successful_pmcids)} XML files.")
    return df[df[pmcid_column].isin(successful_pmcids)]

def preprocess_data(input_csv, doi_column, pmcid_column):
    """
    Preprocess raw dataset by:
      1. Dropping rows with missing DOIs.
      2. Fetching PMCIDs for valid DOIs.
      3. Dropping rows with missing PMCIDs.
      4. Fetching full-text articles in XML format for valid PMCIDs.

    Args:
        input_csv (str): Path to the raw dataset file.
        doi_column (str): Column name containing DOIs.
        pmcid_column (str): Column name for PMCIDs.
    """
    try:
        df = pd.read_csv(input_csv)
        df.columns = df.columns.str.strip()

        # Step 1: Drop rows with missing or empty DOIs
        initial_count = len(df)
        df = df[df[doi_column].notna() & (df[doi_column].str.strip() != "")]
        print(f"Dropped {initial_count - len(df)} rows with missing or empty '{doi_column}'.")

        # Step 2: Populate PMCIDs for rows with valid DOIs
        for index, row in df.iterrows():
            if pd.isna(row[pmcid_column]) or row[pmcid_column].strip() == "":
                pmcid = convert_doi_to_pmcid(row[doi_column])
                df.at[index, pmcid_column] = pmcid

        # Step 3: Drop rows with missing or empty PMCIDs
        initial_count = len(df)
        df = df[df[pmcid_column].notna() & (df[pmcid_column].str.strip() != "")&
                (df['Abstract'] != "") & df['Abstract'].notna()]]
        print(f"Dropped {initial_count - len(df)} rows with missing or empty '{pmcid_column}'.")

        # Step 4: Fetch XML files for PMCIDs
        df_successful = fetch_pmcid_xmls(df, pmcid_column)

        # Save the filtered dataframe
        df_successful.to_csv(output_csv, index=False)
        print(f"Processed data saved to {output_csv}")

    except Exception as e:
        print(f"An error occurred during processing: {e}")

# Run the preprocessing workflow
preprocess_data(input_file, 'DOI', 'PMCID')
