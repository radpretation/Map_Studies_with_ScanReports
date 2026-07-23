import re
import docx
import pdfplumber
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph

class RegexEngine:
    INSTITUTION_MAP = {
        "AIIA_Delhi": "ALL INDIA INSTITUTE OF AYURVEDA",
        "CHC_Jagdishpur": "CHC Jagdishpur"
    }

    ID_NORMALIZATION_RULES = {
        "ALL INDIA INSTITUTE OF AYURVEDA": lambda raw_id: re.sub(r'\D', '', raw_id),
        "CHC Jagdishpur": lambda raw_id: f"CHC{re.search(r'\d+', raw_id).group()}" if re.search(r'\d+', raw_id) else raw_id
    }

    @staticmethod
    def normalize_patient_id(raw_id: str, institute_name: str) -> str:
        if not raw_id or raw_id == "UNKNOWN":
            return "UNKNOWN"
        rule = RegexEngine.ID_NORMALIZATION_RULES.get(institute_name)
        if rule:
            try:
                return rule(raw_id)
            except Exception:
                return raw_id 
        return raw_id

    @staticmethod
    def extract_institute_from_path(cloud_path: str) -> str:
        parts = cloud_path.split('/')
        try:
            reports_idx = parts.index("Reports")
            raw_inst = parts[reports_idx + 1]
            return RegexEngine.INSTITUTION_MAP.get(raw_inst, raw_inst)
        except ValueError:
            return "UNKNOWN_INSTITUTE"

    @staticmethod
    def extract_text(filepath: str) -> str:
        """Extracts text sequentially, preserving the order of paragraphs and tables."""
        text = ""
        try:
            if filepath.lower().endswith('.docx'):
                doc = docx.Document(filepath)
                text_elements = []
                
                # Iterating through the XML body to maintain exact top-to-bottom document structure
                for child in doc.element.body:
                    if isinstance(child, CT_P):
                        para = Paragraph(child, doc)
                        if para.text.strip():
                            text_elements.append(para.text.strip())
                    elif isinstance(child, CT_Tbl):
                        table = Table(child, doc)
                        for row in table.rows:
                            # Flatten table rows with pipes
                            row_data = [cell.text.strip().replace('\n', ' ') for cell in row.cells if cell.text.strip()]
                            if row_data:
                                text_elements.append(" | ".join(row_data))
                                
                text = '\n'.join(text_elements)
                
            elif filepath.lower().endswith('.pdf'):
                with pdfplumber.open(filepath) as pdf:
                    text = '\n'.join([page.extract_text() or "" for page in pdf.pages])
            else:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
        except Exception as e:
            print(f"❌ Error reading text: {e}")
        return text
    
    @staticmethod
    def parse_document_text(text: str) -> dict:
        clean_text = re.sub(r'\s*\|\s*', ' ', text)
        
        metadata = {
            "patientName": "UNKNOWN",
            "patientID": "UNKNOWN",
            "age": "UNKNOWN",
            "gender": "UNKNOWN",
            "description": "UNKNOWN",
            "reportText": ""
        }
        
        # 1. Name Extraction (Added \n to boundary to catch inline variations)
        name_match = re.search(r'(?:Patient\s*Name|Name)\s*[:-]?\s*(.+?)\s*(?:Patient\s*ID|ID\s*NO|\bUHID\b|\bID\b|Age|Date|Sex|\n|$)', clean_text, re.IGNORECASE)
        if name_match:
            metadata["patientName"] = name_match.group(1).strip().upper()

        # 2. Patient ID Extraction 
        id_match = re.search(r'(?:Patient\s*ID|ID\s*NO|\bUHID\b|\bID\b)\s*[:-]?\s*([A-Z0-9\-\s]+?)(?:Age|Date|Sex|Referred|\n|$)', clean_text, re.IGNORECASE)
        if id_match:
            metadata["patientID"] = id_match.group(1).strip()
        else:
            # Failsafe for missing labels (e.g., Image 5: "CHC-3801" floating on its own line)
            alt_id_match = re.search(r'\b(CHC\s*[-:]?\s*\d+|IPD\s*[-:]?\s*\d+)\b', clean_text, re.IGNORECASE)
            if alt_id_match:
                metadata["patientID"] = alt_id_match.group(1).strip()

        # 3. Strict Age / Gender Extraction
        age_sex_match = re.search(r'(\d+)\s*(?:Y|Years|Yrs|Months)?\s*[\/\|\-]\s*(Male|Female|M|F)\b', clean_text, re.IGNORECASE)
        if age_sex_match:
            metadata["age"] = age_sex_match.group(1).strip()
            gen_str = age_sex_match.group(2).upper()
            metadata["gender"] = "MALE" if gen_str.startswith('M') else "FEMALE"

        # 4. Clean Report Text Body Extraction
        start_idx = 0
        search_area = text[:1000]
        table_end_pattern = r'(?:DATE[\s:|0-9a-zA-Z/-]+|REFERRED\s*BY[^\n]*|UHID[^\n]*)\n'
        matches = list(re.finditer(table_end_pattern, text, re.IGNORECASE))
        
        if matches:
            start_idx = matches[-1].end()
            
        report_body = text[start_idx:].strip()
        
        # Aggressive purge of any leftover REFERRED BY artifacts that bled through empty tables
        report_body = re.sub(r'^[\s\|]+', '', report_body).strip()
        report_body = re.sub(r'^(?:REFERRED\s*BY[^\n]*\n?[\s\|]*)+', '', report_body, flags=re.IGNORECASE).strip()
        report_body = re.sub(r'^[\s\|]+', '', report_body).strip()
        
        metadata["reportText"] = report_body

        # 5. Precision Description Extraction
        # if report_body:
        #     # Isolate only the text between the metadata table and the first clinical keyword
        #     heading_area = re.split(r'\n\s*(?:TECHNIQUE|FINDINGS|OBSERVATION|IMPRESSION)[\s:-]', report_body, flags=re.IGNORECASE)[0]
            
        #     # Filter out empty lines or lines with only symbols (like the stray hyphen in Image 1)
        #     desc_lines = [line.strip() for line in heading_area.split('\n') if re.search(r'[a-zA-Z]', line)]
            
        #     if desc_lines:
        #         first_line = desc_lines[0] # Guaranteed to be the actual text heading
                
        #         # Clean prefixes ("Examination:") and suffixes (":", "-", "_")
        #         desc_clean = re.sub(r'^(?:Examination\s*[:-]?\s*)', '', first_line, flags=re.IGNORECASE)
        #         desc_clean = re.sub(r'[:-]+$', '', desc_clean).strip().upper()
                
        #         if desc_clean not in ["TECHNIQUE", "FINDINGS", "OBSERVATION", "IMPRESSION"] and len(desc_clean) > 3:
        #             metadata["description"] = desc_clean
        if report_body:
            # Filter out empty lines or stray symbols to find the real first text line
            desc_lines = [line.strip() for line in report_body.split('\n') if re.search(r'[a-zA-Z]', line)]
            
            if desc_lines:
                first_line = desc_lines[0] 
                
                # Clean prefixes ("Examination:") and trailing punctuation
                desc_clean = re.sub(r'^(?:Examination\s*[:-]?\s*)', '', first_line, flags=re.IGNORECASE)
                desc_clean = re.sub(r'[:-]+$', '', desc_clean).strip().upper()
                
                # Failsafe: Don't accidentally grab a sub-heading if the main title was completely omitted
                if desc_clean not in ["TECHNIQUE", "FINDINGS", "OBSERVATION", "IMPRESSION"] and len(desc_clean) > 3:
                    metadata["description"] = desc_clean

        return metadata