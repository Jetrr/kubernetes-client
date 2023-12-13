from google.oauth2 import service_account
from google.auth.transport.requests import Request
from kubeclient import CustomKubernetesClient
import json

credentials = service_account.Credentials.from_service_account_file(
    filename="keyfile.json",
    scopes=["https://www.googleapis.com/auth/cloud-platform"],
)
# Refresh the token
credentials.refresh(Request())

client = CustomKubernetesClient(credentials=credentials)

events = client.get_all_events()

# Print the JSON output
print(json.dumps(events, indent=2))