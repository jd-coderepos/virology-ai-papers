# STEP 0: Install required packages (only once)
if (!require("medrxivr")) install.packages("medrxivr")
if (!require("writexl")) install.packages("writexl")
if (!require("dplyr")) install.packages("dplyr")

# STEP 1: Load libraries
library(medrxivr)
library(writexl)
library(dplyr)

# STEP 2: Download medrxiv metadata (2015–2025)
metadata_path <- "medrxiv_metadata_2015_2025.rds"

if (!file.exists(metadata_path)) {
  cat("Downloading metadata from medRxiv...\n")
  data_medrxiv <- mx_api_content(from_date = "2015-01-01", to_date = "2025-04-15", server = "medrxiv")
  saveRDS(data_medrxiv, metadata_path)
} else {
  cat("metadata for medRxiv already present, loading cached metadata...\n")
  data_medrxiv <- readRDS(metadata_path)
}

# STEP 3: Define all topic-specific queries
query_list <- list(
  "virology-reinforcement.csv" = list(
    c("reinforcement learning", "policy optimization", "Q-learning", "deep Q-network", "actor-critic method",
      "markov decision process", "reward function", "exploration-exploitation", "temporal difference learning",
      "reinforcement learning agent", "reward maximization")
  ),
  
  "virology-agentic-ai.csv" = list(
    c("autonomous AI system", "tool use", "tool learning", "agent system", "multi-agent based system")
  ),
  
  "virology-deep-learning.csv" = list(
    c("deep learning", "deep neural network")
  ),
  
  "virology-neural-networks.csv" = list(
    c("neural network", "artificial neural network", "feedforward neural network", "backpropagation",
      "neural net algorithm", "multilayer perceptron", "convolutional neural network", "recurrent neural network",
      "long short-term memory network", "CNN", "GRNN", "RNN", "LSTM", "autoencoder")
  ),
  
  "virology-graph-neural-network.csv" = list(
    c("graph neural network", "GNN", "graph embedding", "graph representation learning", "node classification",
      "link prediction", "graph convolutional network", "message passing neural network", "graph attention network",
      "graph-based learning")
  ),
  
  "virology-computer-vision.csv" = list(
    c("computer vision", "vision model", "image processing", "vision algorithm", "computer graphics and vision",
      "object recognition", "object detection", "image recognition", "image segmentation", "image captioning",
      "image classification", "visual recognition", "image synthesis", "scene understanding")
  ),
  
  "virology-natural-language-processing.csv" = list(
    c("natural language processing", "text mining", "NLP", "computational linguistics", "language processing",
      "text analytics", "textual data analysis", "text data analysis", "text analysis", "text classification",
      "text understanding", "text generation", "speech and language technology", "language modeling",
      "language representation learning", "word embedding", "vector embedding", "computational semantics")
  ),
  
  "virology-generative-AI.csv" = list(
    c("generative artificial intelligence", "generative AI", "generative deep learning", "generative models",
      "AGI", "artificial general intelligence")
  ),
  
  "virology-transformer.csv" = list(
    c("transformer", "self-attention", "encoder", "decoder", "encoder-decoder", "transformer architecture",
      "attention-based neural network", "transformer network", "sequence-to-sequence", "mamba",
      "retrieval augmented generation", "RAG", "hybrid artificial intelligence", "hybrid AI", "human-in-the-loop")
  ),
  
  "virology-llm.csv" = list(
    c("large language model", "LLM", "language model", "transformer-based model", "pretrained language model",
      "generative language model", "foundation model", "state-of-the-art language model", "BERT", "GPT",
      "finetuned models", "finetuning")
  ),
  
  "virology-vision-transformer.csv" = list(
    c("multimodal model", "multimodal neural network", "multimodal transformer", "multi-modal language model",
      "multi-modal large language model", "multimodal learning", "vision transformer", "diffusion model",
      "generative diffusion model", "diffusion-based generative model", "continuous diffusion model",
      "fusion model", "multi-sensory learning")
  ),
  
  "virology-vision-language.csv" = list(
    c("vision-language model", "vision language model", "visual question answering", "visual grounding",
      "text-to-image generation", "image-text alignment")
  )
)

# STEP 4: Define relevant categories for infectious diseases
relevant_categories <- c(
  "Epidemiology",
  "Infectious Diseases (except HIV/AIDS)",
  "Public and Global Health",
  "Respiratory Medicine",
  "HIV/AIDS",
  "Pathology",
  "Immunology",
  "Intensive Care and Critical Care Medicine",
  "Pharmacology and Therapeutics",
  "Genetic and Genomic Medicine"
)


# STEP 5: Run each query, apply category filter, and export to Excel
for (file_name in names(query_list)) {
  cat("\nRunning query for:", file_name, "\n")
  query <- query_list[[file_name]]
  
  results <- tryCatch(
    mx_search(data = data_medrxiv, query = query, report = TRUE),
    error = function(e) {
      cat("Failed to search:", e$message, "\n")
      return(NULL)
    }
  )
  
  if (!is.null(results) && nrow(results) > 0) {
  
    # Filter by relevant categories
    results_filtered <- results %>%
      filter(category %in% relevant_categories)
    
    cat("Results after category filter:", nrow(results_filtered), "\n")
    
    if (nrow(results_filtered) > 0) {
      results_clean <- results_filtered %>%
        mutate(
          `Year of publication` = format(date, "%Y"),
          `Title of article` = title,
          Authors = authors
        ) %>%
        select(
          Authors, `Year of publication`, `Title of article`, category, date,
          abstract, doi
        )
      
      write_xlsx(results_clean, path = gsub(".csv$", ".xlsx", file_name))
      cat("Saved to:", gsub(".csv$", ".xlsx", file_name), "\n")
    } else {
      cat("Query returned results, but none matched relevant categories.\n")
    }
  } else {
    cat("No results found.\n")
  }
}