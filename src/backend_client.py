import requests
from src.config import Config

class BackendClient:
    def __init__(self):
        self.base_url = Config.BACKEND_BASE_URL
        
    
    def get_processed_paths(self) -> set:
        """Fetches all existing filePaths from the backend to build an O(1) lookup set."""
        try:
            response = requests.get(f"{self.base_url}/patientReports/paths", timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                # If Node.js returns a direct array: ["path1", "path2"]
                if isinstance(data, list):
                    return set(data)
                    
                # If Node.js returns a dictionary: {"paths": ["path1", "path2"]}
                elif isinstance(data, dict):
                    return set(data.get("paths", []))
                    
            return set()
        except Exception as e:
            print(f"❌ Error fetching paths from backend: {e}")
            return set()

    def post_patient_report(self, payload: dict) -> bool:
        """Posts the fully extracted report payload to the backend."""
        try:
            response = requests.post(f"{self.base_url}", json=payload, timeout=10)
            if response.status_code in [200, 201]:
                return True
            print(f"⚠️ Backend rejected payload: {response.status_code} - {response.text}")
            return False
        except Exception as e:
            print(f"❌ Error posting to backend: {e}")
            return False