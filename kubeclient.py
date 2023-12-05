from kubernetes.client import client, config
from kubernetes.client.rest import ApiException

class CustomKubernetesClient:
    """
    Custom Kubernetes client Wrapper for creating, deleting, and retrieving job status.
    """
    def __init__(self, config_file="C:/Users/a/.kube/config", namespace="default"):
        config.load_kube_config(config_file=config_file)
        self.batch_v1 = client.BatchV1Api()
        self.core_v1 = client.CoreV1Api()
        self.namespace = namespace

    def create_job(self, name: str, image: str, command: list[str], args: list[str]):
        # Configureate Pod template container
        container = client.V1Container(
            name=name,
            image=image,
            command=command,
            args=args,
            resources=client.V1ResourceRequirements(limits={"nvidia.com/gpu": "1"}),
        )
        # Create and configurate a spec section
        template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(labels={"app": "ml"}),
            spec=client.V1PodSpec(
                restart_policy="Never",
                containers=[container],
                node_selector={"cloud.google.com/gke-accelerator": "nvidia-tesla-t4"},
            ),
        )
        # Create the specification of deployment
        spec = client.V1JobSpec(template=template, backoff_limit=0)
        # Instantiate the job object
        job = client.V1Job(
            api_version="batch/v1",
            kind="Job",
            metadata=client.V1ObjectMeta(name=name),
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
                return "Succeeded"
            if pod.status.phase == "Failed":
                return "Failed"
            if pod.status.phase == "Running":
                return "Started"
            if pod.status.phase == "Pending":
                pod_scheduled = get_condition_type("PodScheduled")
                if pod_scheduled and pod_scheduled["status"] == "False":
                    return "Queued"
                else:
                    return "Pending"
        except client.ApiException as e:
            print(f"Exception when calling Kubernetes API: {e}")

    def delete_job(self, job_name):
        try:
            self.batch_v1.delete_namespaced_job(name=job_name, namespace=self.namespace)
            return True
        except client.ApiException as e:
            print(f"Exception when calling Kubernetes API: {e}")
            return False