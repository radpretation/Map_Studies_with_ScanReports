# import re
# import docx
# import pdfplumber
# from docx.oxml.table import CT_Tbl
# from docx.oxml.text.paragraph import CT_P
# from docx.table import Table
# from docx.text.paragraph import Paragraph

# class RegexEngine:
#     INSTITUTION_MAP = {
#         "AIIA_Delhi": "ALL INDIA INSTITUTE OF AYURVEDA",
#         "CHC_Jagdishpur": "CHC Jagdishpur"
#     }

#     ID_NORMALIZATION_RULES = {
#         "ALL INDIA INSTITUTE OF AYURVEDA": lambda raw_id: re.sub(r'\D', '', raw_id),
#         "CHC Jagdishpur": lambda raw_id: f"CHC{re.search(r'\d+', raw_id).group()}" if re.search(r'\d+', raw_id) else raw_id
#     }

#     @staticmethod
#     def normalize_patient_id(raw_id: str, institute_name: str) -> str:
#         if not raw_id or raw_id == "UNKNOWN":
#             return "UNKNOWN"
#         rule = RegexEngine.ID_NORMALIZATION_RULES.get(institute_name)
#         if rule:
#             try:
#                 return rule(raw_id)
#             except Exception:
#                 return raw_id 
#         return raw_id

#     @staticmethod
#     def extract_institute_from_path(cloud_path: str) -> str:
#         parts = cloud_path.split('/')
#         try:
#             reports_idx = parts.index("Reports")
#             raw_inst = parts[reports_idx + 1]
#             return RegexEngine.INSTITUTION_MAP.get(raw_inst, raw_inst)
#         except ValueError:
#             return "UNKNOWN_INSTITUTE"

#     @staticmethod
#     def extract_text(filepath: str) -> str:
#         """Extracts text sequentially, preserving the order of paragraphs and tables."""
#         text = ""
#         try:
#             if filepath.lower().endswith('.docx'):
#                 doc = docx.Document(filepath)
#                 text_elements = []
                
#                 # Iterating through the XML body to maintain exact top-to-bottom document structure
#                 for child in doc.element.body:
#                     if isinstance(child, CT_P):
#                         para = Paragraph(child, doc)
#                         if para.text.strip():
#                             text_elements.append(para.text.strip())
#                     elif isinstance(child, CT_Tbl):
#                         table = Table(child, doc)
#                         for row in table.rows:
#                             # Flatten table rows with pipes
#                             row_data = [cell.text.strip().replace('\n', ' ') for cell in row.cells if cell.text.strip()]
#                             if row_data:
#                                 text_elements.append(" | ".join(row_data))
                                
#                 text = '\n'.join(text_elements)
                
#             elif filepath.lower().endswith('.pdf'):
#                 with pdfplumber.open(filepath) as pdf:
#                     text = '\n'.join([page.extract_text() or "" for page in pdf.pages])
#             else:
#                 with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
#                     text = f.read()
#         except Exception as e:
#             print(f"❌ Error reading text: {e}")
#         return text
    
#     @staticmethod
#     def parse_document_text(text: str) -> dict:
#         clean_text = re.sub(r'\s*\|\s*', ' ', text)
        
#         metadata = {
#             "patientName": "UNKNOWN",
#             "patientID": "UNKNOWN",
#             "uhid": "UNKNOWN",
#             "age": "UNKNOWN",
#             "gender": "UNKNOWN",
#             "description": "UNKNOWN",
#             "reportText": ""
#         }
        
#         # Metadata Lookahead Boundaries (Prevents text bleed in PDFs)
        
#         boundaries = r'(?:Patient\s*ID|ID\s*NO|\bUHID\b|\bID\b|Age|Date|Sex|Gender|Ref|Address|Mobile|Report|\n|$)'
        
#         # 1. Name Extraction
#         name_match = re.search(r'(?:Patient\s*Name|Name)\s*[:-]?\s*(.+?)(?=\s*' + boundaries + ')', clean_text, re.IGNORECASE)
#         if name_match:
#             metadata["patientName"] = name_match.group(1).strip().upper()
            
#         # 2. UHID Extraction
#         uhid_match = re.search(r'\bUHID\b\s*[:-]?\s*([A-Z0-9\-\s]+?)(?=\s*' + boundaries + ')', clean_text, re.IGNORECASE)
#         if uhid_match:
#             metadata["uhid"] = uhid_match.group(1).strip()

#         # 3. Patient ID Extraction
#         id_match = re.search(r'(?:Patient\s*ID|ID\s*NO|\bID\b)\s*[:-]?\s*([A-Z0-9\-\s]+?)(?=\s*' + boundaries + ')', clean_text, re.IGNORECASE)
#         if id_match:
#             metadata["patientID"] = id_match.group(1).strip()
#         else:
#             alt_id_match = re.search(r'\b(CHC\s*[-:]?\s*\d+|IPD\s*[-:]?\s*\d+|PT\s*[-:]?\s*\d+)\b', clean_text, re.IGNORECASE)
#             if alt_id_match:
#                 metadata["patientID"] = alt_id_match.group(1).strip()
                
                
#        # 4. Strict Age / Gender Extraction (Supports Combined and Separated layouts)
#         age_sex_match = re.search(r'(\d+)\s*(?:Y|Years|Yrs|Months)?\s*[\/\|\-]\s*(Male|Female|M|F)\b', clean_text, re.IGNORECASE)
#         if age_sex_match:
#             metadata["age"] = age_sex_match.group(1).strip()
#             gen_str = age_sex_match.group(2).upper()
#             metadata["gender"] = "MALE" if gen_str.startswith('M') else "FEMALE"
#         else:
#             # Fallback for separated PDF layouts
#             isolated_age = re.search(r'\bAge\b\s*[:-]?\s*(\d+)', clean_text, re.IGNORECASE)
#             if isolated_age:
#                 metadata["age"] = isolated_age.group(1).strip()
                
#             isolated_gender = re.search(r'\b(?:Gender|Sex)\b\s*[:-]?\s*(Male|Female|M|F)\b', clean_text, re.IGNORECASE)
#             if isolated_gender:
#                 gen_str = isolated_gender.group(1).upper()
#                 metadata["gender"] = "MALE" if gen_str.startswith('M') else "FEMALE"

#         # 5. Clean Report Text Body Extraction
#         start_idx = 0
#         search_area = text[:1500]
        
#         # Robust End Pattern mapped directly to PDF elements
#         table_end_pattern = r'(?:DATE[^\n]*|REFERRED\s*BY[^\n]*|UHID[^\n]*|Report\s*No\.?[^\n]*|Mobile[^\n]*)\n'
#         matches = list(re.finditer(table_end_pattern, search_area, re.IGNORECASE))
        
#         if matches:
#             start_idx = matches[-1].end()
            
#         report_body = text[start_idx:].strip()
        
#         report_body = re.sub(r'^[\s\|]+', '', report_body).strip()
#         report_body = re.sub(r'^(?:REFERRED\s*BY[^\n]*\n?[\s\|]*)+', '', report_body, flags=re.IGNORECASE).strip()
#         report_body = re.sub(r'^[\s\|]+', '', report_body).strip()
        
#         metadata["reportText"] = report_body

#         # 6. Precision Description Extraction
#         if report_body:
#             desc_lines = [line.strip() for line in report_body.split('\n') if re.search(r'[a-zA-Z]', line)]
            
#             if desc_lines:
#                 first_line = desc_lines[0] 
#                 desc_clean = re.sub(r'^(?:Examination\s*[:-]?\s*)', '', first_line, flags=re.IGNORECASE)
#                 desc_clean = re.sub(r'[:-]+$', '', desc_clean).strip().upper()
                
#                 if desc_clean not in ["TECHNIQUE", "FINDINGS", "OBSERVATION", "IMPRESSION"] and len(desc_clean) > 3:
#                     metadata["description"] = desc_clean

#         return metadata



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
            "uhid": "UNKNOWN",
            "age": "UNKNOWN",
            "gender": "UNKNOWN",
            "description": "UNKNOWN",
            "reportText": ""
        }
        
        # Hardened boundaries mapped to both PDF and DOCX labels
        boundaries = r'Patient\s*Name|Name|Patient\s*ID|ID\s*NO|\bUHID\b|\bID\b|Age|Date|Sex|Gender|Ref|Address|Mobile|Report'
        lookahead = r'(?=\s*(?:' + boundaries + r')|\s*\n|\s*$)'
        
        # 1. Name Extraction (Uses [^\n]+? to strictly prevent crossing newlines)
        name_match = re.search(r'(?:Patient\s*Name|Name)\s*[:-]?\s*([^\n]+?)' + lookahead, clean_text, re.IGNORECASE)
        if name_match:
            metadata["patientName"] = name_match.group(1).strip().upper()
            
        # 2. UHID Extraction
        uhid_match = re.search(r'\bUHID\b\s*[:-]?\s*([^\n]+?)' + lookahead, clean_text, re.IGNORECASE)
        if uhid_match:
            metadata["uhid"] = uhid_match.group(1).strip()

        # 3. Patient ID Extraction
        id_match = re.search(r'(?:Patient\s*ID|ID\s*NO|\bID\b)\s*[:-]?\s*([^\n]+?)' + lookahead, clean_text, re.IGNORECASE)
        if id_match:
            metadata["patientID"] = id_match.group(1).strip()
        else:
            # Fallback for standalone IDs like PT804429 or CHC3948
            alt_id_match = re.search(r'\b(CHC\s*[-:]?\s*\d+|IPD\s*[-:]?\s*\d+|PT\s*[-:]?\s*\d+)\b', clean_text, re.IGNORECASE)
            if alt_id_match:
                metadata["patientID"] = alt_id_match.group(1).strip()
                
        # 4. Strict Age / Gender Extraction (Supports Combined and Separated layouts)
        age_sex_match = re.search(r'(\d+)\s*(?:Y|Years|Yrs|Months)?\s*[\/\|\-]\s*(Male|Female|M|F)\b', clean_text, re.IGNORECASE)
        if age_sex_match:
            metadata["age"] = age_sex_match.group(1).strip()
            gen_str = age_sex_match.group(2).upper()
            metadata["gender"] = "MALE" if gen_str.startswith('M') else "FEMALE"
        else:
            # Fallback for separated PDF layouts
            isolated_age = re.search(r'\bAge\b\s*[:-]?\s*(\d+)', clean_text, re.IGNORECASE)
            if isolated_age:
                metadata["age"] = isolated_age.group(1).strip()
                
            isolated_gender = re.search(r'\b(?:Gender|Sex)\b\s*[:-]?\s*(Male|Female|M|F)\b', clean_text, re.IGNORECASE)
            if isolated_gender:
                gen_str = isolated_gender.group(1).upper()
                metadata["gender"] = "MALE" if gen_str.startswith('M') else "FEMALE"

        # 5. Clean Report Text Body Extraction
        start_idx = 0
        search_area = text[:1500]
        
        # Robust End Pattern mapped directly to PDF elements
        table_end_pattern = r'(?:DATE[^\n]*|REFERRED\s*BY[^\n]*|UHID[^\n]*|Report\s*No\.?[^\n]*|Mobile[^\n]*)\n'
        matches = list(re.finditer(table_end_pattern, search_area, re.IGNORECASE))
        
        if matches:
            start_idx = matches[-1].end()
            
        report_body = text[start_idx:].strip()
        
        report_body = re.sub(r'^[\s\|]+', '', report_body).strip()
        report_body = re.sub(r'^(?:REFERRED\s*BY[^\n]*\n?[\s\|]*)+', '', report_body, flags=re.IGNORECASE).strip()
        report_body = re.sub(r'^[\s\|]+', '', report_body).strip()
        
        metadata["reportText"] = report_body

        # 6. Precision Description Extraction
        if report_body:
            desc_lines = [line.strip() for line in report_body.split('\n') if re.search(r'[a-zA-Z]', line)]
            
            if desc_lines:
                first_line = desc_lines[0] 
                desc_clean = re.sub(r'^(?:Examination\s*[:-]?\s*)', '', first_line, flags=re.IGNORECASE)
                desc_clean = re.sub(r'[:-]+$', '', desc_clean).strip().upper()
                
                if desc_clean not in ["TECHNIQUE", "FINDINGS", "OBSERVATION", "IMPRESSION"] and len(desc_clean) > 3:
                    metadata["description"] = desc_clean

        return metadata