############################################################
# ReviewService  (Server Module)
############################################################
import json, anvil.server
from anvil.tables import app_tables, query as q
from datetime import datetime
# ─── Config ───────────────────────────────────────────────
TABLE_NAME         = "documents"
PDF_COL            = "pdf"
ORIG_JSON_COL      = "result_json"
CORR_JSON_COL      = "corrected_json"
MAX_SUMMARY_FIELDS = 8
# ───────────────────────────────────────────────────────────
class AppError(RuntimeError):
  """Predictable, user-visible errors."""
  pass
# verify table
if not hasattr(app_tables, TABLE_NAME):
  raise AppError(
    f"[ReviewService] No table named '{TABLE_NAME}'. "
    f"Available: {', '.join(dir(app_tables))}"
  )
TABLE          = getattr(app_tables, TABLE_NAME)
TABLE_COLUMNS  = {c["name"] for c in TABLE.list_columns()}
# ─── Helpers ──────────────────────────────────────────────
def _col_exists(col): return col in TABLE_COLUMNS
def _get_row(rid):
  row = TABLE.get_by_id(rid)
  if row is None:
    raise AppError(f"[ReviewService] Row '{rid}' not found.")
  return row
def _load_json(row):
  """
    Return a Python dict from the row, no matter whether the column
    holds a dict (already parsed) or a JSON string.
    """
  raw = (
    row[CORR_JSON_COL]
    if _col_exists(CORR_JSON_COL) and row[CORR_JSON_COL]
    else row[ORIG_JSON_COL]
  )
  if isinstance(raw, dict):
    return raw                      # already parsed
  try:
    return json.loads(raw)          # parse from string/bytes
  except Exception as e:
    raise AppError(f"[ReviewService] JSON parse error: {e}")

def _safe(row, col, default=None):
  return row[col] if _col_exists(col) else default
# ─── RPCs ─────────────────────────────────────────────────
@anvil.server.callable
def list_documents():
  docs=[]
  for row in TABLE.search():
    item={
      "row_id": row.get_id(),
      "created": _safe(row,"created",datetime.utcnow()),
      "doc_id":  _safe(row,"doc_id"),
    }
    payload=_load_json(row)
    doc_level=payload.get("output",[{}])[0] if isinstance(payload.get("output"),list) else {}
    for k,v in doc_level.items():
      if isinstance(v,(str,int,float,bool)) and len(item)-3<MAX_SUMMARY_FIELDS:
        item[k]=v
    docs.append(item)
  return docs
@anvil.server.callable
def get_document(row_id):
  row=_get_row(row_id)
  return {"row_id":row_id,"pdf":row[PDF_COL],"json":_load_json(row)}
@anvil.server.callable
def save_document(row_id, patched_json:dict):
  try:
    from lease_extraction.models.dto.extraction import ExtractionPayload
    ExtractionPayload.model_validate(patched_json)
  except ModuleNotFoundError:
    pass
  except Exception as e:
    raise AppError(f"[ReviewService] Validation error: {e}")
  if not _col_exists(CORR_JSON_COL):
    raise AppError(f"[ReviewService] Table lacks '{CORR_JSON_COL}' column.")
  row=_get_row(row_id)
  row[CORR_JSON_COL]=json.dumps(patched_json, default=str)
  row.update()
  return {"status":"ok"}
@anvil.server.callable
def delete_document(row_id):
  _get_row(row_id).delete()
  return {"status":"deleted"}