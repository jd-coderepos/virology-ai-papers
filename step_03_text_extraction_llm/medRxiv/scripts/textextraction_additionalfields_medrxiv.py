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
            "Analyze the provided research paper text and extract the following information strictly from the content without any assumptions:"
            f"{full_text}\n\n"
            "IMPORTANT: Your response must be strictly in the JSON format, extract the following information strictly from the paper text provided without any assumptions:"
            "1. \"research_aim\": Extract the primary goal or aim of the research.\n"
            "2. \"research_problem\": Identify the specific research problem addressed in the paper.\n"
            "3. \"ai_objective\": What AI is being used for in the research.\n"
            "4. \"ai_methodology\": Provide a brief description of the AI-based approach used.\n"
            "5. \"ai_method_details\": Extract details about how AI is used, including specific techniques, architectures, or models.\n"
            "6. \"ai_method_type\": The AI method used. If more than one method present, return as a list.\n"
            "7. \"type_of_underlying_data\": The raw input used for experiment and analysis in the research paper.\n"
            "8. \"dataset_name\": Extract the name of the dataset used in the research.\n\n"
            
            "9. \"disease_name\": Identify and extract the infectious or viral disease examined in the paper. If multiple diseases are discussed, list them all.\n"
            "   - If multiple diseases are studied, return a list of disease names.\n"

            "10. \"virology_subdomain\": Determine the **specific subdomain of virology** studied in the paper. \n"
            "   - Identify the virology subdomain based on the focus of the study (e.g., respiratory viruses, neurotropic viruses, hepatic viruses, zoonotic viruses, etc.).\n"
            "   - If the paper discusses respiratory viruses (e.g., Influenza, RSV, SARS-CoV-2), return \"Respiratory Virology\".\n"
            "   - If the study focuses on viruses affecting the nervous system (e.g., Rabies, Zika, HSV), return \"Neurovirology\".\n"
            "   - If the research is related to liver viruses (e.g., Hepatitis B, Hepatitis C), return \"Hepatic Virology\".\n"
            "   - If the study examines how viruses interact with the immune system, return \"Viral Immunology\".\n"
            "   - If the research involves emerging or re-emerging viruses (e.g., COVID-19, Monkeypox, Nipah), return \"Emerging & Re-emerging Viruses\".\n"
            "   - If the focus is on viruses that jump from animals to humans (e.g., Ebola, Nipah), return \"Zoonotic Virology\".\n"
            "   - If the paper does not specify a clear virology subdomain, return \"General Virology\".\n\n"
            
            "Strict Constraints:\n"
            "- The response must be strictly based on explicit mentions in the paper. Do not infer or assume missing details.\n"
            "- Always return valid JSON output and do not include any additional text or explanations.\n\n"
            "- Failure to follow these rules will result in an invalid response."
        )
    }

    system_prompt = {
        "role": "system",
        "content": "You are an AI research assistant with expertise in Virology and Artificial Intelligence. Extract only the required structured information and return valid JSON."
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
            "Authors": row.get("Authors", ""),
            "Year of publication": row.get("Year of publication", ""),
            "Name of Publication/Journal": row.get("Name of Publication/Journal", ""),
            "Title": row.get("Title", ""),
            "category": row.get("category", ""),
            "date": row.get("date", ""),
            "Abstract": row.get("Abstract", ""),
            "doi": doi,
            "Research Aim": llm_data.get("research_aim", ""),
            "Research Problem": llm_data.get("research_problem", ""),
            "AI Objective": llm_data.get("ai_objective", ""),
            "AI Methodology": llm_data.get("ai_methodology", ""),
            "AI Method Details": llm_data.get("ai_method_details", ""),
            "AI Method Type": llm_data.get("ai_method_type", ""),
            "Type of Underlying Data": llm_data.get("type_of_underlying_data", ""),
            "Dataset Name": llm_data.get("dataset_name", ""),
            "Disease Name": llm_data.get("disease_name", ""),
            "Subdomain": llm_data.get("virology_subdomain", "")
        }

        results.append(result)

    pd.DataFrame(results).to_csv(output_csv, index=False)
    print(f"\nProcessing complete. Output saved to: {output_csv}")

# === Final Paths ===
if __name__ == "__main__":
    input_csv = r"D:\Desktop\biorxiv_new\Final_output_without_false_postives.csv"
    pdf_dir = r"D:\Desktop\biorxiv_new\pdf\merged_pdfs"
    output_csv = r"D:\Desktop\biorxiv_new\Extracted_LLaMA_Output.csv"

    process_doi_csv(input_csv, pdf_dir, output_csv)

