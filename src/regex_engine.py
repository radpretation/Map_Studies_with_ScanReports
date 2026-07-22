

# # import re
# # import docx
# # import pdfplumber

# # class RegexEngine:
# #     INSTITUTION_MAP = {
# #         "AIIA_Delhi": "ALL INDIA INSTITUTE OF AYURVEDA",
# #         "CHC_Jagdishpur": "CHC Jagdishpur"
# #     }

# #     ID_NORMALIZATION_RULES = {
# #         "ALL INDIA INSTITUTE OF AYURVEDA": lambda raw_id: re.sub(r'\D', '', raw_id),
# #         "CHC Jagdishpur": lambda raw_id: f"CHC{re.search(r'\d+', raw_id).group()}" if re.search(r'\d+', raw_id) else raw_id
# #     }

# #     @staticmethod
# #     def normalize_patient_id(raw_id: str, institute_name: str) -> str:
# #         if not raw_id or raw_id == "UNKNOWN":
# #             return "UNKNOWN"
# #         rule = RegexEngine.ID_NORMALIZATION_RULES.get(institute_name)
# #         if rule:
# #             try:
# #                 return rule(raw_id)
# #             except Exception:
# #                 return raw_id 
# #         return raw_id

# #     @staticmethod
# #     def extract_institute_from_path(cloud_path: str) -> str:
# #         parts = cloud_path.split('/')
# #         try:
# #             reports_idx = parts.index("Reports")
# #             raw_inst = parts[reports_idx + 1]
# #             return RegexEngine.INSTITUTION_MAP.get(raw_inst, raw_inst)
# #         except ValueError:
# #             return "UNKNOWN_INSTITUTE"

# #     @staticmethod
# #     def extract_text(filepath: str) -> str:
# #         text = ""
# #         try:
# #             if filepath.lower().endswith('.docx'):
# #                 doc = docx.Document(filepath)
                
# #                 # 1. Extract from Tables (This captures the missing metadata)
# #                 table_text = []
# #                 for table in doc.tables:
# #                     for row in table.rows:
# #                         # Grab text, replace newlines in cells, and ignore empty cells
# #                         row_data = [cell.text.strip().replace('\n', ' ') for cell in row.cells if cell.text.strip()]
# #                         if row_data:
# #                             # Join with pipes to mimic PDF flattening
# #                             table_text.append(" | ".join(row_data))
                
# #                 # 2. Extract from Paragraphs (This captures the clinical report)
# #                 para_text = [para.text.strip() for para in doc.paragraphs if para.text.strip()]
                
# #                 # Combine both sets of text
# #                 text = '\n'.join(table_text + para_text)
                
# #             elif filepath.lower().endswith('.pdf'):
# #                 with pdfplumber.open(filepath) as pdf:
# #                     text = '\n'.join([page.extract_text() or "" for page in pdf.pages])
# #             else:
# #                 with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
# #                     text = f.read()
# #         except Exception as e:
# #             print(f"❌ Error reading text: {e}")
# #         return text
    
# #     @staticmethod
# #     def parse_document_text(text: str) -> dict:
# #         # Clean up pipe characters and extra spaces from flattened tables
# #         clean_text = re.sub(r'\s*\|\s*', ' ', text)
        
# #         metadata = {
# #             "patientName": "UNKNOWN",
# #             "patientID": "UNKNOWN",
# #             "age": "UNKNOWN",
# #             "gender": "UNKNOWN",
# #             "description": "UNKNOWN",
# #             "reportText": ""
# #         }
        
# #         # 1. Name Extraction 
# #         name_match = re.search(r'(?:Patient\s*Name|Name)\s*[:-]?\s*([A-Za-z\s]+?)(?:Patient\s*ID|ID\s*NO|UHID|Age|Date|Sex)', clean_text, re.IGNORECASE)
# #         if name_match:
# #             metadata["patientName"] = name_match.group(1).strip().upper()

# #         # 2. Patient ID Extraction 
# #         id_match = re.search(r'(?:Patient\s*ID|ID\s*NO|UHID|ID)\s*[:-]?\s*([A-Z0-9\-\s]+?)(?:Age|Date|Sex|Referred)', clean_text, re.IGNORECASE)
# #         if id_match:
# #             metadata["patientID"] = id_match.group(1).strip()

# #         # 3. Age / Gender Extraction
# #         age_sex_match = re.search(r'(?:Age\s*/\s*Sex|Age|Sex)\s*[:-]?\s*(\d+)\s*(?:Y|Years|Yrs|Months)?\s*/?\s*([A-Za-z]+)', clean_text, re.IGNORECASE)
# #         if age_sex_match:
# #             metadata["age"] = age_sex_match.group(1).strip()
# #             metadata["gender"] = "MALE" if age_sex_match.group(2).upper().startswith('M') else "FEMALE"

# #         # 4. Clean Report Text Body Extraction
# #         # Start after the table data (usually REFERRED BY or DATE)
# #         start_idx = 0
# #         ref_match = re.search(r'(?:REFERRED\s*BY[^\n]*\n|DATE[\s:]*.*?\d{4}\n)', text, re.IGNORECASE)
# #         if ref_match:
# #             start_idx = ref_match.end()
        
# #         # End before the signature block
# #         end_idx = len(text)
# #         sig_match = re.search(r'(Reported\s*by|Dr\.|NOT\s*VALID\s*FOR\s*MEDICOLEGAL|Consultant\s*Radiologist|MBBS)', text, re.IGNORECASE)
# #         if sig_match:
# #             end_idx = sig_match.start()
            
# #         if start_idx < end_idx:
# #             report_body = text[start_idx:end_idx].strip()
# #         else:
# #             report_body = text.strip()
            
# #         metadata["reportText"] = report_body

# #         # 5. Description Extraction (Pulled directly from the top of the newly isolated reportText)
# #         if report_body:
# #             # Look at the very first line of the clean report body
# #             first_line = report_body.split('\n')[0].strip()
# #             # Clean off "Examination:" or trailing colons
# #             desc_clean = re.sub(r'^(?:Examination\s*[:-]?\s*)', '', first_line, flags=re.IGNORECASE)
# #             desc_clean = re.sub(r'[:-]$', '', desc_clean).strip().upper()
            
# #             # Ensure we didn't just grab "TECHNIQUE" or "FINDINGS" if the header was missing
# #             if desc_clean not in ["TECHNIQUE", "FINDINGS"]:
# #                 metadata["description"] = desc_clean

# #         return metadata


# import re
# import docx
# import pdfplumber

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
#         text = ""
#         try:
#             if filepath.lower().endswith('.docx'):
#                 doc = docx.Document(filepath)
                
#                 # Extract from Tables first
#                 table_text = []
#                 for table in doc.tables:
#                     for row in table.rows:
#                         row_data = [cell.text.strip().replace('\n', ' ') for cell in row.cells if cell.text.strip()]
#                         if row_data:
#                             table_text.append(" | ".join(row_data))
                
#                 # Extract from Paragraphs
#                 para_text = [para.text.strip() for para in doc.paragraphs if para.text.strip()]
#                 text = '\n'.join(table_text + para_text)
                
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
#             "age": "UNKNOWN",
#             "gender": "UNKNOWN",
#             "description": "UNKNOWN",
#             "reportText": ""
#         }
        
#         # 1. Name Extraction 
#         name_match = re.search(r'(?:Patient\s*Name|Name)\s*[:-]?\s*([A-Za-z\s]+?)(?:Patient\s*ID|ID\s*NO|UHID|Age|Date|Sex)', clean_text, re.IGNORECASE)
#         if name_match:
#             metadata["patientName"] = name_match.group(1).strip().upper()

#         # 2. Patient ID Extraction (Includes UHID support)
#         id_match = re.search(r'(?:Patient\s*ID|ID\s*NO|UHID|ID)\s*[:-]?\s*([A-Z0-9\-\s]+?)(?:Age|Date|Sex|Referred)', clean_text, re.IGNORECASE)
#         if id_match:
#             metadata["patientID"] = id_match.group(1).strip()

#         # 3. Age / Gender Extraction (Strict Gender Locking)
#         # Matches formats like "65/M", "47 Years / Male", or "22 Yrs Female"
#         age_sex_match = re.search(r'(?:Age\s*/\s*Sex|Age|Sex)\s*[:-]?\s*(\d+)\s*(?:Y|Years|Yrs|Months)?\s*[/\\|\-]?\s*(Male|Female|M|F)\b', clean_text, re.IGNORECASE)
#         if age_sex_match:
#             metadata["age"] = age_sex_match.group(1).strip()
#             gen_str = age_sex_match.group(2).upper()
#             metadata["gender"] = "MALE" if gen_str.startswith('M') else "FEMALE"

#         # 4. Clean Report Text Body Extraction
#         start_idx = 0
        
#         # Dynamic Table End Detection: Find the last occurrence of a Date or REFERRED BY
#         table_end_pattern = r'(\d{2}[/.-]\d{2}[/.-]\d{4}|REFERRED\s*BY[^\n]*)'
#         matches = list(re.finditer(table_end_pattern, text, re.IGNORECASE))
        
#         if matches:
#             # Cut the text immediately after the last table element found
#             start_idx = matches[-1].end()
        
#         # End before the signature block or advice
#         end_idx = len(text)
#         sig_match = re.search(r'(Reported\s*by|Dr\.|NOT\s*VALID\s*FOR\s*MEDICOLEGAL|Consultant\s*Radiologist|MBBS|ADVICE\s*:)', text, re.IGNORECASE)
#         if sig_match:
#             end_idx = sig_match.start()
            
#         if start_idx < end_idx:
#             report_body = text[start_idx:end_idx].strip()
#         else:
#             report_body = text.strip()
            
#         # Clean up any leading pipes or extra spaces that bled through
#         report_body = re.sub(r'^[\s\|]+', '', report_body).strip()
#         metadata["reportText"] = report_body

#         # 5. Description Extraction 
#         if report_body:
#             # The heading is now guaranteed to be the very first line of the clean body
#             first_line = report_body.split('\n')[0].strip()
            
#             # Clean off prefixes/suffixes
#             desc_clean = re.sub(r'^(?:Examination\s*[:-]?\s*)', '', first_line, flags=re.IGNORECASE)
#             desc_clean = re.sub(r'[:-]+$', '', desc_clean).strip().upper()
            
#             # Failsafe: Ensure we didn't just grab a sub-heading if the main title was missing
#             if desc_clean not in ["TECHNIQUE", "FINDINGS", "OBSERVATION"] and len(desc_clean) > 3:
#                 metadata["description"] = desc_clean

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
            "age": "UNKNOWN",
            "gender": "UNKNOWN",
            "description": "UNKNOWN",
            "reportText": ""
        }
        
        # 1. Name Extraction (Added \n to boundary to catch inline variations)
        name_match = re.search(r'(?:Patient\s*Name|Name)\s*[:-]?\s*([A-Za-z\s\.]+?)(?:Patient\s*ID|ID\s*NO|UHID|Age|Date|Sex|\n|$)', clean_text, re.IGNORECASE)
        if name_match:
            metadata["patientName"] = name_match.group(1).strip().upper()

        # 2. Patient ID Extraction 
        id_match = re.search(r'(?:Patient\s*ID|ID\s*NO|UHID|ID)\s*[:-]?\s*([A-Z0-9\-\s]+?)(?:Age|Date|Sex|Referred|\n|$)', clean_text, re.IGNORECASE)
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
        table_end_pattern = r'(?:DATE[\s:|0-9a-zA-Z/-]+|REFERRED\s*BY[^\n]*)\n'
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
        if report_body:
            # Isolate only the text between the metadata table and the first clinical keyword
            heading_area = re.split(r'\n\s*(?:TECHNIQUE|FINDINGS|OBSERVATION|IMPRESSION)[\s:-]', report_body, flags=re.IGNORECASE)[0]
            
            # Filter out empty lines or lines with only symbols (like the stray hyphen in Image 1)
            desc_lines = [line.strip() for line in heading_area.split('\n') if re.search(r'[a-zA-Z]', line)]
            
            if desc_lines:
                first_line = desc_lines[0] # Guaranteed to be the actual text heading
                
                # Clean prefixes ("Examination:") and suffixes (":", "-", "_")
                desc_clean = re.sub(r'^(?:Examination\s*[:-]?\s*)', '', first_line, flags=re.IGNORECASE)
                desc_clean = re.sub(r'[:-]+$', '', desc_clean).strip().upper()
                
                if desc_clean not in ["TECHNIQUE", "FINDINGS", "OBSERVATION", "IMPRESSION"] and len(desc_clean) > 3:
                    metadata["description"] = desc_clean

        return metadata