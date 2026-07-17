import os
import requests
import urllib.parse
from pathlib import Path

PB_BASE_URL = os.environ.get("PB_BASE_URL", "https://unf.wavelynxtech.com/api")
PB_COLLECTION_ID = os.environ.get("PB_COLLECTION_ID", "kceqp1an569q6sp")
PB_ADMIN_TOKEN = os.environ.get(
    "PB_ADMIN_TOKEN",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3ODUxMTUzMTIsImlkIjoic2VvNHN2bHc1Njdhcmk0IiwidHlwZSI6ImFkbWluIn0.2QZ07ip9yRe0yHQBEe8bMqpCmrPxe_fXoQD3ZgyUoTs"
)


class PocketBaseClient:
    def __init__(
        self, 
        base_url: str = PB_BASE_URL, 
        collection_id: str = PB_COLLECTION_ID, 
        admin_token: str = PB_ADMIN_TOKEN
    ):
        self.base_url = base_url.rstrip("/")
        self.collection_id = collection_id
        self.admin_token = admin_token

    def _get_headers(self) -> dict:
        return {"Authorization": f"Bearer {self.admin_token}"}

    def check_active_token(self, token_name: str) -> str | None:
        """
        Queries PocketBase to find if an identical token name exists with status = "ACTIVE".
        Returns the token string if found, otherwise returns None.
        """
        filter_query = f'name = "{token_name}" && status = "ACTIVE"'
        encoded_filter = urllib.parse.quote(filter_query)
        
        url = f"{self.base_url}/collections/{self.collection_id}/records?filter={encoded_filter}"
        
        try:
            print(f"[PocketBase Cache] Checking for existing active token: '{token_name}'...")
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            if response.status_code == 200:
                items = response.json().get("items", [])
                if items:
                    token_str = items[0].get("token") or items[0].get("id")
                    print(f"[PocketBase Cache] Found existing active token: {token_str}")
                    return token_str
        except Exception as e:
            print(f"[PocketBase Cache Warning] Query failed: {e}")
            
        return None

    def create_token_record(self, token_name: str, local_bin_path: Path) -> str:
        """
        Uploads binary asset and registers a new active token record in PocketBase.
        """
        url = f"{self.base_url}/collections/{self.collection_id}/records"
        
        with open(local_bin_path, "rb") as f:
            multipart_payload = {
                "name": (None, token_name),
                "status": (None, "ACTIVE"),
                "card": (local_bin_path.name, f, "application/octet-stream")
            }
            print(f"[PocketBase] Registering token '{token_name}' with asset '{local_bin_path.name}'...")
            response = requests.post(url, headers=self._get_headers(), files=multipart_payload, timeout=30)
            
        if response.status_code in [200, 201]:
            data = response.json()
            token_string = data.get("token") or data.get("id")
            print(f"[PocketBase] Success! Created Token Record ID: {token_string}")
            return token_string
        else:
            raise Exception(f"PocketBase Registration Failed ({response.status_code}): {response.text}")