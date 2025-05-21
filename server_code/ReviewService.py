# ServerModule: document_helpers
import json, anvil.server, anvil.media
import anvil.tables as tables
from anvil.tables import app_tables


@anvil.server.callable
def get_document(doc_id):
  """
  Returns (pdf_inline_url_or_None, active_json_str, flags_dict)

  * active_json_str → corrected_json if present, else result_json
  * flags_dict      → contents of the `flags` column, or {} if none
  """
  row = app_tables.documents.get(doc_id=doc_id)
  if not row:
    raise ValueError(f"No document with id {doc_id}")

  # ----- PDF URL (inline) -----
  pdf_media = row["pdf"]
  pdf_url = pdf_media.get_url(False) if pdf_media else None

  # ----- JSON -----
  active_json = row["corrected_json"] or row["result_json"] or {}
  json_str = json.dumps(active_json, indent=2)

  # ----- Flags -----
  flags = row["flags"] or {}

  return pdf_url, json_str, flags


@anvil.server.callable
def save_corrected_json(doc_id, json_text, flags=None):
  """
  Writes `corrected_json` and `flags` back to the row.

  Args:
      doc_id    : document row key
      json_text : stringified JSON to store in corrected_json
      flags     : dict of {path: True} flag states (may be None)
  Returns:
      {"ok": True} on success, or {"ok": False, "msg": "..."} on error
  """
  row = app_tables.documents.get(doc_id=doc_id)
  if not row:
    raise ValueError(f"No document with id {doc_id}")

  try:
    parsed_json = json.loads(json_text)
  except json.JSONDecodeError as e:
    return {"ok": False, "msg": f"JSON error: {e}"}

  row["corrected_json"] = parsed_json
  row["flags"] = flags or {}

  return {"ok": True}


@anvil.server.callable
def get_document_dropdown_items(limit=None):
  """
  Returns a list of (label, value) pairs for the dropdown.
  Both label and value are the doc_id, sorted A–Z.
  """
  rows = app_tables.documents.search()  # add limit if you wish
  items = [(r["doc_id"], r["doc_id"]) for r in rows]
  items.sort(key=lambda t: t[0])
  items.insert(0, ("", None))           # blank placeholder
  return items
