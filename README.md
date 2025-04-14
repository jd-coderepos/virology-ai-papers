# 🧬 Virology and Epidemiology AI Research Collection

This repository contains the dataset [`collection_with_abstracts.csv`](https://github.com/jd-coderepos/virology-ai-papers/blob/main/collection_with_abstracts.csv), compiled via queries issued to the [PubMed](https://pubmed.ncbi.nlm.nih.gov/) database. PubMed is one of the largest databases indexing publications in the Life Sciences.

## 🔬 Dataset Scope

This dataset includes papers from PubMed that address problems in virology or epidemiology using deep learning neural network-based solutions. The dataset consists of 11,450 unique papers. For more detailed insights into the queries used to compile this collection, please view [this document](https://docs.google.com/document/d/1uMkXik3B3rNnKLbZc5AyqWruTGUKdpJcZFZZ4euM0Aw/edit?usp=sharing).

## 📑 Data Columns Description

Each row in the `collection_with_abstracts.csv` file corresponds to a unique academic paper, structured with the following columns:

- **PMID**: PubMed ID, a unique identifier for each publication.
- **Title**: Title of the publication.
- **Authors**: List of authors in the format `Last Name, First Initials`.
- **Citation**: Citation details, typically including volume, issue, and pages.
- **First Author**: The first listed author of the paper.
- **Journal/Book**: The name of the journal or book in which the paper is published.
- **Publication Year**: The year the paper was published.
- **Create Date**: The date the record was created in PubMed.
- **PMCID**: PubMed Central ID, linking to the full text of the article in the [PubMed Central](https://pmc.ncbi.nlm.nih.gov/) database. This field is optional and may not be present for all records.
- **NIHMS ID**: NIH Manuscript Submission ID, used when a paper is included in NIH public access policy compliance. This field is optional and may not be present for all records.
- **DOI**: Digital Object Identifier, providing a persistent link to its location on the internet. This field is optional and may not be present for all records.
- **Abstract**: The abstract of the publication. This field is optional and may not be present for all records.

### ❗ Note on Optional Fields

Fields marked as "optional" may not be present for all records within the dataset. This indicates that certain information is not available or applicable for those specific entries.

## 🌐 Accessing Full Texts

The PubMed Central (PMC) database, a subset of PubMed records, provides access to the full text of articles in XML format or other formats. Articles can be accessed via the API using the following URL: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id=[insert-pmcid-here]`, where `[insert-pmcid-here]` is to be replaced with the actual PMCID of the article.


## 📘 bioRxiv and medRxiv Preprint Mining

In addition to the PubMed dataset, this repository includes a robust R-based pipeline for retrieving and processing preprints from bioRxiv and medRxiv, two leading preprint servers for biology and health sciences.
This pipeline is powered by the medrxivr R package, which provides programmatic access to metadata from both servers.
The scripts for this pipeline are located in the folder:
📁 biorxiv_medrxiv_scraper/

## 💻 Prerequisites

Before running the scripts, make sure **R** and **RStudio** are installed on your system:

### 1️⃣ Install R:
- Visit: https://cran.r-project.org/
- Click on your operating system (Windows, macOS, or Linux) and follow the installation instructions.

### 2️⃣ Install RStudio:
- Visit: https://posit.co/download/rstudio-desktop/ 
- Download the free **RStudio Desktop** version for your platform.

## 🔧 R Package Dependencies

Install the required packages in RStudio by running:

```r
install.packages("medrxivr")
install.packages("dplyr")
install.packages("readxl")
install.packages("writexl")
```

Documentation for `medrxivr`:  
- 📘 GitHub: https://github.com/ropensci/medrxivr  
- 📘 Package Docs: https://docs.ropensci.org/medrxivr/

## ▶️ How to Run the Script

You can run `medrxiv_metadata_fetcher.R` using either **RStudio** or the **R terminal**.


### ✅ Steps:

1. **Open your project or folder in RStudio**  
   Make sure your R script (`medrxiv_metadata_fetcher.R`) is in the working directory (or note its full path).

2. **Go to the Terminal tab in RStudio**  
   - At the bottom pane of RStudio, click on the **“Terminal”** tab (next to “Console”).
   - If the terminal is not open, go to:  
     **Tools → Terminal → New Terminal**

3. **Run the script**  
   If your script is in the current directory:
   ```Rscript medrxiv_metadata_fetcher.R```

   If your script is elsewhere, provide the full path:
   ```Rscript "C:/Users/YourName/Desktop/project_folder/medrxiv_metadata_fetcher.R"```


## 📁 Script 1: `medrxiv_metadata_fetcher.R`

This script fetches and filters preprint metadata from **bioRxiv** or **medRxiv**, based on topic-specific keyword searches, and saves the results as Excel files.

### ✅ What the Script Does — Step by Step

1. **Fetch metadata from bioRxiv or medRxiv**  
   Metadata is downloaded using the `mx_api_content` function:
   ```r
   mx_api_content(from_date = "2015-01-01", to_date = "2025-04-13", server = "biorxiv")
   ```
   - To switch to **medRxiv**, change `server = "biorxiv"` to `server = "medrxiv"`.
   - You can also change the date range by modifying `from_date` and `to_date`.

2. **Save metadata locally as an `.rds` file**  
   The downloaded data is saved as `biorxiv_metadata_2015_2025.rds` so the script doesn’t need to re-download it every time:
   ```r
   saveRDS(data_biorxiv, "biorxiv_metadata_2015_2025.rds")
   ```

3. **Run keyword-based queries**  
   A list of topics is defined in `query_list`, where each topic maps to a list of related keywords.  
   Example:
   ```r
   "virology-llm.csv" = list(
     c("large language model", "LLM", "GPT", "BERT", "foundation model")
   )
   ```
   
   ⚠️ Important: If a keyword consists of multiple words, it must be enclosed in quotation marks to preserve the exact phrase during search.

4. **Filter results by scientific category**  
   After querying, results are filtered to include only papers in fields like:
   - *Epidemiology*
   - *Immunology*
   - *Bioinformatics*, etc.

   You can edit the `relevant_categories` vector in the script to change this.
   For a complete list of available subject categories, refer to the bioRxiv Subject Collections page: 
   https://www.biorxiv.org/collection

5. **Extract and organize metadata from search results**  
   For each query, the script pulls specific columns from the search results:
   - `title` → Title of the article  
   - `authors` → Author names  
   - `category` → Subject category (e.g., Immunology)  
   - `date` → Posting date  
   - `abstract`, `doi` → Abstract and persistent link  
   - The script also creates:
     - `Year of publication` (extracted from the date)
     - `Name of Publication/Journal` (based on category)

   The selected metadata is cleaned and reordered:
   ```r
   select(
     Authors, `Year of publication`, `Title of article`, `Name of Publication/Journal`,
     title, authors, category, date, abstract, doi
   )
   ```

6. **Export results to `.xlsx` files**  
   Each topic defined in `query_list` produces a separate Excel file.
   - The key `"virology-llm.csv"` results in an output named `virology-llm.xlsx`
   - The `.csv` in the key name is just a label and **does not refer to any CSV files**

   ✅ Example output files:
   - `virology-llm.xlsx`
   - `virology-transformer.xlsx`
   - `virology-deep-learning.xlsx`

## 📁 Script 2: `aggregate_and_deduplicate_doi.R`

This script combines all topic-wise `.xlsx` files generated by the previous script and removes duplicate entries based on DOI to produce a single, clean dataset.

### ✅ Step-by-Step Overview

1. **Set the folder path**  
   Define the path to the folder where all your `.xlsx` files are stored (e.g., `bio_lib`).  
   ```r
   folder_path <- "C:/Users/yourname/Desktop/bio_lib"
   ```
   > ⚠️ Make sure the folder path is correct, or the script won’t be able to find the files to process.

2. **Combines them** into one dataset and tags each entry with its source file.
3. **Detects and logs duplicate DOIs** into:
   ```
   duplicates_by_doi.xlsx
   ```
4. **Removes duplicates** and saves the cleaned metadata to:
   ```
   aggregated_deduplicated.xlsx
   ```
