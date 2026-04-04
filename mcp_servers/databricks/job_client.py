import os
from typing import Any
from dotenv import load_dotenv

load_dotenv()

try:
    from databricks.sdk import WorkspaceClient
    from databricks.sdk.service.jobs import RunNowResponse
    _SDK_AVAILABLE = True
except ImportError:
    WorkspaceClient = None
    _SDK_AVAILABLE = False


def _get_client() -> Any:
    if not _SDK_AVAILABLE:
        raise ImportError("databricks-sdk is not installed. Run: pip install databricks-sdk")
    host = os.environ.get("DATABRICKS_HOST", "")
    token = os.environ.get("DATABRICKS_TOKEN", "")
    if not host or not token:
        raise EnvironmentError("DATABRICKS_HOST and DATABRICKS_TOKEN must be set.")
    return WorkspaceClient(host=host, token=token)


def trigger_enrichment(book_id: str) -> dict[str, Any]:
    """Trigger the book enrichment Databricks Workflow job."""
    try:
        client = _get_client()
        job_name = os.environ.get("ENRICHMENT_JOB_NAME", "abip-book-enrichment")
        # Find job by name
        jobs = list(client.jobs.list(name=job_name))
        if not jobs:
            return {
                "error": True,
                "errorCategory": "validation",
                "isRetryable": False,
                "message": (
                    f"Enrichment job '{job_name}' not found. "
                    "Create it in Databricks Workflows first."
                ),
            }
        job_id = jobs[0].job_id
        run = client.jobs.run_now(job_id=job_id, job_parameters={"book_id": book_id})
        return {"run_id": str(run.run_id), "book_id": book_id, "status": "triggered"}
    except EnvironmentError as e:
        return {"error": True, "errorCategory": "validation", "isRetryable": False, "message": str(e)}
    except ImportError as e:
        return {"error": True, "errorCategory": "validation", "isRetryable": False, "message": str(e)}
    except Exception as e:
        return {"error": True, "errorCategory": "transient", "isRetryable": True, "message": str(e)}


def get_job_status(run_id: str) -> dict[str, Any]:
    """Get the status of a Databricks job run."""
    try:
        client = _get_client()
        run = client.jobs.get_run(run_id=int(run_id))
        state = run.state
        return {
            "run_id": run_id,
            "life_cycle_state": state.life_cycle_state.value if state.life_cycle_state else "UNKNOWN",
            "result_state": state.result_state.value if state.result_state else None,
            "state_message": state.state_message or "",
        }
    except EnvironmentError as e:
        return {"error": True, "errorCategory": "validation", "isRetryable": False, "message": str(e)}
    except Exception as e:
        return {"error": True, "errorCategory": "transient", "isRetryable": True, "message": str(e)}
