############################################################
# ReviewForm  (client-side)
# Expected components on the Form:
#   • pdf_viewer     : RichText   (Format = Raw HTML)  ← left pane
#   • form_container : ColumnPanel                    ← right pane
#   • btn_save       : Button                         ← inside form_container
############################################################
from anvil import *
import anvil.server
from datetime import date
import urllib.parse      # for URL-encoding the PDF link

class ReviewForm(ReviewFormTemplate):

  # ─────────────────────────────────────────────────────────
  # INIT
  # ─────────────────────────────────────────────────────────
  def __init__(self, row_id=None, **properties):
    self.init_components(**properties)

    # map JSON-Pointer → UI component (only for primitives)
    self._component_map = {}

    if row_id:
      self.load_doc(row_id)

  # ─────────────────────────────────────────────────────────
  # LOAD A DOCUMENT
  # ─────────────────────────────────────────────────────────
  def load_doc(self, row_id):
    """
    Pull doc from the server, show PDF.js viewer, and render dynamic form.
    """
    details     = anvil.server.call("get_document", row_id)
    self.row_id = row_id

    # ----- show full Mozilla PDF.js viewer in the left pane -----
    pdf_url    = anvil.media.to_url(details["pdf"])
    viewer_url = (
      "https://mozilla.github.io/pdf.js/web/viewer.html?file="
      + urllib.parse.quote(pdf_url, safe="")
    )
    self.pdf_viewer.content = (
      f"<iframe src='{viewer_url}' "
      f"style='border:none;width:100%;height:100%;'></iframe>"
    )
    # ------------------------------------------------------------

    # build editable form on the right
    self.form_container.clear()
    self._component_map = {}
    self._render_object(
      parent      = self.form_container,
      json_obj    = details["json"],
      schema_node = {},          # no JSON Schema stored
      path        = [],
    )

  # ─────────────────────────────────────────────────────────
  # SAVE BUTTON
  # ─────────────────────────────────────────────────────────
  def btn_save_click(self, **event_args):
    patched = self._rebuild_json()
    anvil.server.call("save_document", self.row_id, patched)
    alert("Saved!", title="Success")

  # ─────────────────────────────────────────────────────────
  # DYNAMIC RENDERERS
  # ─────────────────────────────────────────────────────────
  def _render_object(self, parent, json_obj, schema_node, path):
    """Recursively render dicts / lists into the UI."""
    if isinstance(json_obj, dict):
      for key, val in json_obj.items():
        self._render_field(parent, key, val, schema_node.get(key, {}), path + [key])
    elif isinstance(json_obj, list):
      for idx, item in enumerate(json_obj):
        card = ColumnPanel(role="card")
        parent.add_component(card)
        self._render_object(card, item, schema_node.get("items", {}), path + [str(idx)])

  def _render_field(self, parent, key, value, schema, path):
    """Render a single primitive or nested collection."""
    parent.add_component(Label(text=key.replace("_", " ").title()))

    # nested structures
    if isinstance(value, (dict, list)):
      self._render_object(parent, value, schema.get("properties", {}) if isinstance(schema, dict) else {}, path)
      return

    # primitive widgets
    if isinstance(schema, dict) and schema.get("enum"):
      comp = DropDown(items=schema["enum"], selected_value=value)
    elif isinstance(value, bool):
      comp = CheckBox(checked=value)
    elif self._looks_like_iso_date(value):
      comp = DatePicker(date=date.fromisoformat(value))
    elif isinstance(value, (int, float)):
      comp = TextBox(text=str(value), type="number")
    else:
      comp = TextBox(text=str(value))

    parent.add_component(comp)
    self._component_map[self._path_to_pointer(path)] = comp

  # ─────────────────────────────────────────────────────────
  # COLLECT / REBUILD JSON
  # ─────────────────────────────────────────────────────────
  def _rebuild_json(self):
    new_json = {}
    for ptr, comp in self._component_map.items():
      self._set_by_pointer(new_json, ptr, self._value_from_component(comp))
    return new_json

  def _value_from_component(self, comp):
    if isinstance(comp, CheckBox):
      return comp.checked
    if isinstance(comp, DatePicker):
      return comp.date.isoformat() if comp.date else None
    if isinstance(comp, TextBox) and comp.type == "number":
      txt = comp.text.strip()
      if txt == "":
        return None
      return float(txt) if "." in txt else int(txt)
    if isinstance(comp, DropDown):
      return comp.selected_value
    return comp.text

  # ─────────────────────────────────────────────────────────
  # JSON POINTER UTILITIES
  # ─────────────────────────────────────────────────────────
  def _path_to_pointer(self, path):
    return "/" + "/".join(str(p) for p in path)

  def _set_by_pointer(self, obj, pointer, value):
    toks = pointer.strip("/").split("/")
    cur  = obj
    for tok in toks[:-1]:
      tok = int(tok) if tok.isdigit() else tok
      if tok not in cur:
        cur[tok] = {} if not toks[toks.index(tok)+1].isdigit() else []
      cur = cur[tok]
    last = int(toks[-1]) if toks[-1].isdigit() else toks[-1]
    cur[last] = value

  # ─────────────────────────────────────────────────────────
  # HELPER: DATE DETECTION
  # ─────────────────────────────────────────────────────────
  def _looks_like_iso_date(self, val):
    try:
      return isinstance(val, str) and len(val) >= 10 and val[4] == "-" and val[7] == "-" and date.fromisoformat(val[:10])
    except Exception:
      return False
