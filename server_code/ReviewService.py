############################################################
# ReviewService  (Server Module) – matches table: pdf,
# result_json, corrected_json, doc_id
############################################################
import json
import anvil.server
import anvil.tables as tables
from anvil.tables import app_tables
from datetime import datetime

# ─── Configuration ────────────────────────────────────────
TABLE_NAME            = "documents"
PDF_COL               = "pdf"            # Media object
ORIGINAL_JSON_COL     = "result_json"    # Extractor output
CORRECTED_JSON_COL    = "corrected_json" # Reviewer edits
MAX_SUMMARY_FIELDS    = 8                # fields to show in list_documents
# ───────────────────────────────────────────────────────────


# ─── Helpers ──────────────────────────────────────────────
def _get_row(row_id):
  row = app_tables[TABLE_NAME].get_by_id(row_id)
  if row is None:
    raise anvil.server.AppError(f"Document row '{row_id}' not found.")
  return row


def _load_json(row):
  """Return whichever JSON (corrected → original) is present, as a dict."""
  raw = row.get(CORRECTED_JSON_COL) or row[ORIGINAL_JSON_COL]
  try:
    return json.loads(raw)
  except Exception as e:
    raise anvil.server.AppError(f"Invalid JSON stored in row: {e}")


# ─── RPC: List documents ──────────────────────────────────
@anvil.server.callable(require_user=True)
def list_documents():
  """
    Lightweight listing: row_id, created, doc_id + up to N scalar fields
    auto-harvested from payload['output'][0].
    """
  docs = []
  for row in app_tables[TABLE_NAME].search(tables.order_by("-created")):
    item = {
      "row_id":  row.get_id(),
      "created": row.get("created", datetime.utcnow()),
      "doc_id":  row.get("doc_id"),   # if you track an external id
    }

    payload = _load_json(row)
    doc_level = payload.get("output", [{}])[0] if isinstance(payload.get("output"), list) else {}

    for k, v in doc_level.items():
      if isinstance(v, (str, int, float, bool)) and len(item) - 3 < MAX_SUMMARY_FIELDS:
        item[k] = v

    docs.append(item)
  return docs


# ─── RPC: Get a single document ───────────────────────────
@anvil.server.callable(require_user=True)
def get_document(row_id):
  """
    Returns {'row_id', 'pdf' (Media), 'json' (dict)}.
    Prefers corrected_json; falls back to original result_json.
    """
  row = _get_row(row_id)
  return {
    "row_id": row_id,
    "pdf":    row[PDF_COL],
    "json":   _load_json(row),
  }


# ─── RPC: Save reviewer edits ─────────────────────────────
@anvil.server.callable(require_user=True)
def save_document(row_id, patched_json: dict):
  """
    Validates with ExtractionPayload (if importable) then stores to
    corrected_json.
    """
  try:
    from lease_extraction.models.dto.extraction import ExtractionPayload
    ExtractionPayload.model_validate(patched_json)
  except ModuleNotFoundError:
    # model not shipped to Anvil – skip strict validation
    pass
  except Exception as e:
    raise anvil.server.AppError(f"Validation error: {e}")

  row = _get_row(row_id)
  row[CORRECTED_JSON_COL] = json.dumps(patched_json, default=str)
  row.update()
  return {"status": "ok"}


# ─── RPC: Delete a document row ───────────────────────────
@anvil.server.callable(require_user=True)
def delete_document(row_id):
  row = _get_row(row_id)
  row.delete()
  return {"status": "deleted"}
