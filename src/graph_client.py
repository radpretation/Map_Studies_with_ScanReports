import os
import tempfile
import requests
from src.config import Config

class GraphClient:
    def __init__(self):
        self.access_token = self._get_access_token()
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json"
        }
        
    def _get_access_token(self) -> str:
        url = f"https://login.microsoftonline.com/{Config.TENANT_ID}/oauth2/v2.0/token"
        payload = {
            "client_id": Config.CLIENT_ID,
            "client_secret": Config.CLIENT_SECRET,
            "refresh_token": Config.REFRESH_TOKEN,
            "grant_type": "refresh_token"
        }
        response = requests.post(url, data=payload)
        response.raise_for_status()
        return response.json()["access_token"]
        
    def get_delta_changes(self, delta_link: str = None) -> tuple:
        """Fetches the delta changes. Returns a tuple of (items_list, new_delta_link)"""
        # If no delta_link exists, start a fresh query at the root folder
        if not delta_link:
            url = "https://graph.microsoft.com/v1.0/me/drive/root:/Radpretation/Reports:/delta"
        else:
            url = delta_link
            
        items = []
        while url:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            items.extend(data.get("value", []))
            
            # Microsoft returns nextLink if there are more pages of changes
            if "@odata.nextLink" in data:
                url = data["@odata.nextLink"]
            else:
                # If nextLink is gone, deltaLink is provided for the next script run
                new_delta = data.get("@odata.deltaLink")
                break
                
        return items, new_delta
        
    def download_file(self, download_url: str, file_id: str, filename: str) -> str:
        """Downloads file to a temporary location. Forces PDF conversion for legacy .doc"""
        is_legacy_doc = filename.lower().endswith('.doc') and not filename.lower().endswith('.docx')
        ext = ".pdf" if is_legacy_doc else f".{filename.split('.')[-1]}"
        
        # Bypassing the unreliable 'downloadUrl' and using the guaranteed /content endpoint
        if is_legacy_doc:
            url = f"https://graph.microsoft.com/v1.0/me/drive/items/{file_id}/content?format=pdf"
        else:
            url = f"https://graph.microsoft.com/v1.0/me/drive/items/{file_id}/content"
            
        try:
            # allow_redirects=True is required for the /content endpoint
            res = requests.get(url, headers=self.headers, timeout=20, allow_redirects=True)
            
            if res.status_code == 200:
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
                temp_file.write(res.content)
                temp_file.close()
                return temp_file.name
            else:
                print(f"❌ Microsoft API rejected download for {filename} (Status: {res.status_code})")
                
        except Exception as e:
            print(f"❌ Request Error downloading {filename}: {e}")
            
        return None