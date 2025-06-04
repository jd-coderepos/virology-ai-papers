import os
import re
import json
import time
import pandas as pd
from pathlib import Path
from pdf2image import convert_from_path
import pytesseract
import ollama

import sys
import logging

# Set up logging to file
logging.basicConfig(
    filename="output_otheritems.txt",
    filemode='w',  # overwrite each run; use 'a' to append
    format='%(message)s',
    level=logging.INFO,
    encoding='utf-8'  # ensures Unicode characters are supported
)

# Redirect print() to also write to the file
class Logger(object):
    def __init__(self):
        self.terminal = sys.stdout
        self.log = open("output_otheritems.txt", "w", encoding='utf-8')

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        self.terminal.flush()
        self.log.flush()

sys.stdout = Logger()

# Optional: Set Tesseract path if not in system PATH
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def extract_text_from_pdf(pdf_path):
    try:
        from pdf2image.exceptions import PDFInfoNotInstalledError

        # Use your exact Poppler path
        poppler_path = r"C:\Users\thaku\Downloads\Release-24.08.0-0\poppler-24.08.0\Library\bin"

        # Convert PDF to images
        pages = convert_from_path(
            pdf_path,
            dpi=300,
            poppler_path=poppler_path
        )
        
        # OCR each page
        text = ""
        for page in pages:
            text += pytesseract.image_to_string(page) + "\n"
        return text.strip()

    except PDFInfoNotInstalledError:
        print("ERROR: Poppler not found or 'pdfinfo.exe' missing.")
        return ""
    except Exception as e:
        print(f"ERROR reading {pdf_path}: {e}")
        return ""


def strip_references(text):
    match = re.split(r'\bReferences\b|\bREFERENCES\b|\bBibliography\b', text, maxsplit=1)
    return match[0].strip() if match else text.strip()

# Function to interact with LLaMA 3.2 3B
def chat_with_llama(full_text):
    user_prompt = {
        "role": "user",
        "content": (
            "Analyze the provided research paper text and extract the following information strictly from the content without any assumptions:\n\n"
            f"{full_text}\n\n"
            "IMPORTANT: Your response must be strictly in JSON format and based solely on the provided text. Do not assume any information not present in the text.\n\n"
            "1. \"was_performance_measured\": Answer \"Yes\" **ONLY IF** the paper explicitly mentions performance evaluation, "
            "reports specific metrics, or references a performance comparison. Otherwise, answer \"No\".\n"
            "2. \"performance_results\": If \"was_performance_measured\" is \"Yes\", extract all reported performance metrics "
            "and their values as they appear in the paper. If multiple metrics are reported, format them as a structured JSON object.\n"
            "   - If evaluation is mentioned but no specific values are provided, return \"Mentioned but not provided\".\n"
            "   - If \"was_performance_measured\" is \"No\", return an empty string (\"\").\n"
            "3. \"performance_measurement_details\": If \"was_performance_measured\" is \"Yes\", describe how the performance was measured, "
            "including the methods, datasets, and evaluation criteria used. If not mentioned, return \"Not specified\".\n"
            "\nVerification Criteria:\n"
            "- The response **must be based strictly on explicit mentions** of performance evaluation.\n"
            "- If the paper does **not mention** any form of evaluation (e.g., accuracy, comparison to baseline, cross-validation, etc.), return **\"No\"**.\n"
            "- If a metric is **mentioned but has no numerical value**, return it as:\n"
            "     { \"Metric Name\": \"Mentioned but not provided\" }\n"
            "- Do **not** return lists or arrays. Only return **single numerical values** per metric.\n"
            "- If the paper reports multiple values for a metric, extract only the most representative value.\n"
            "- Do **not infer or assume** the existence of evaluations or metrics not directly stated.\n"
            "- **Do not assume** evaluation exists if it is implied or referenced indirectly.\n"
            "- Failure to follow these rules will result in an invalid response."
        )
    }

    system_prompt = {
        "role": "system",
        "content": "You are an AI assistant specializing in AI research paper analysis. Extract only the required structured information and return valid JSON."
    }
 
    for attempt in range(3):
        try:
            response = ollama.chat(
                model="llama3.2:3b",
                messages=[system_prompt, user_prompt],
                options={"temperature": 0}
            )
            content = response["message"]["content"]
            match = re.search(r"\{.*\}", content, re.DOTALL)
            if match:
                return json.loads(match.group(0))
        except Exception as e:
            print(f"LLaMA attempt {attempt+1} failed: {e}")
            time.sleep(1)
    return {}

def process_doi_csv(input_csv, pdf_dir, output_csv):
    df = pd.read_csv(input_csv)
    results = []

    for idx, row in df.iterrows():
        doi = row.get("doi", "").strip()
        if not doi:
            print(f"Row {idx} has no DOI, skipping.")
            continue

        doi_id = doi.replace("/", "_")
        matching_pdf = next(Path(pdf_dir).glob(f"*{doi_id}.pdf"), None)

        if not matching_pdf:
            print(f"No PDF found for DOI: {doi}")
            continue

        print(f"Processing:{doi}({matching_pdf.name})")
        raw_text = extract_text_from_pdf(matching_pdf)
        clean_text = strip_references(raw_text)
        llm_data = chat_with_llama(clean_text)

        result = {
            "Was Performance Measured": llm_data.get("was_performance_measured", "null"),
            "Performance Results": llm_data.get("performance_results", {}),
            "Performance Measurement Details": llm_data.get("performance_measurement_details", "Not specified")
        }
        print(json.dumps(result, indent=2, ensure_ascii=False)) 
        results.append(result)

    pd.DataFrame(results).to_csv(output_csv, index=False)
    print(f"\nProcessing complete. Output saved to: {output_csv}")

# === Final Paths ===
if __name__ == "__main__":
    input_csv = r"D:\Desktop\medrxiv_new\Finaloutput_embedding2_without_falsepositive_medrxiv.csv"
    pdf_dir = r"D:\Desktop\medrxiv_new\pdf\merged_pdfs"
    output_csv = r"D:\Desktop\medrxiv_new\Extracted_LLaMA_Output_performanceMertics_1new.csv"

    process_doi_csv(input_csv, pdf_dir, output_csv)