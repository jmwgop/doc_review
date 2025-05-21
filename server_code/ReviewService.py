# ================================
# 1.  SERVER MODULE  (ReviewService)
# ================================

import json
from pathlib import Path
import anvil.server
import anvil.media
from anvil.tables import app_tables

_DATA_DIR = Path("data/output")          # fallback when table empty
_PDF_DIR  = Path("data/input")

@anvil.server.callable
def list_doc_ids() -> list[str]:
  """Return doc_ids present in Data Table; fall back to file system."""
  rows = app_tables.documents.search(tables.order_by("doc_id"))
  if rows:
    return [r["doc_id"] for r in rows]
    # dev fallback so the form still loads even if table empty
  return sorted(p.stem for p in _DATA_DIR.glob("*.json"))

@anvil.server.callable
def load_document(doc_id: str) -> dict:
  """Return a dict {result_json, corrected_json, has_pdf}."""
  row = app_tables.documents.get(doc_id=doc_id)
  if row:
    return {
      "result_json": row["result_json"],
      "corrected_json": row.get("corrected_json") or {},
      "has_pdf": row["pdf"] is not None,
    }
    # local‑disk fallback (dev only)
  with open(_DATA_DIR / f"{doc_id}.json", "r", encoding="utf-8") as fp:
    payload = json.load(fp)
  return {"result_json": payload, "corrected_json": {}, "has_pdf": False}

@anvil.server.callable
def save_corrected_json(doc_id: str, corrected: dict):
  row = app_tables.documents.get(doc_id=doc_id)
  if not row:
    raise RuntimeError(f"No row for {doc_id} – push phase must run first")
  row["corrected_json"] = corrected

@anvil.server.callable
def get_pdf(doc_id: str):
  row = app_tables.documents.get(doc_id=doc_id)
  if row and row["pdf"] is not None:
    return row["pdf"]
    # dev fallback
  pdf_file = next((_PDF_DIR / doc_id).glob("*.pdf"), None)
  return anvil.media.from_file(pdf_file, content_type="application/pdf") if pdf_file else None