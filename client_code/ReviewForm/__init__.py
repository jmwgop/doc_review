import anvil.server, json, anvil
from ._anvil_designer import ReviewFormTemplate

class ReviewForm(ReviewFormTemplate):
  """
  Document reviewer.

  **Designer expectations**
  ─────────────────────────
  • Media      → name **pdf_viewer**
  • ColumnPanel→ name **fields_panel**
  • Label      → name **doc_label**
  • Button     → name **prev_btn**
  • Button     → name **next_btn**
  • Button     → name **save_btn**
  """

  def __init__(self, **properties):
    self.init_components(**properties)

    self._widgets: dict[str, anvil.Component] = {}
    self._doc_ids = anvil.server.call("list_doc_ids")
    self._idx = 0
    self._load_doc()

  # ── load one doc ──
  def _load_doc(self):
    self._doc_id = self._doc_ids[self._idx]
    bundle = anvil.server.call("load_document", self._doc_id)
    self._orig = bundle.get("result_json") or {}
    self._corr = bundle.get("corrected_json") or {}
    merged = {**self._orig, **self._corr}

    self.pdf_viewer.source = anvil.server.call("get_pdf", self._doc_id)

    self.fields_panel.clear()
    self._widgets.clear()
    for k, v in merged.items():
      self._add_field(k, v)

    self.doc_label.text = f"{self._doc_id}  ({self._idx+1}/{len(self._doc_ids)})"

  # ── add one dynamic field ──
  def _add_field(self, key, val):
    from anvil import Label, TextBox, TextArea, CheckBox
    self.fields_panel.add_component(Label(text=key, bold=True))

    if isinstance(val, bool):
      w = CheckBox(checked=val)
    elif isinstance(val, (int, float, str)) or val is None:
      w = TextBox(text="" if val is None else str(val))
    else:
      w = TextArea(text=json.dumps(val, indent=2), height_row_count=4)

    self.fields_panel.add_component(w)
    self._widgets[key] = w

  # ── gather edits ──
  def _edits(self):
    out = {}
    for k, w in self._widgets.items():
      v = w.checked if isinstance(w, anvil.CheckBox) else w.text
      out[k] = v
    return {k: v for k, v in out.items() if self._orig.get(k) != v}

  # ── events ──
  def prev_btn_click(self, **e):
    if self._idx > 0:
      self._idx -= 1
      self._load_doc()

  def next_btn_click(self, **e):
    if self._idx < len(self._doc_ids) - 1:
      self._idx += 1
      self._load_doc()

  def save_btn_click(self, **e):
    anvil.server.call("save_corrected_json", self._doc_id, self._edits())
    anvil.alert("✅ Saved", timeout=1.5)
