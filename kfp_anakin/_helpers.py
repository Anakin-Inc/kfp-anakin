"""Functions embedded into compiled components through `additional_funcs`.

KFP copies each function's source into the component, without this module's
globals, so they import what they need inside the function and can only call
each other if the component lists both.
"""


def to_json(value):
    """Convert SDK models (or lists of them) to JSON-serializable data."""
    if isinstance(value, list):
        return [item.model_dump(mode="json") for item in value]
    return value.model_dump(mode="json")


def write_jsonl(artifact, rows):
    """Write `rows` to a Dataset artifact as JSON Lines and record the row count."""
    import json

    with open(artifact.path, "w", encoding="utf-8") as output:
        for row in rows:
            output.write(json.dumps(row, ensure_ascii=False) + "\n")
    artifact.metadata["rows"] = len(rows)


def redact_webhook_secret(monitor):
    """Hide a monitor's webhook signing secret: Kubeflow stores outputs and shows them in the UI."""
    if monitor.get("alert_webhook_secret"):
        monitor["alert_webhook_secret"] = "[redacted: view it in the Anakin dashboard]"
    return monitor


def refuse_if_financial(text):
    """Raise ValueError if `text` looks like a payment or fund transfer.

    The same rule as Anakin's MCP server. Benign writes such as "add to cart"
    pass. Set ANAKIN_ALLOW_FINANCIAL=true on the task to turn it off.
    """
    import os
    import re

    if os.environ.get("ANAKIN_ALLOW_FINANCIAL") == "true":
        return
    # `\b` doesn't break on `_` or `-`, so "amazon_checkout" must become "amazon checkout".
    haystack = re.sub(r"[_-]+", " ", text)
    pattern = (
        r"\b(payments?|pay\s?now|checkout|purchase|place\s?order|buy\s?now|"
        r"wire\s?transfer|remit(?:tance)?|payout|charge\s?card|transfer\s?funds)\b"
    )
    if re.search(pattern, haystack, re.IGNORECASE):
        raise ValueError(
            "kfp-anakin does not run payments or fund transfers, so this action was not run. "
            "Use a read action to look up information, or complete the payment directly on "
            "the site. Set ANAKIN_ALLOW_FINANCIAL=true on the task to turn this check off."
        )
