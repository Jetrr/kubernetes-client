from kubernetes import client, config
from kubernetes.client.rest import ApiException
import datetime
import json
import yaml
import copy

config.load_kube_config(config_file="C:/Users/a/.kube/config")

batch_v1 = client.BatchV1Api()
core_api = client.CoreV1Api()


def create_job_object(name: str, image: str, command: list[str], args: list[str]):
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

    return job


def create_job(api_instance, job):
    try:
        api_response = api_instance.create_namespaced_job(body=job, namespace="default")
        print("Job created. status='%s'" % str(api_response.status))
    except ApiException as e:
        print("Exception when calling BatchV1Api->create_namespaced_job: %s\n" % e)


def serialize_dates(object):
    if isinstance(object, list):
        for item in object:
            serialize_dates(item)
    elif isinstance(object, dict):
        for key, value in object.items():
            if isinstance(value, datetime.datetime):
                object[key] = value.isoformat()
            elif isinstance(value, list) or isinstance(value, dict):
                serialize_dates(value)


def get_all_jobs(namespace="default"):
    batch_v1 = client.BatchV1Api()
    try:
        jobs = batch_v1.list_namespaced_job(namespace)
        serialize_dates(jobs)
        return jobs
    except ApiException as e:
        print("Exception when calling BatchV1Api->list_namespaced_job: %s\n" % e)


def get_all_pods(namespace="default"):
    try:
        pods = core_api.list_namespaced_pod(namespace)
        serialize_dates(pods)
        return pods
    except ApiException as e:
        print("Exception when calling CoreV1Api->list_namespaced_pod: %s\n" % e)


def get_specific_job(job_name, namespace="default"):
    try:
        job = batch_v1.read_namespaced_job(name=job_name, namespace=namespace)
        serialize_dates(job)
        return job
    except ApiException as e:
        print(f"Exception when calling BatchV1Api->read_namespaced_job: {e}\n")


def get_job_pod_status(job_name, namespace="default"):
    try:
        # Get the job
        job = batch_v1.read_namespaced_job(name=job_name, namespace=namespace)

        # Extract the label selector from the job spec
        selector = job.spec.selector.match_labels
        label_selector = ",".join([f"{k}={v}" for k, v in selector.items()])

        # List pods based on the selector
        pods = core_api.list_namespaced_pod(namespace, label_selector=label_selector)

        for pod in pods.items:
            print(f"Pod Name: {pod.metadata.name}")
            print("Pod Status:", pod.status.phase)
            if pod.status.conditions:
                for condition in pod.status.conditions:
                    print(f"  - {condition.type}: {condition.status}")

            # Check container statuses for more details
            if pod.status.container_statuses:
                for container_status in pod.status.container_statuses:
                    print(f"  Container Name: {container_status.name}")
                    if container_status.state.waiting:
                        print(f"    Waiting: {container_status.state.waiting.reason}")
                    elif container_status.state.running:
                        print("    Running")
                    elif container_status.state.terminated:
                        print(
                            f"    Terminated: {container_status.state.terminated.reason}"
                        )
            print("-------")

        pod = pods.items[0]
        # if
    except client.ApiException as e:
        print(f"Exception when calling Kubernetes API: {e}")

def delete_job(job_name, namespace="default"):
    try:
        batch_v1.delete_namespaced_job(name=job_name, namespace=namespace)
        return True
    except client.ApiException as e:
        print(f"Exception when calling Kubernetes API: {e}")
        return False

def main():
    # Load configuration inside a Pod
    # config.load_incluster_config()

    # Define job parameters
    name = "ml-job-03"  # UNIQUE Name of the job object
    # image = "us-central1-docker.pkg.dev/jetrr-cloud/training-app/training-main-dev:2.0"
    image = "ubuntu"
    command = ["bash", "-c", "sleep 300 && echo done"]
    args = []  # Example arguments

    job = create_job_object(name, image, command, args)
    create_job(batch_v1, job)
    # delete_job(name)

    # jobs = get_all_jobs(batch_v1)
    # print(jobs)
    # print(json.dumps(jobs, indent=2))

    # pods = get_all_pods(core_api)
    # print(pods)

    # job = get_specific_job(batch_v1, name)
    # print(job.status)

    # get_job_pod_status(name)


if __name__ == "__main__":
    main()
