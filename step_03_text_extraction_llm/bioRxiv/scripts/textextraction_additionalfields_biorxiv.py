import os
import re
import pandas as pd
import json
import time
import xml.etree.ElementTree as ET
import ollama

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

    try:
        response = ollama.chat(
            model="llama3.2:3b",
            messages=[system_prompt, user_prompt],
            options={"temperature": 0}
        )
        response_text = response["message"]["content"].strip()
        print(response_text)
        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        else:
            print("Warning: LLaMA response did not contain valid JSON.")
            return {}
    except json.JSONDecodeError:
        print("Error: LLaMA returned invalid JSON.")
        return {}
    except Exception as e:
        print(f"Error interacting with LLaMA: {e}")
        return {}

def extract_full_text(xml_file):
    """Extracts full text content from an XML research paper and truncates it before the 'References' section."""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        full_text = " ".join(elem.text.strip() for elem in root.iter() if elem.text)
        truncated_text = re.split(r'<title>\s*References\s*</title>|References', full_text, maxsplit=1, flags=re.IGNORECASE)[0]
        return truncated_text.strip()
    except Exception as e:
        print(f"Error parsing XML: {e}")
        return None

def process_papers(csv_file_path, xml_folder_path, output_csv):
    """Reads PMCID from CSV, extracts metadata, processes XML, and saves performance evaluation results."""
    # Read only the first 4 rows of the CSV file
    df = pd.read_csv(csv_file_path)
    df = df.tail(13)
    
    if 'PMCID' not in df.columns:
        print("Error: PMCID column not found in CSV file.")
        return

    processed_data = []
    failed_pmcids = []
    
    for _, row in df.iterrows():
        pmcid = str(row["PMCID"]).strip()
        xml_file_path = os.path.join(xml_folder_path, f"{pmcid}.xml")
        extracted_data = extract_full_text(xml_file_path)
        
        print(f"Processing {pmcid}...")
        llm_data = None
        
        for attempt in range(3):
            llm_data = chat_with_llama(extracted_data)
            if isinstance(llm_data, dict): 
                break
            print(f"Warning: Invalid LLaMA response (Attempt {attempt+1}/3) for {pmcid}")
            time.sleep(2)

        if not isinstance(llm_data, dict):
            print(f"Error: LLaMA failed to return valid JSON after 3 attempts for {pmcid}. Skipping...")
            failed_pmcids.append(pmcid)
            llm_data = {}
        
        metadata = {
            "PMCID": pmcid,
            "Was Performance Measured": llm_data.get("was_performance_measured", "null"),
            "Performance Results": llm_data.get("performance_results", {}),
            "Performance Measurement Details": llm_data.get("performance_measurement_details", "Not specified")
        }
        
        processed_data.append(metadata)
        print(processed_data)
    
    output_df = pd.DataFrame(processed_data, columns=["PMCID", "Was Performance Measured", "Performance Results", "Performance Measurement Details"])
    output_df.to_csv(output_csv, index=False)
    print(f"Processing complete. Results saved to {output_csv}")

# Example usage
csv_file_path = "D:/studentassistant/student_assistanttask2/working_dir/virology-ai-papers/dataset/OutputOfEmbedding2WithoutFalsePositive.csv"
xml_folder_path = "D:/studentassistant/student_assistanttask2/working_dir/virology-ai-papers/xml_outputs"
output_csv = "D:/studentassistant/student_assistanttask2/virology-ai-papers/scripts/codes/testLlama/Performance_metrics.csv"

process_papers(csv_file_path, xml_folder_path, output_csv)
