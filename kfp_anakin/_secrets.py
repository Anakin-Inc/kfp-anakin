"""Inject the Anakin API key into a task from a Kubernetes secret."""

from kfp import dsl, kubernetes


def with_api_key(
    task: dsl.PipelineTask, secret_name: str = "anakin", secret_key: str = "api-key"
) -> dsl.PipelineTask:
    """Set ANAKIN_API_KEY on `task` from a Kubernetes secret, and return the task.

    Create the secret in the namespace your pipelines run in:
    `kubectl create secret generic anakin --from-literal=api-key=ask_... -n <namespace>`

    Args:
        task: The task to add the key to.
        secret_name: Name of the Kubernetes secret.
        secret_key: Key inside the secret that holds the API key.
    """
    return kubernetes.use_secret_as_env(
        task, secret_name=secret_name, secret_key_to_env={secret_key: "ANAKIN_API_KEY"}
    )
