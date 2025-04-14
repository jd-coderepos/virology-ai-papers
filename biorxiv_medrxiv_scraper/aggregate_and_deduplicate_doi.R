# Load libraries
if (!require("readxl")) install.packages("readxl")
if (!require("writexl")) install.packages("writexl")
if (!require("dplyr")) install.packages("dplyr")

library(readxl)
library(writexl)
library(dplyr)

# Fixed path to folder with Excel files
folder_path <- "C:/Users/thaku/OneDrive/Desktop/bio_lib"  # use forward slashes

# Get all .xlsx files recursively
file_list <- list.files(path = folder_path, pattern = "\\.xlsx$", full.names = TRUE, recursive = TRUE)

if (length(file_list) == 0) {
  stop("No .xlsx files found in the specified directory.")
}

# Read and tag each file with its origin
read_tagged <- function(file) {
  df <- read_excel(file)
  df$source_file <- basename(file)
  return(df)
}

# Combine all files
combined_data <- lapply(file_list, read_tagged) %>% bind_rows()

cat("Total rows before deduplication:", nrow(combined_data), "\n")

# Check for 'doi' column
if (!"doi" %in% names(combined_data)) {
  stop("No 'doi' column found in the combined dataset.")
}

# Identify duplicates
duplicate_rows <- combined_data %>%
  group_by(doi) %>%
  filter(n() > 1) %>%
  arrange(doi)

if (nrow(duplicate_rows) > 0) {
  cat("Found", nrow(duplicate_rows), "duplicate rows (by DOI).\n")
  write_xlsx(duplicate_rows, file.path(folder_path, "duplicates_by_doi.xlsx"))
  cat("Duplicates saved to: duplicates_by_doi.xlsx\n")
} else {
  cat("No duplicate DOIs found.\n")
}

# Deduplicate
deduplicated <- combined_data %>%
  distinct(doi, .keep_all = TRUE)

cat("Final row count after deduplication:", nrow(deduplicated), "\n")

# Save final dataset
output_path <- file.path(folder_path, "aggregated_deduplicated.xlsx")
write_xlsx(deduplicated, output_path)
cat("Cleaned data saved to:", output_path, "\n")
