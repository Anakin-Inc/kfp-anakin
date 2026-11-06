"""Run a task described in plain language in a cloud browser driven by an AI agent."""

from kfp import dsl

from kfp_anakin._helpers import refuse_if_financial
from kfp_anakin._runtime import BASE_IMAGE, RUNTIME_PACKAGES


@dsl.component(
    base_image=BASE_IMAGE,
    packages_to_install=RUNTIME_PACKAGES,
    additional_funcs=[refuse_if_financial],
)
def browser_task(
    prompt: str,
    url: str = None,
    session_id: str = None,
    max_steps: int = None,
    timeout_ms: int = None,
    output_schema: dict = None,
) -> dict:
    """Run a task described in plain language in a cloud browser driven by an AI agent.

    The agent navigates, clicks, types and extracts. Use it for multi-step flows
    scrape_url can't do and no Wire action covers (Wire actions are faster and cheaper,
    so try wire_discover first). Runs are capped at about 330 seconds server-side. For
    logged-in tasks pass session_id; never put passwords in prompt. Turn caching off on
    this task if it changes anything. Refuses payment or fund-transfer tasks (raises
    ValueError).

    Args:
        prompt: What to do and what to return.
        url: Start here. Omit to let the agent follow URLs in the prompt.
        session_id: Saved browser session to run as a logged-in user.
        max_steps: Maximum agent steps.
        timeout_ms: Task timeout in milliseconds.
        output_schema: JSON Schema the returned result should follow.

    Returns:
        success, result, steps_taken, iterations, cached, duration_ms and run_id.
    """
    import os
    import time

    import httpx

    refuse_if_financial(f"{prompt} {url or ''}")
    api_key = os.environ.get("ANAKIN_API_KEY")
    if not api_key:
        raise ValueError(
            "browser_task needs an Anakin API key in ANAKIN_API_KEY. Get a key at "
            "https://anakin.io/dashboard (the free tier needs no card)."
        )

    def call(client, method, path, **kwargs):
        response = client.request(method, path, **kwargs)
        if response.is_error:
            raise RuntimeError(f"{method} {path} failed ({response.status_code}): {response.text}")
        return response.json()

    body = {"prompt": prompt, "async": True}
    optional = {
        "url": url,
        "session_id": session_id,
        "max_steps": max_steps,
        "timeout_ms": timeout_ms,
        "output_schema": output_schema,
    }
    body.update({k: v for k, v in optional.items() if v is not None})

    with httpx.Client(
        base_url="https://api.anakin.io/v1", headers={"X-API-Key": api_key}, timeout=60.0
    ) as client:
        accepted = call(client, "POST", "/ai/evaluate", json=body)
        workflow_id = accepted.get("workflow_id")
        resolved = accepted
        if workflow_id:
            # Runs are capped at ~330s server-side, so poll for up to 6 minutes.
            for _ in range(120):
                job = call(client, "GET", f"/ai/jobs/{workflow_id}")
                if job.get("status") in {"completed", "failed", "timed_out"}:
                    break
                time.sleep(3.0)
            else:
                raise TimeoutError(f"Browser task {workflow_id} did not finish in 6 minutes.")
            if job["status"] != "completed":
                # A failed run reports its reason in result.result, not in error.
                reason = job.get("error") or (job.get("result") or {}).get("result") or "unknown"
                raise RuntimeError(f"Browser task {job['status']}: {reason}")
            resolved = job.get("result") or job

    steps = resolved.get("steps")
    return {
        "success": resolved.get("success"),
        "result": resolved.get("result"),
        "steps_taken": len(steps) if isinstance(steps, list) else None,
        "iterations": resolved.get("iterations"),
        "cached": resolved.get("cached"),
        "duration_ms": resolved.get("duration_ms"),
        "run_id": resolved.get("run_id"),
    }
