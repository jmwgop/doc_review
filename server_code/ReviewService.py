# ServerModule: document_helpers
import json, anvil.server, anvil.media
import anvil.server
import anvil.tables as tables
from anvil.tables import app_tables

@anvil.server.callable
def get_document(doc_id):
  """
    Returns (pdf_inline_url_or_None, result_json_str, corrected_json_str)
    """
  row = app_tables.documents.get(doc_id=doc_id)
  if not row:
    raise ValueError(f"No document with id {doc_id}")

  pdf_media = row["pdf"]

  # ----- build an *inline* URL if we have a PDF -----
  pdf_url = None
  if pdf_media:
    # attachment=False → Content-Disposition: inline
    pdf_url = pdf_media.get_url(False)
    print(pdf_url)
  active_json = row["corrected_json"] or row["result_json"] or {}
  return (
    pdf_url,                                  # <- plain string now
    json.dumps(row["result_json"] or {}, indent=2),
    json.dumps(active_json, indent=2),
  )
  
@anvil.server.callable
def save_corrected_json(doc_id, json_text):
  """
    Parses json_text, writes it to corrected_json column, returns ok/err.
    """
  import json
  row = app_tables.documents.get(doc_id=doc_id)
  if not row:
    raise ValueError(f"No document with id {doc_id}")

  try:
    parsed = json.loads(json_text)
  except json.JSONDecodeError as e:
    return {"ok": False, "msg": f"JSON error: {e}"}

  row['corrected_json'] = parsed
  return {"ok": True}

@anvil.server.callable
def get_document_dropdown_items(limit=None):
  """
  Returns a list of (label, value) pairs for a dropdown.
  Both label and value are the doc_id, sorted A–Z.
  """
  rows = app_tables.documents.search()            # no limit

  # Build and sort items
  items = [(row['doc_id'], row['doc_id']) for row in rows]
  items.sort(key=lambda t: t[0])

  # Optional blank/placeholder at the top:
  items.insert(0, ('', None))      # label='', value=None

  return items
