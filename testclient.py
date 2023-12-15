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

client = CustomKubernetesClient(
  credentials=credentials
  cluster_name="gpu-cluster-auto",
  cluster_location="us-central1-f"
  project_id="jetrr-cloud"
)

# events = client.get_all_events()

print(client.get_job_status("ec84a81b-0ffd-42e4-af4e-77762d33057a"))

# Print the JSON output
# print(json.dumps(events, indent=2))