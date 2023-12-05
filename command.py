inference_args = [
    "--model_path='/root/model'",
    "--save_path='/root/output'",
    "--prompt_file='/root/prompt.json'",
    "--gender='male'",
]

inference_cmd = ["python3", "infer-dreambooth.py"] + inference_args

cmd = [
    "mkdir -p model output",
    "gsutil -m cp -r gs://envison-us-central1-dev/5893016f-2e65-470c-9835-492d038e5a18/model .",
    "gsutil cp gs://configs-us-central1/prompts/prompts-v4.json prompt.json",
    " ".join(inference_cmd),
    "gsutil -m cp -r output gs://envison-us-central1-dev/aa-test/output",
]

joined = " && ".join(cmd)

print(joined)
