# ui_builder_textbox_only.py   (CLIENT module)

from anvil import *
import datetime   
from .field_config import EXCLUDE_PATHS, FIELD_WIDGETS, ALLOWED_WIDGET_TYPES
from . import flag_utils as fu
import re


# ----- helpers for path matching -------------------------------------------
def _normalise(path: str) -> str:
  """Convert 'parties[0].address.street' → 'parties[*].address.street'."""
  return re.sub(r"\[\d+\]", "[*]", path)

# ui_builder_textbox_only.py
# -------------------------------------------------
def _is_excluded(path: str) -> bool:
  """
    Return True if `path` itself **or any parent path**
    (after normalising list indices) is in EXCLUDE_PATHS.
    Prints debug info for every candidate it checks.
    """
  def _norm(p: str) -> str:
    return re.sub(r"\[\d+\]", "[*]", p)

  n = _norm(path)
  parts = n.split(".")

  for i in range(len(parts), 0, -1):
    candidate = ".".join(parts[:i])
    match = any(candidate == _norm(p) for p in EXCLUDE_PATHS)
    print(f"[DEBUG _is_excluded] checking {candidate!r} → {match}")
    if match:
      return True
  return False

def _widget_cfg(path: str):
  n = _normalise(path)
  return FIELD_WIDGETS.get(n, None)
# ---------------------------------------------------------------------------

class JsonTextboxBuilder:

  def __init__(self, saved_flags=None):
    self.path_to_widget = {}
    self.path_to_flag_cb = {}
    self.saved_flags = saved_flags or {}

  # ------------------------------------------------------------------ build
  def build(self, value, path=""):
    if _is_excluded(path):
      return Spacer()   # skip entirely

      # ---------- dict ----------
    if isinstance(value, dict):
      card = ColumnPanel(
        role="outlined-card",
        spacing_above="none",
        spacing_below="none"

      )
      for k, v in value.items():
        child_path = f"{path}.{k}" if path else k
        if _is_excluded(child_path):
          continue                        # skip both label **and** subtree
    
        row = FlowPanel(
                        spacing_above="none",
                        spacing_below="none"
                       )
        row.add_component(Label(text=k, bold=True))
        row.add_component(self.build(v, child_path))
        card.add_component(row)
      return card


    # ---------- list ----------
    if isinstance(value, list):
      wrapper = ColumnPanel(spacing="none")
      rp = RepeatingPanel(item_template="JsonItemTpl",
                          spacing_above='none',
                          spacing_below='none')    
      rp.items = value or []
    
      def setup_row(**event_args):
        row = event_args['sender']
        row.parent_path = path
    
      rp.set_event_handler('show', setup_row)
    
      self.path_to_widget[path] = rp
      wrapper.add_component(rp)
    
      # add/remove controls
      add_btn = Button(text="+ Add", role="outlined-button")
      add_btn.set_event_handler("click", lambda **e: self._add_list_item(path))
      wrapper.add_component(add_btn)
    
      wrapper.expand = True
    
      return wrapper


      # ---------- scalar ----------
    cfg = _widget_cfg(path) or {}
    widget_type = cfg.get("type", "textbox")
    if widget_type not in ALLOWED_WIDGET_TYPES:
      widget_type = "textbox"

    if widget_type == "textarea":
      w = TextArea(text=self._to_str(value), height="6em")
    elif widget_type == "dropdown":
      choices = cfg.get("choices", [])
      # ensure current value included
      if self._to_str(value) not in choices:
        choices = choices + [self._to_str(value)]
      w = DropDown(items=[(c, c) for c in choices], selected_value=self._to_str(value))
    elif widget_type == "datepicker":
      try:
        dt_val = datetime.date.fromisoformat(value) if value else None
      except Exception:
        dt_val = None
      w = DatePicker(date=dt_val)
    else:  # textbox default
      is_long = isinstance(value, str) and ("\n" in value or len(value) > 80)
      if is_long:
        w = TextArea(text=self._to_str(value), height="6em")
      else:
        w = TextBox(text=self._to_str(value))

    self.path_to_widget[path] = w

    # ---- flag checkbox ----
    flag_cb = fu.create_flag_checkbox(path, flagged=self.saved_flags.get(path, False))
    self.path_to_flag_cb[path] = flag_cb

    row = FlowPanel(spacing="small")
    row.add_component(w)
    row.add_component(flag_cb)
    return row

    # ------------------------------------------------------------ collect ----
  def collect(self, original, path=""):
    if _is_excluded(path):
      return original   # untouched

      # dict
    if isinstance(original, dict):
      return {k: self.collect(v, f"{path}.{k}" if path else k)
              for k, v in original.items()}

      # list
    if isinstance(original, list):
      rp = self.path_to_widget[path]
      collected = []
      for i, itm in enumerate(rp.items):
        collected.append(self.collect(itm, f"{path}[{i}]"))
      return collected

      # scalar
    w = self.path_to_widget[path]
    val = self._get_widget_value(w)
    return val

  def collect_flags(self):
    return fu.collect_flags(self.path_to_flag_cb)

    # --------------------------------------------------------- internals -----
  def _add_list_item(self, path):
    rp = self.path_to_widget.get(path)
    if rp is None:
      return
      # assume homogenous list of dicts → empty dict; else None
    blank = {} if rp.items and isinstance(rp.items[0], dict) else None
    rp.items = rp.items + [blank]

  def _get_widget_value(self, widget):
    if isinstance(widget, DropDown):
      return widget.selected_value
    if isinstance(widget, DatePicker):
      return widget.date.isoformat() if widget.date else None
    if isinstance(widget, (TextArea, TextBox)):
      txt = widget.text.strip()
      return self._from_str(txt)
    return None

    # ---------- helpers ------------------------------------------------------
  def _to_str(self, v):
    if v is None:
      return ""
    if isinstance(v, bool):
      return "true" if v else "false"
    return str(v)

  def _from_str(self, s):
    if s == "":
      return None
    if s.lower() in ("true", "false"):
      return s.lower() == "true"
    try:
      return int(s)
    except ValueError:
      try:
        return float(s)
      except ValueError:
        return s
