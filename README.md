# 🦚 Virology-AI Papers: A Pipeline for Mining Deep Learning Research in Virology and Epidemiology

This repository provides a structured, four-step pipeline to **collect**, **filter**, **process**, and **annotate** scientific literature that applies deep learning and large language models (LLMs) to problems in virology and epidemiology. It integrates data from trusted sources like **PubMed**, **bioRxiv**, and **medRxiv**, with a strong focus on:

* Collecting metadata from scientific databases
* Semantic filtering of results to ensure relevance
* Extracting structured information using LLMs
* Human validation and correction of the extracted data

This pipeline enables high-quality datasets that support downstream tasks such as biomedical NLP research, systematic review automation, and AI benchmarking.

---

## 📂 Repository Structure

The project is organized into the following modular steps:

### 📁 Folder Overview

Each stage of the pipeline is organized into a dedicated folder:

| Folder Name                     | Description                                                                                  |
| ------------------------------- | -------------------------------------------------------------------------------------------- |
| `step_01_metadata_collection/`  | Scripts and outputs related to collecting metadata from PubMed, bioRxiv, and medRxiv.        |
| `step_02_semantic_filtering/`   | Python scripts to semantically filter abstracts using sentence embeddings.                   |
| `step_03_text_extraction_llm/`  | Code to extract and structure full-text data from PDFs or XMLs using OCR or parsing + LLaMA. |
| `step_04_human_annotated_data/` | Ground-truth corrections and final structured data annotated by humans.                      |

---

### 🔹 Step 01 — Metadata Collection

**Folder:** `step_01_metadata_collection/`

This step retrieves metadata and abstracts from **PubMed**, **bioRxiv**, and **medRxiv** using different tools:

* **PubMed**: Data is collected manually using the **PubMed web interface**.
* **bioRxiv and medRxiv**: Metadata is retrieved using the R package [`medrxivr`](https://github.com/ropensci/medrxivr).

All three sources use **the same keyword queries and topic filters** to ensure consistent data collection across repositories.

📘 Metadata Details

PubMed Metadata Fields:

PMID: PubMed ID, a unique identifier for each publication

Title: Title of the publication

Authors: List of authors in the format Last Name, First Initials

Citation: Citation details, including volume, issue, and pages

First Author: The first listed author

Journal/Book: Name of the journal/book

Publication Year: Year of publication

Create Date: Date created in PubMed

PMCID: PubMed Central ID

NIHMS ID: NIH Manuscript Submission ID

DOI: Digital Object Identifier

Abstract: Abstract text

bioRxiv / medRxiv Metadata Fields:

Authors: List of authors

Year of publication: Year when the article was posted

Title of article: Title of the article

category: Scientific category (e.g., Immunology, Epidemiology)

date: Posting date on the preprint server

Abstract: Article abstract

doi: Digital Object Identifier for the article

#### 📘 PubMed Metadata Collection

Metadata from **PubMed** is collected via manual queries using the official PubMed web interface.

* A full record of query construction and methodology is documented here: [Query Design Document](https://docs.google.com/document/d/1yesEbGY5eTAjBcC1-5acyT-5PVfLWwlI9ddLQpGUdnE/edit#heading=h.xxnjc2xkhm8n)

#### 📋 Prerequisites for bioRxiv and medRxiv Scripts

Before running the scripts, make sure R and RStudio are installed:

1. **Install R**: [https://cran.r-project.org/](https://cran.r-project.org/)
2. **Install RStudio**: [https://posit.co/download/rstudio-desktop/](https://posit.co/download/rstudio-desktop/)

**Install required R packages:**

```r
install.packages("medrxivr")
install.packages("dplyr")
install.packages("readxl")
install.packages("writexl")
```

#### ▶️ Script 1: `medrxiv_metadata_fetcher.R`

This script fetches metadata from **bioRxiv** or **medRxiv** using keyword lists and filters results by relevant scientific categories.

**How to run:**

```bash
Rscript medrxiv_metadata_fetcher.R
```

Or provide full path:

```bash
Rscript "C:/Users/YourName/Desktop/project_folder/medrxiv_metadata_fetcher.R"
```

**What it does:**

* Downloads metadata using `mx_api_content()` with user-defined date ranges and source
* Saves raw data as `.rds` files
* Executes topic-specific keyword searches via `query_list`
* Filters by categories (e.g., Epidemiology, Immunology, Bioinformatics)
* Extracts fields like title, authors, category, date, abstract, DOI
* Adds derived fields like publication year and publication name
* Outputs `.xlsx` files for each topic

**Example output files:**

* `virology-llm.xlsx`
* `virology-transformer.xlsx`
* `virology-deep-learning.xlsx`

#### ▶️ Script 2: `aggregate_and_deduplicate_doi.R`

This script consolidates topic-specific outputs and eliminates duplicates.

**How to run:**

```r
folder_path <- "C:/Users/yourname/Desktop/bio_lib"
```

* Combines `.xlsx` files into one dataset
* Identifies and logs duplicate DOIs to `duplicates_by_doi.xlsx`
* Outputs cleaned dataset to `aggregated_deduplicated.xlsx`

**Final Output:**

* A single, deduplicated file containing metadata from all topic areas

---

### 🔹 Step 02 — Semantic Filtering

**Folder:** `step_02_semantic_filtering/`

This step applies embedding-based semantic filtering to refine the initial search results. It uses pretrained sentence transformers to evaluate the relevance of abstracts to the target domain.

**Goals:**

* Remove papers with irrelevant or ambiguous keyword matches
* Prioritize highly relevant documents for LLM processing

**Typical script(s):**

* `semantic_filtering.py`

**Dependencies:**

* Python ≥ 3.7
* `sentence-transformers`
* `pandas`
* `numpy`
* `scikit-learn`

**Installation:**

```bash
pip install sentence-transformers pandas numpy scikit-learn
```

**Suggested model:**

* `all-MiniLM-L6-v2` from `sentence-transformers`

**How to run:**

```bash
python semantic_filtering.py
```

---

### 🔹 Step 03 — Text Extraction with LLM

**Folder:** `step_03_text_extraction_llm/`

This step uses a local large language model (LLaMA 3.2B via Ollama) to extract structured fields from full paper texts. The input can be either **PDF** (processed via OCR) or **XML** (parsed as plain text).

**Goals:**

* Process full text from PDFs or XMLs
* Strip reference sections
* Run LLM extraction of predefined fields from full text

**Dependencies:**

* Python ≥ 3.8
* `pdf2image`
* `pytesseract`
* `ollama`
* `pandas`
* `re`, `json`, `logging`, `pathlib`

**Installation:**

```bash
pip install pdf2image pytesseract ollama pandas
```

**System Requirements:**

* [Poppler](https://github.com/oschwartz10612/poppler-windows) installed and added to PATH
* [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) installed and accessible
* Ollama installed and running LLaMA 3.2B locally

**How to run:**

```bash
python Textextraction_performancemetrics_medrxiv.py
python Textextraction_additionalfields_medrxiv.py
```

**Output:**

* `Extracted_LLaMA_Output.csv`: Structured file with extracted fields from papers

---

### 🔹 Step 04 — Human Annotation

**Folder:** `step_04_human_annotated_data/`

This step includes manually reviewed or corrected outputs from the LLM extraction phase. It covers detailed validation and correction of the following structured fields:

1. `research_aim`: The primary goal or aim of the research
2. `research_problem`: The specific research problem addressed
3. `ai_objective`: What AI is being used for in the research
4. `ai_methodology`: A brief description of the AI-based approach used
5. `ai_method_details`: Details on techniques, architectures, or models
6. `ai_method_type`: The AI method(s) used (as a list if multiple)
7. `type_of_underlying_data`: The raw input data used for experiments
8. `dataset_name`: Name(s) of the dataset(s) used
9. `disease_name`: Viral or infectious disease studied (list if multiple)
10. `virology_subdomain`: Subfield of virology addressed
11. `was_performance_measured`: Boolean flag
12. `performance_results`: Summary of the results
13. `performance_measurement_details`: Description of how performance was evaluated

**Key contents:**

* `Extracted_LLaMA_Output_biorxiv_groundtruth_tobecompleted.csv`

**Purpose:**

* Serve as ground truth for evaluation
* Enable supervised fine-tuning or training of models

---

## 🚀 Getting Started

1. Clone the repository:

```bash
git clone https://github.com/jd-coderepos/virology-ai-papers.git
cd virology-ai-papers
```

2. Follow the instructions in each step's folder.

3. Install required R and Python packages as outlined above.

---

## 🎓 Use Cases

* Literature mining in virology and public health
* Evaluation of LLM capabilities in scientific information extraction
* Systematic review automation in life sciences

---

## 🌐 Citation

If you use this dataset or codebase, please consider citing or referencing this repository in your work.


