from kubernetes import client as k8s_client, config as k8s_config
from kubernetes.client.rest import ApiException
from google.cloud import container_v1
from google.auth.transport.requests import Request
from tempfile import NamedTemporaryFile
import base64
import json
import datetime

PROJECT_ID="jetrr-cloud"
CLUSTER_ZONE="us-central1-f"
CLUSTER_NAME="gpu-cluster-auto"

class CustomKubernetesClient:
    """
    Custom Kubernetes client wrapper for managing Kubernetes jobs.
    
    This class provides methods to create, delete, and retrieve the status of Kubernetes jobs,
    as well as listing all events in a given namespace.
    
    Attributes:
        batch_v1 (k8s_client.BatchV1Api): The client for interacting with the Kubernetes Batch API.
        core_v1 (k8s_client.CoreV1Api): The client for interacting with the Kubernetes Core API.
        namespace (str): The Kubernetes namespace in which operations will be performed.
    """
    def __init__(self, credentials, namespace="default"):
        """
        Initializes the CustomKubernetesClient with the provided credentials and namespace.
        
        Args:
            credentials: The credentials object containing the token for Kubernetes API authentication.
            namespace (str): The Kubernetes namespace to operate in. Defaults to "default".
        Example:
            ```python
            credentials = service_account.Credentials.from_service_account_file(
                filename="keyfile.json",
                scopes=["https://www.googleapis.com/auth/cloud-platform"],
            )
            # Refresh the token
            credentials.refresh(Request())

            client = CustomKubernetesClient(credentials=credentials)
            ```
        """
        token = credentials.token
        # Create the Cluster Manager Client
        cluster_client = container_v1.ClusterManagerClient(
            credentials=credentials
        )
        request = container_v1.GetClusterRequest(
            name=f'projects/{PROJECT_ID}/locations/{CLUSTER_ZONE}/clusters/{CLUSTER_NAME}'
        )
        response = cluster_client.get_cluster(request)

        endpoint = response.endpoint
        certificate_authority = response.master_auth.cluster_ca_certificate

        configuration = k8s_client.Configuration()
        configuration.host = f'https://{endpoint}'
        configuration.api_key['authorization'] = 'Bearer ' + token
        configuration.verify_ssl = True
        # Provide a path to a valid certificate authority file.
        with NamedTemporaryFile(delete=False) as cert:
            cert.write(base64.b64decode(certificate_authority))
            configuration.ssl_ca_cert = cert.name

        k8s_client.Configuration.set_default(configuration)
        self.batch_v1 = k8s_client.BatchV1Api()
        self.core_v1 = k8s_client.CoreV1Api()
        self.namespace = namespace

    def _datetime_json_serializer(self, obj):
        """
        A JSON serializer for datetime objects.
        
        Args:
            obj: The object to serialize.
            
        Returns:
            str: The ISO format string if the object is a datetime.
            
        Raises:
            TypeError: If the object is not a datetime instance.
        """
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        raise TypeError("Type %s not serializable" % type(obj))

    def create_job(self, name: str, image: str, command: list[str], args: list[str]):
        """
        Creates a Kubernetes job with the specified parameters.
        
        Args:
            name (str): The name of the job to create.
            image (str): The Docker image to use for the job's container.
            command (list[str]): The command to run in the container.
            args (list[str]): The arguments to pass to the command.
            
        Returns:
            bool: True if the job was created successfully, False otherwise.
        Example:
            ```python
            client = CustomKubernetesClient(credentials=credentials)
            job_id=str(uuid4())
            client.create_job(
                name=job_id
                image="path/to/training-job/image:tag"
                command=["python3", "training.py"]
                args=[]
            )
            ```
        """
        # Configureate Pod template container
        container = k8s_client.V1Container(
            name=name,
            image=image,
            command=command,
            args=args,
            resources=k8s_client.V1ResourceRequirements(limits={"nvidia.com/gpu": "1"}),
        )
        # Create and configurate a spec section
        template = k8s_client.V1PodTemplateSpec(
            metadata=k8s_client.V1ObjectMeta(labels={"app": "ml"}),
            spec=k8s_client.V1PodSpec(
                restart_policy="Never",
                containers=[container],
                node_selector={"cloud.google.com/gke-accelerator": "nvidia-tesla-t4"},
            ),
        )
        # Create the specification of deployment
        spec = k8s_client.V1JobSpec(template=template, backoff_limit=0)
        # Instantiate the job object
        job = k8s_client.V1Job(
            api_version="batch/v1",
            kind="Job",
            metadata=k8s_client.V1ObjectMeta(name=name),
            spec=spec,
        )

        try:
            api_response = self.batch_v1.create_namespaced_job(body=job, namespace=self.namespace)
            print("Job created. status='%s'" % str(api_response.status))
            return True
        except ApiException as e:
            print("Exception when calling BatchV1Api->create_namespaced_job: %s\n" % e)
            return False

    def get_job_status(self, job_name: str):
        """
        Retrieves the status of the specified Kubernetes job.
        
        Args:
            job_name (str): The name of the job to retrieve the status for.
            
        Returns:
            str: The status of the job, which can be `completed`, `failed`, `started`, `pending`, or `unspecified`.
        """
        try:
            # Get the job
            job = self.batch_v1.read_namespaced_job(name=job_name, namespace=self.namespace)

            # Extract the label selector from the job spec
            selector = job.spec.selector.match_labels
            label_selector = ",".join([f"{k}={v}" for k, v in selector.items()])

            # List pods based on the selector
            pods = self.core_v1.list_namespaced_pod(self.namespace, label_selector=label_selector)
            pod = pods.items[0]

            def get_condition_type(condition_type: str):
                conditions = pod.status.conditions
                if conditions == None:
                    return None
                condition_dict = next((x for x in conditions if x['type'] == condition_type), None)
                return condition_dict

            if pod.status.phase == "Succeeded":
                return "completed"
            if pod.status.phase == "Failed":
                return "failed"
            if pod.status.phase == "Running":
                return "started"
            if pod.status.phase == "Pending":
                pod_scheduled = get_condition_type("PodScheduled")
                if pod_scheduled and pod_scheduled["status"] == "False":
                    return "pending" # since 'queued case isn't being handled, we'll just return 'pending' for now

            return "pending"
        except k8s_client.ApiException as e:
            print(f"Exception when calling Kubernetes API: {e}")
            return "unspecified"

    def delete_job(self, job_name):
        """
        Deletes the specified Kubernetes job.
        
        Args:
            job_name (str): The name of the job to delete.
            
        Returns:
            `bool`: True if the job was deleted successfully, False otherwise.
        """
        try:
            self.batch_v1.delete_namespaced_job(name=job_name, namespace=self.namespace)
            return True
        except k8s_client.ApiException as e:
            print(f"Exception when calling Kubernetes API: {e}")
            return False
        
    def get_all_events(self):
        """
        Retrieves all events from the Kubernetes namespace.
        
        Returns:
            list: A list of event dictionaries sorted by creation timestamp, or None if an error occurs.
        
        Example:
            ```
            [{
                "time": "2023-12-13T10:16:45+00:00",
                "namespace": "default",
                "name": "b209b665-d275-4b43-b3a7-07f70cc8ac69.17a05cb84228234e",
                "reason": "Completed",
                "message": "Job completed"
            }]
            ```
        """
        try:
            events = self.core_v1.list_namespaced_event(self.namespace)
            # Sort the events by creation timestamp
            sorted_events = sorted(events.items, key=lambda x: x.metadata.creation_timestamp)
            # Convert the sorted events to JSON
            events_json = []

            for event in sorted_events:
                event_dict = {
                    "time": event.metadata.creation_timestamp,
                    "namespace": event.metadata.namespace,
                    "name": event.metadata.name,
                    "reason": event.reason,
                    "message": event.message
                }
                events_json.append(event_dict)

            # Serialize the list of event dictionaries to JSON
            json_output = json.dumps(
                events_json, 
                default=self._datetime_json_serializer, 
            )

            return json.loads(json_output)

        except k8s_client.ApiException as e:
            print(f"Exception when calling Kubernetes API: {e}")
            return None