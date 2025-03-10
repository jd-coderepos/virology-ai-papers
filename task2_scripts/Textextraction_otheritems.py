import os
import re
import pandas as pd
from metapub import PubMedFetcher, PubMedAuthor
import xml.etree.ElementTree as ET
import ollama 
import json
import time

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
    retries = 3
    while retries > 0:
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
                print("Warning: LLaMA response did not contain valid JSON. Attempting to parse usable data...")
                parsed_data = attempt_to_extract_data(response_text)
                if parsed_data:
                    return parsed_data
                retries -= 1
                time.sleep(1)
        except json.JSONDecodeError:
            print("Error: LLaMA returned invalid JSON. Trying again...")
            retries -= 1
            time.sleep(1)
        except Exception as e:
            print(f"Error interacting with LLaMA: {e}. Trying again...")
            retries -= 1
            time.sleep(1)

    print("Failed to get a valid response after several attempts.")
    return {}

def attempt_to_extract_data(response_text):
    """Attempt to manually parse key-value pairs from malformed JSON or non-JSON output."""
    fields = ["subdomain", "disease_name", "research_aim", "research_problem", "ai_objective", "ai_methodology",
                "ai_method_details", "ai_method_type", "type_of_underlying_data", "dataset_name", ]
    data = {}
    for field in fields:
        regex = rf'"{field}"\s*:\s*(.*?)[,}}]'
        match = re.search(regex, response_text, re.DOTALL)
        if match:
            try:
                # Attempt to evaluate the extracted value safely if it looks like a dictionary or list
                data[field] = json.loads(match.group(1).strip('"'))
            except json.JSONDecodeError:
                # If not a JSON-like structure, just strip quotes and take raw string
                data[field] = match.group(1).strip('"')
    return data if data else None


def get_article_details(pmid):
    fetcher = PubMedFetcher()
    try:
        # Fetch article metadata using PMID
        article = fetcher.article_by_pmid(pmid)
        if not article:
            return {"primary_author_affiliation": "No article found", "publication_types": "Not available"}

        # Ensure the XML content is a string
        xml_content = article.xml
        if isinstance(xml_content, bytes):
            xml_content = xml_content.decode('utf-8')

        # Parse the XML content
        root = ET.fromstring(xml_content)

        # Extract primary author's affiliation
        primary_author_affiliation = "No authors found"
        primary_author_elem = root.find('.//AuthorList/Author')
        if primary_author_elem is not None:
            primary_author = PubMedAuthor(primary_author_elem)
            if primary_author.affiliations:
                primary_author_affiliation = primary_author.affiliations[0]

        # Extract evidence source
        publication_types = []
        pub_type_elements = root.findall('.//PublicationType')
        if pub_type_elements:
            publication_types = [pub_type.text for pub_type in pub_type_elements]

        return {
            "primary_author_affiliation": primary_author_affiliation,
            "publication_types": ", ".join(publication_types) if publication_types else "Publication type not available"
        }

    except Exception as e:
        return {"primary_author_affiliation": f"Error: {e}", "publication_types": "Error"}

def extract_full_text(xml_file):
    """Extracts full text content from an XML research paper and truncates it before the 'References' section."""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # Extract text from XML structure
        full_text = " ".join(elem.text.strip() for elem in root.iter() if elem.text)

        # Truncate text at "References" section
        truncated_text = re.split(r'<title>\s*References\s*</title>|References', full_text, maxsplit=1, flags=re.IGNORECASE)[0]
        return truncated_text.strip()
    
    except Exception as e:
        print(f"Error parsing XML: {e}")
        return None
    
def process_papers(csv_file_path, xml_folder_path, output_csv):
    """Reads PMCID from CSV, extracts metadata, processes XML with MetaPub, and saves results."""
    
    # Load CSV data
    df = pd.read_csv(csv_file_path, encoding='utf-8')
    df = df.head(30)
    # Ensure 'PMCID' column exists
    if 'PMCID' not in df.columns:
        print("Error: PMCID column not found in CSV file.")
        return

    # Define new required columns
    columns = [
        "Authors", "Year of publication", "Primary affiliation of primary author",
        "Title of article", "Name of Publication/Journal",
        "Subdomain", "Disease Name", "Type of Evidence Source", "Research Aim",
        "Research Problem", "AI Objective", "AI Methodology", "AI Method Details",
        "AI Method Type", "Is the software publicly released?",
        "software license","Type of Underlying Data", "Dataset Name"
    ]

    failed_pmcids = []
    processed_data = []

    # Process each row
    for _, row in df.iterrows():
        pmcid = str(row["PMCID"]).strip()
        
        # Find corresponding XML file
        xml_file_path = os.path.join(xml_folder_path, f"{pmcid}.xml")

        extracted_data = extract_full_text(xml_file_path)
        
        print(f"Processing {pmcid}...")
        llm_data = None
        for attempt in range(3):
            llm_data = chat_with_llama(extracted_data)

            if isinstance(llm_data, dict): 
                break
            else:
                print(f"Warning: Invalid LLaMA response (Attempt {attempt+1}/3) for {pmcid}")
                time.sleep(2)  # Wait before retrying

        if not isinstance(llm_data, dict): 
            print(f"Error: LLaMA failed to return valid JSON after 3 attempts for {pmcid}. Skipping...")
            failed_pmcids.append(pmcid)
            llm_data = {} 
        # Extract metadata
        metadata = {
            "Authors": row.get("Authors", ""),
            "Year of publication": row.get("Publication Year", ""),
            "Title of article": row.get("Title", ""),
            "Name of Publication/Journal": row.get("Journal/Book", "")
        }

        if llm_data:
            metadata.update({
            "Subdomain": llm_data.get("subdomain", "null"),
            "Disease Name": llm_data.get("disease_name", "null"),
            "Research Aim": llm_data.get("research_aim", "null"),
            "Research Problem": llm_data.get("research_problem", "null"),
            "AI Objective": llm_data.get("ai_objective", "null"),
            "AI Methodology": llm_data.get("ai_methodology", "null"),
            "AI Method Details": llm_data.get("ai_method_details", "null"),
            "AI Method Type": llm_data.get("ai_method_type", "null"),
            "Is the software publicly released?": " ",
            "software license": " ",
            "Type of Underlying Data": llm_data.get("type_of_underlying_data", "null"),
            "Dataset Name": llm_data.get("dataset_name", "null")
            })     

        # Extract primary author's affiliation and publication type using MetaPub
        pmid = row.get("PMID", "")
        if pmid:
            article_details = get_article_details(pmid)
            metadata["Primary affiliation of primary author"] = article_details["primary_author_affiliation"]
            metadata["Type of Evidence Source"] = article_details["publication_types"]

        # Append to results
        processed_data.append(metadata)
        print(processed_data)

    # Save processed data to CSV
    output_df = pd.DataFrame(processed_data, columns=columns)
    #print(processed_data)
    output_df.to_csv(output_csv, index=False, encoding='utf-8')
    print(f"Processing complete. Results saved to {output_csv}")

# Example usage
csv_file_path = "D:/studentassistant/student_assistanttask2//virology-ai-papers/scripts/codes/testLlama/final_outputandcode/missed_data.csv"
xml_folder_path = "D:/studentassistant/student_assistanttask2/working_dir/virology-ai-papers/xml_outputs"
output_csv = "D:/studentassistant/student_assistanttask2/virology-ai-papers/scripts/codes/testLlama/final_outputandcode/Extracted_fields.csv"

# Run processing
process_papers(csv_file_path, xml_folder_path, output_csv)
