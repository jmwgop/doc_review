import anvil.server, json, anvil
from ._anvil_designer import ReviewFormTemplate  # auto-generated

class ReviewForm(ReviewFormTemplate):
  """
  Split-pane document reviewer.
  • Left  = PDF (Media component named pdf_viewer)
  • Right = dynamic field list (ColumnPanel named fields_panel)
  """

  # ---------- init ----------
  def __init__(self, **properties):
    self.init_components(**properties)

    # convenience handles
    self._panel   = self.fields_panel      # ColumnPanel on the right
    self._widgets = {}                     # key → widget
    self._doc_ids = anvil.server.call("list_doc_ids")
    self._idx     = 0                      # which doc we’re on
    self._load_doc()

  # ---------- load one doc ----------
  def _load_doc(self):
    self._doc_id = self._doc_ids[self._idx]
    bundle       = anvil.server.call("load_document", self._doc_id)
    self._orig   = bundle.get("result_json")     or {}
    self._corr   = bundle.get("corrected_json")  or {}
    merged       = {**self._orig, **self._corr}

    # PDF
    self.pdf_viewer.source = anvil.server.call("get_pdf", self._doc_id)

    # rebuild right-hand fields
    self._panel.clear()
    self._widgets.clear()
    for key, val in merged.items():
      self._add_field(key, val)

    self.doc_label.text = f"{self._doc_id}   ({self._idx+1}/{len(self._doc_ids)})"

  # ---------- create one field ----------
  def _add_field(self, key, val):
    from anvil import Label, TextBox, TextArea, CheckBox
    self._panel.add_component(Label(text=key, bold=True))

    if isinstance(val, bool):
      w = CheckBox(checked=val)
    elif isinstance(val, (int, float, str)) or val is None:
      w = TextBox(text="" if val is None else str(val))
    else:                                   # list / dict / unknown
      w = TextArea(text=json.dumps(val, indent=2), height_row_count=4)

    self._panel.add_component(w)
    self._widgets[key] = w

  # ---------- collect edits & save ----------
  def _gather_edits(self):
    new = {}
    for k, w in self._widgets.items():
      if isinstance(w, anvil.CheckBox):
        v = w.checked
      else:
        txt = w.text
        try:
          v = float(txt) if txt.replace('.', '', 1).isdigit() else txt
        except Exception:
          v = txt
      if self._orig.get(k) != v:
        new[k] = v
    return new

  # ---------- button events ----------
  def prev_btn_click(self, **e):
    if self._idx > 0:
      self._idx -= 1
      self._load_doc()

  def next_btn_click(self, **e):
    if self._idx < len(self._doc_ids) - 1:
      self._idx += 1
      self._load_doc()

  def save_btn_click(self, **e):
    anvil.server.call("save_corrected_json", self._doc_id, self._gather_edits())
    anvil.alert("Saved!", timeout=1.5)
