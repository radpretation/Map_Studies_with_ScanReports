
import os
import traceback
from src.config import Config
from src.graph_client import GraphClient
from src.backend_client import BackendClient
from src.regex_engine import RegexEngine
from src.body_classifier import BodyClassifier

def main():
    print("🚀 Starting Data Ingestion Engine...")
    
    backend = BackendClient()
    graph = GraphClient()
    
    # 1. Fetch Backend Truth
    print("📦 Fetching existing file paths from backend...")
    processed_paths = backend.get_processed_paths()
    print(f"✅ Found {len(processed_paths)} existing records.")
    
    # 2. Load State (Delta Token)
    delta_link = None
    if os.path.exists(Config.DELTA_TOKEN_FILE):
        with open(Config.DELTA_TOKEN_FILE, 'r') as f:
            delta_link = f.read().strip()
            
    # 3. Query Microsoft Graph
    print("🔍 Fetching delta changes from OneDrive...")
    try:
        # The graph_client already handles pagination automatically
        items, new_delta_link = graph.get_delta_changes(delta_link)
    except Exception as e:
        print(f"❌ Fatal error fetching Delta changes: {e}")
        return # Exit safely if we can't talk to Microsoft
        
    print(f"📥 Received {len(items)} items from Delta Query.")
    
    processed_count = 0
    error_count = 0
    
    # 4. Filter & Process Items Safely
    for item in items:
        # ⬇️ THE SHIELD: If anything inside this loop fails, it won't crash the script
        try:
            # Ignore folders or files deleted/moved out of scope
            if 'file' not in item or '@removed' in item:
                continue  
                
            filename = item.get('name', 'UNKNOWN_FILE')
            file_id = item.get('id')
            download_url = item.get('@microsoft.graph.downloadUrl')
            parent_path = item.get('parentReference', {}).get('path', '')
            
            # Construct the absolute path
            absolute_cloud_path = f"{parent_path}/{filename}"
            created_date = item.get('lastModifiedDateTime', item.get('createdDateTime'))
            
            # O(1) Deduplication Check (Skips the file if we've already processed it)
            if absolute_cloud_path in processed_paths:
                continue
                
            print(f"\n📄 Processing new file: {filename}")
            
            # Download and Extract
            temp_path = graph.download_file(download_url, file_id, filename)
            if not temp_path:
                print(f"⚠️ Skipping {filename}: Download or PDF conversion failed.")
                error_count += 1
                continue
                
            raw_text = RegexEngine.extract_text(temp_path)
            
            # Safely clean up the temp file
            try:
                os.remove(temp_path)
            except Exception as e:
                print(f"⚠️ Could not delete temp file {temp_path}: {e}")
            
            if not raw_text.strip():
                print(f"⚠️ Skipping {filename}: No readable text extracted.")
                error_count += 1
                continue
                
            # --- The Extraction Pipeline ---
            # Automatically split the document if multiple patients are found
            reports = RegexEngine.split_into_reports(raw_text)
            
            for idx, single_report_text in enumerate(reports):
                if not single_report_text.strip(): 
                    continue
                
                # 1. Parse Document Data completely from the specific report chunk
                doc_metadata = RegexEngine.parse_document_text(single_report_text)
                
                # 2. Determine Institute
                institute_name = RegexEngine.extract_institute_from_path(parent_path)
                
                # 3. Normalize ID based on Institute Rules
                normalized_id = RegexEngine.normalize_patient_id(doc_metadata["patientID"], institute_name)
                
                # 4. Classify Body Part
                body_part = BodyClassifier.get_body_part(doc_metadata["description"], single_report_text)
                
                # Generate unique filePath for sub-reports to prevent DB overwrites
                unique_file_path = absolute_cloud_path if len(reports) == 1 else f"{absolute_cloud_path}#part{idx+1}"
                
                # Construct the Output Payload
                payload = {
                    "filePath": unique_file_path,
                    "fileCreatedDate": created_date,
                    "instituteName": institute_name,
                    "patientID": normalized_id,
                    "UHID": doc_metadata.get("UHID", "UNKNOWN"), # Captures UHID
                    "patientName": doc_metadata["patientName"],
                    "age": doc_metadata["age"],
                    "gender": doc_metadata["gender"],
                    "description": doc_metadata["description"],
                    "bodyPart": body_part,
                    "reportText": doc_metadata["reportText"],
                    "reportStatus": "REPORT_RECEIVED"
                }
                
                print(f"PAYLOAD (Part {idx+1}/{len(reports)})-->>", payload)
                
                # Dispatch to Backend
                if backend.post_patient_report(payload):
                    processed_count += 1
                else:
                    print(f"⚠️ Backend rejected payload for {filename} (Part {idx+1})")
                    error_count += 1
            
            # Add to set locally to prevent duplicate POSTs in the same run
            processed_paths.add(absolute_cloud_path) 
                
        except Exception as e:
            print(f"❌ Unhandled error processing {filename}: {e}")
            traceback.print_exc() 
            error_count += 1
            continue 
            
    # 5. Save State for Next Execution
    if new_delta_link:
        with open(Config.DELTA_TOKEN_FILE, 'w') as f:
            f.write(new_delta_link)
        print("\n💾 Saved new Delta Token.")
        
    print(f"🎉 Ingestion Complete. Processed: {processed_count} | Errors/Skipped: {error_count}")

if __name__ == "__main__":
    main()