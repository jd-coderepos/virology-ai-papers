# Load required libraries (install if missing)
if (!require("readxl")) install.packages("readxl")
if (!require("writexl")) install.packages("writexl")
if (!require("dplyr")) install.packages("dplyr")

library(readxl)
library(writexl)
library(dplyr)

# Set the path to the folder containing Excel files
folder_path <- "C:/Users/thaku/OneDrive/Desktop/medRxiv"

# Get a list of all .xlsx files in the folder (recursively)
file_list <- list.files(path = folder_path, pattern = "\\.xlsx$", full.names = TRUE, recursive = TRUE)

# Stop execution if no Excel files are found
if (length(file_list) == 0) {
  stop("No .xlsx files found in the specified directory.")
}

# Define a function to read and tag each file with its filename
read_tagged <- function(file) {
  df <- read_excel(file)
  df$source_file <- basename(file)
  return(df)
}

# Read and combine all Excel files into one data frame
combined_data <- lapply(file_list, read_tagged) %>% bind_rows()

cat("Total rows before deduplication:", nrow(combined_data), "\n")

# Check if the 'doi' column exists
if (!"doi" %in% names(combined_data)) {
  stop("No 'doi' column found in the combined dataset.")
}

# Identify duplicate rows based on DOI
duplicate_rows <- combined_data %>%
  group_by(doi) %>%
  filter(n() > 1) %>%
  arrange(doi)

# If duplicates exist, save them to a separate file
if (nrow(duplicate_rows) > 0) {
  cat("Found", nrow(duplicate_rows), "duplicate rows (by DOI).\n")
  write_xlsx(duplicate_rows, file.path(folder_path, "duplicates_by_doi.xlsx"))
  cat("Duplicates saved to: duplicates_by_doi.xlsx\n")
} else {
  cat("No duplicate DOIs found.\n")
}

# Remove duplicate entries, keeping only the first occurrence
deduplicated <- combined_data %>%
  distinct(doi, .keep_all = TRUE)

cat("Final row count after deduplication:", nrow(deduplicated), "\n")

# Save the cleaned, deduplicated dataset to a new Excel file
output_path <- file.path(folder_path, "aggregated_deduplicated.xlsx")
write_xlsx(deduplicated, output_path)
cat("Cleaned data saved to:", output_path, "\n")