# Custom Kubernetes Client Wrapper

Custom Kubernetes client Wrapper for creating, deleting, and retrieving job status.

## Kubernetes cli setup for getting cluster and it's credentials
gcloud components install kubectl

gcloud components install gke-gcloud-auth-plugin

gcloud container clusters get-credentials gpu-cluster-auto --zone us-central1-f

## Making a node unschedulable and configure it to not be scaled down for logging
 kubectl cordon `node_name`

 kubectl annotate node `node_name` cluster-autoscaler.kubernetes.io/scale-down-disabled=true
 

## Client Setup

1. Copy `kubeclient.py` to your working Directory
2. Install kubernetes packages `pip install kubernetes`
3. Import Client and Use Methods

```py
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from kubeclient import CustomKubernetesClient
import json
from uuid import uuid4

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

job_id=str(uuid4())

# Create a Job
client.create_job(
  name=job_id
  image="path/to/training-job/image:tag"
  command=["python3", "training.py"]
  args=[]
)

# delete a job
client.delete_job(job_id)

# Retrive Job Status
client.get_job_status(job_id)
# Response = Literal['completed', 'failed', 'started', 'pending', 'unspecified']

events = client.get_all_events()

# Print the JSON output
print(json.dumps(events, indent=2))
```

**Note:** You do not need to set up kubernetes tools if the cluster is already up and running.

![GKE](assets/GKE-architechture.svg)

## Setting up Kubernetes Tools

Enable Container APIs if you haven't: `gcloud services enable container.googleapis.com`

1. Make sure to have `kubectl` installed.
2. You may install kubectl if you have gcloud by `gcloud components install kubectl`
3. Install gke plugin for kubectl `gcloud components install gke-gcloud-auth-plugin`

## Working with Kubernetes Cluster on GKE using `Kubectl`

| Argument                      | Description                                                                                                                                                                                                                      |
|-------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `gpu-cluster-auto`            | The name of the Kubernetes cluster to be created.                                                                                                                                                                                |
| `--zone us-central1-f`        | Specifies the zone where the cluster will be located. This is a specific geographic location within a region.                                                                                                                    |
| `--num-nodes=1`               | Sets the number of nodes for the cluster's default node pool. In this case, it's set to 1 node.                                                                                                                                  |
| `--machine-type=n1-standard-4`| Defines the type of machine to use for the nodes. `n1-standard-4` means each node will have 4 virtual CPUs and 15 GB of memory.                                                                                                  |
| `--accelerator type="nvidia-tesla-t4,count=1,gpu-driver-version=default"` | Requests an NVIDIA Tesla T4 GPU to be attached to each node, with the default GPU driver version.                                                                                                                                |
| `--scopes`                    | Defines the set of Google Cloud Platform (GCP) service accounts permissions for the nodes. The listed scopes allow the cluster to interact with other GCP services like storage, logging, monitoring, etc.                        |
| `--min-nodes 1`               | The minimum number of nodes for the cluster's node pool. Autoscaling won't scale below this number.                                                                                                                              |
| `--max-nodes 10`              | The maximum number of nodes for the cluster's node pool. Autoscaling won't scale above this number.                                                                                                                              |
| `--enable-autoscaling`        | Enables the cluster to automatically adjust the number of nodes based on the workload.                                                                                                                                            |
| `--autoscaling-profile optimize-utilization` | Sets the autoscaling profile to 'optimize-utilization', which means the autoscaler will prioritize keeping the utilization high over keeping spare capacity.                                                                     |

## The Importance of Setting the `devstorage.full_control` Scope for Write Access in Google Cloud Storage

It's crucial to highlight the scope `https://www.googleapis.com/auth/devstorage.full_control`. By default, the permissions for accessing Google Cloud Storage are set to read-only. However, if we want the applications running on our Kubernetes pods to be able to write data to Google Cloud Storage, we need to grant them more than just read permissions.

This is where the `devstorage.full_control` scope comes into play. By including this scope, we give the virtual machines (VMs) that make up our Kubernetes nodes the necessary permissions to write to Google Cloud Storage. This is a permission setting at the VM level, which is different from the permissions associated with a service account key file.

Even if the service account used by `gsutil` (a command-line tool for Google Cloud Storage) has all the required permissions to write to storage, the operation will fail if the VM itself doesn't have the write access granted. This is because the VM's scope acts as a gatekeeper, determining what the service account is allowed to do on that particular machine.

In summary, without setting the `devstorage.full_control` scope, our jobs running on the Kubernetes pods will not be able to write their results back to any storage, despite the service account's capabilities. Therefore, it's essential to explicitly define this scope to ensure that our applications have the necessary permissions to perform write operations on Google Cloud Storage.

### Create GKS Cluster

**Bash:**
```bash
gcloud container clusters create gpu-cluster-auto \
  --zone us-central1-f \
  --machine-type=n1-standard-4 \
  --accelerator type="nvidia-tesla-t4,count=1,gpu-driver-version=default" \
  --scopes "https://www.googleapis.com/auth/devstorage.full_control",\
"https://www.googleapis.com/auth/logging.write",\
"https://www.googleapis.com/auth/monitoring",\
"https://www.googleapis.com/auth/service.management.readonly",\
"https://www.googleapis.com/auth/servicecontrol",\
"https://www.googleapis.com/auth/trace.append" \
  --num-nodes 1 \
  --min-nodes 1 \
  --max-nodes 10 \
  --enable-autoscaling \
  --autoscaling-profile optimize-utilization \
  --enable-image-streaming
``` 

**PowerShell:**
```powershell
gcloud container clusters create gpu-cluster-auto `
  --zone us-central1-f `
  --machine-type=n1-standard-4 `
  --accelerator type="nvidia-tesla-t4,count=1,gpu-driver-version=default" `
  --scopes "https://www.googleapis.com/auth/devstorage.full_control,https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/monitoring,https://www.googleapis.com/auth/service.management.readonly,https://www.googleapis.com/auth/servicecontrol,https://www.googleapis.com/auth/trace.append" `
  --num-nodes 1 `
  --min-nodes 1 `
  --max-nodes 10 `
  --enable-autoscaling `
  --autoscaling-profile optimize-utilization `
  --enable-image-streaming
```

### Retrieve Cluster to Kubectl

Get Cluster Credentials to interact with kubectl

```bash
gcloud container clusters get-credentials gpu-cluster --zone us-central-f
```

To view Clusters: `gcloud container clusters list`

To View the Nodes: `kubectl get nodes`

To run a sample job: `kubectl apply -f ml-job.yaml`

To View the Running Nodes: `kubectl get nodes`

To View the Running Pods: `kubectl get pods`

To View the Running Jobs: `kubectl get jobs`

To View the logs of a pod: `kubectl logs <pod name>`

To Connect to a Particular Pod: `kubectl exec -it <pod name> -- /bin/bash`

To get all Events: `kubectl get events --sort-by='.metadata.creationTimestamp'`

### Create a Multi GPU Cluster for Distributed Inference

Each Node has Multiple GPUs. For example 4 GPUs per node for Distributed Inference.

```powershell
gcloud container clusters create multi-gpu `
  --zone us-central1-f `
  --machine-type=n1-highcpu-32 `
  --accelerator type="nvidia-tesla-t4,count=4,gpu-driver-version=default" `
  --scopes "https://www.googleapis.com/auth/devstorage.full_control,https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/monitoring,https://www.googleapis.com/auth/service.management.readonly,https://www.googleapis.com/auth/servicecontrol,https://www.googleapis.com/auth/trace.append" `
  --num-nodes 1 `
  --min-nodes 1 `
  --max-nodes 25 `
  --enable-autoscaling `
  --autoscaling-profile optimize-utilization `
  --enable-image-streaming
```

### Create Node Pool (Optional)

**Bash:**

```bash
gcloud container node-pools create gpu-pool-auto \
  --cluster=gpu-cluster-auto \
  --zone=us-central1-f \
  --machine-type=n1-standard-4 \
  --accelerator=type=nvidia-tesla-t4,count=1,gpu-driver-version=default \
  --scopes="https://www.googleapis.com/auth/devstorage.full_control",\
"https://www.googleapis.com/auth/logging.write",\
"https://www.googleapis.com/auth/monitoring",\
"https://www.googleapis.com/auth/service.management.readonly",\
"https://www.googleapis.com/auth/servicecontrol",\
"https://www.googleapis.com/auth/trace.append" \
  --num-nodes=1 \
  --min-nodes=1 \
  --max-nodes=10 \
  --enable-autoscaling \
  --autoscaling-profile=optimize-utilization \
  --enable-image-streaming
```

**PowerShell:**

```powershell
gcloud container node-pools create gpu-pool-auto `
  --cluster=gpu-cluster-auto `
  --zone=us-central1-f `
  --machine-type=n1-standard-4 `
  --accelerator=type=nvidia-tesla-t4,count=1,gpu-driver-version=default `
  --scopes "https://www.googleapis.com/auth/devstorage.full_control,https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/monitoring,https://www.googleapis.com/auth/service.management.readonly,https://www.googleapis.com/auth/servicecontrol,https://www.googleapis.com/auth/trace.append" `
  --num-nodes=1 `
  --min-nodes=1 `
  --max-nodes=10 `
  --enable-autoscaling `
  --autoscaling-profile=optimize-utilization `
  --enable-image-streaming
```

<!-- Currently Under Working -->

## Add Flags for Image Streaming and caching docker images for faster starting time for new nodes

```bash
gcloud container clusters create CLUSTER_NAME \
  --zone=us-central1-f \
  --image-type="COS_CONTAINERD"
  --enable-image-streaming \
```

### verify the image streaming

Get the Kubernetes event log to see image pull events:

```bash
kubectl get events --all-namespaces
```

The output is similar to the following:

|NAMESPACE  |LAST SEEN  |TYPE    |REASON          |OBJECT                                                 |MESSAGE
|---------  |---------  |----    |------          |------                                                 |---------
|default    |11m        |Normal  |Pulling         |pod/frontend-64bcc69c4b-pgzgm                          | Pulling image `"us-docker.pkg.dev/google-samples/containers/gke/gb-frontend:v5"`
|default    |11m        |Normal  |Pulled          |pod/frontend-64bcc69c4b-pgzgm                          | Successfully pulled image `"us-docker.pkg.dev/google-samples/containers/gke/gb-frontend:v5"` in 1.536908032s
|default    |11m        |Normal  |ImageStreaming  |node/gke-riptide-cluster-default-pool-f1552ec4-0pjv    | Image `us-docker.pkg.dev/google-samples/containers/gke/gb-frontend:v5` is backed by image streaming.

## Working with A100 Cluster with multi-instance GPUs enabled (GPU slicing)

```powershell
gcloud container clusters create power-cluster `
  --zone us-central1-f `
  --machine-type=a2-highgpu-1g `
  --accelerator type="nvidia-tesla-a100,count=1,gpu-partition-size=1g.5gb,gpu-driver-version=default" `
  --scopes "https://www.googleapis.com/auth/devstorage.full_control,https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/monitoring,https://www.googleapis.com/auth/service.management.readonly,https://www.googleapis.com/auth/servicecontrol,https://www.googleapis.com/auth/trace.append" `
  --num-nodes 1 `
  --min-nodes 1 `
  --max-nodes 7 `
  --enable-autoscaling `
  --autoscaling-profile=optimize-utilization `
  --enable-image-streaming
```



## Pulling Training image in cpu node to be used for image streaming

- `kubectl apply -f image-prepull-job.yaml` run this command with the necessary configs of node selector in the yaml file to run an image pre-pull job on a cpu node. This will cache images on the cpu node that can be used by image streaming to quickly deploy the image on a new gpu node 
