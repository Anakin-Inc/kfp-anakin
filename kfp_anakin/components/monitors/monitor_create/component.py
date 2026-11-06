"""Create a scheduled website monitor."""

from kfp import dsl

from kfp_anakin._helpers import redact_webhook_secret, to_json
from kfp_anakin._runtime import BASE_IMAGE, RUNTIME_PACKAGES


@dsl.component(
    base_image=BASE_IMAGE,
    packages_to_install=RUNTIME_PACKAGES,
    additional_funcs=[to_json, redact_webhook_secret],
)
def monitor_create(
    url: str,
    interval_minutes: int,
    scope: str = "page",
    watch_mode: str = "full_page",
    watch_format: str = "markdown",
    output_schema: dict = None,
    ai_mode: bool = False,
    ai_goal: str = None,
    use_browser: bool = False,
    country: str = "us",
    session_id: str = None,
    is_active: bool = True,
    expires_at: str = None,
    alert_webhook_url: str = None,
    alert_emails: str = None,
    max_pages: int = None,
    max_depth: int = None,
    include_patterns: list = None,
    exclude_patterns: list = None,
    wire_action_id: str = None,
    wire_catalog_slug: str = None,
    wire_credential_id: str = None,
    wire_params: dict = None,
    wire_watch_paths: list = None,
) -> dict:
    """Create a scheduled website monitor.

    Checks url every interval_minutes (minimum 15) and records a change when the content
    differs, optionally alerting a webhook or email. See https://anakin.io/pricing for
    the credit cost per check and the active-monitor limit on each plan.

    Creating a monitor isn't idempotent: turn caching off on this task and don't give it
    retries.

    Args:
        url: The URL to watch (the root URL for site scope).
        interval_minutes: Minutes between checks. Minimum 15.
        scope: "page" watches one URL, "site" crawls the site and tracks pages added,
            removed and changed, "wire" runs a Wire action each check and diffs its JSON.
        watch_mode: "full_page" or "specific_data" (tracks only output_schema's fields).
        watch_format: Compared format in full_page mode: "markdown", "html" or
            "cleaned_html".
        output_schema: JSON Schema of the fields to track. Required for
            watch_mode="specific_data".
        ai_mode: Filter out trivial changes with AI and summarize real ones.
        ai_goal: Which changes count as meaningful (used with ai_mode).
        use_browser: Check with a headless browser.
        country: Proxy country code.
        session_id: Saved browser session for login-protected pages.
        is_active: Start checking immediately.
        expires_at: End date (ISO 8601 or YYYY-MM-DD). The monitor pauses then.
        alert_webhook_url: Webhook that receives signed change alerts.
        alert_emails: Comma-separated email recipients for change alerts.
        max_pages: Site scope: maximum pages per run.
        max_depth: Site scope: crawl depth (1-5).
        include_patterns: Site scope: patterns or URLs to track.
        exclude_patterns: Site scope: patterns to skip.
        wire_action_id: Wire scope (required there): the action to run each check.
        wire_catalog_slug: Wire scope: the action's catalog slug.
        wire_credential_id: Wire scope: credential for actions that need auth.
        wire_params: Wire scope: parameters for the action.
        wire_watch_paths: Wire scope: JSON paths to diff instead of the whole result.

    Returns:
        The new monitor. The webhook signing secret is redacted: read it in the Anakin
        dashboard.
    """
    from anakin import Anakin

    options: dict = {
        "scope": scope,
        "watch_mode": watch_mode,
        "watch_format": watch_format,
        "ai_mode": ai_mode,
        "use_browser": use_browser,
        "country": country,
        "is_active": is_active,
    }
    optional = {
        "output_schema": output_schema,
        "ai_goal": ai_goal,
        "session_id": session_id,
        "expires_at": expires_at,
        "alert_webhook_url": alert_webhook_url,
        "alert_emails": alert_emails,
        "max_pages": max_pages,
        "max_depth": max_depth,
        "include_patterns": include_patterns,
        "exclude_patterns": exclude_patterns,
        "wire_action_id": wire_action_id,
        "wire_catalog_slug": wire_catalog_slug,
        "wire_credential_id": wire_credential_id,
        "wire_params": wire_params,
        "wire_watch_paths": wire_watch_paths,
    }
    options.update({k: v for k, v in optional.items() if v is not None})
    monitor = Anakin().monitors.create(url, interval_minutes, **options)
    return redact_webhook_secret(to_json(monitor))
