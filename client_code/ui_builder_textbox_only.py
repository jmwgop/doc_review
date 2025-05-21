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

def _is_excluded(path: str) -> bool:
  def _norm(p: str) -> str:
    return re.sub(r"\[\d+\]", "[*]", p)
  n = _norm(path)
  parts = n.split(".")
  for i in range(len(parts), 0, -1):
    candidate = ".".join(parts[:i])
    match = any(candidate == _norm(p) for p in EXCLUDE_PATHS)
    if match:
      return True
  return False

def _widget_cfg(path: str):
  n = _normalise(path)
  return FIELD_WIDGETS.get(n, None)

class JsonTextboxBuilder:

  def __init__(self, saved_flags=None):
    self.path_to_widget = {}
    self.path_to_flag_cb = {}
    self.saved_flags = saved_flags or {}

  def build(self, value, path=""):
    if _is_excluded(path):
      return None

    # ---------- dict ----------
    if isinstance(value, dict):
      card = ColumnPanel(
        role="outlined-card",
        spacing_above="none",
        spacing_below="none",
        col_spacing="none",
      )
      card.expand = True
      for k, v in value.items():
        child_path = f"{path}.{k}" if path else k
        if _is_excluded(child_path):
          continue
        row = FlowPanel(
          spacing_above="none",
          spacing_below="none",
          spacing="none"
        )
        row.add_component(Label(text=k, bold=True))
        sub_component = self.build(v, child_path)
        if sub_component is not None:
          row.add_component(sub_component)
        card.add_component(row)
      return card

    # ---------- list ----------
    if isinstance(value, list):
      # Only wrap in a ColumnPanel if you need the "Add" button; otherwise just return the RepeatingPanel
      if len(value) == 0:
        # If the list is empty, still return a panel with an Add button
        panel = ColumnPanel(spacing="none", spacing_above="none", spacing_below="none", col_spacing="none")
        add_btn = Button(text="+ Add", role="outlined-button", spacing_above="none", spacing_below="none")
        add_btn.set_event_handler("click", lambda **e: self._add_list_item(path))
        panel.add_component(add_btn)
        return panel

      rp = RepeatingPanel(
        item_template="JsonItemTpl",
        spacing_above="none",
        spacing_below="none"
      )
      rp.items = value or []

      def setup_row(**event_args):
        row = event_args['sender']
        row.parent_path = path

      rp.set_event_handler('show', setup_row)
      self.path_to_widget[path] = rp

      # Only add the Add button under the RP if needed
      panel = ColumnPanel(spacing="none", spacing_above="none", spacing_below="none", col_spacing="none")
      panel.add_component(rp)
      add_btn = Button(text="+ Add", role="outlined-button", spacing_above="none", spacing_below="none")
      add_btn.set_event_handler("click", lambda **e: self._add_list_item(path))
      panel.add_component(add_btn)
      return panel

    # ---------- scalar ----------
    cfg = _widget_cfg(path) or {}
    widget_type = cfg.get("type", "textbox")
    if widget_type not in ALLOWED_WIDGET_TYPES:
      widget_type = "textbox"

    if widget_type == "textarea":
      w = TextArea(text=self._to_str(value), height="6em")
    elif widget_type == "dropdown":
      choices = cfg.get("choices", [])
      if self._to_str(value) not in choices:
        choices = choices + [self._to_str(value)]
      w = DropDown(items=[(c, c) for c in choices], selected_value=self._to_str(value))
    elif widget_type == "datepicker":
      try:
        dt_val = datetime.date.fromisoformat(value) if value else None
      except Exception:
        dt_val = None
      w = DatePicker(date=dt_val)
    else:
      is_long = isinstance(value, str) and ("\n" in value or len(value) > 80)
      if is_long:
        w = TextArea(text=self._to_str(value), height="6em")
      else:
        w = TextBox(text=self._to_str(value))

    self.path_to_widget[path] = w

    # ---- flag checkbox ----
    flag_cb = fu.create_flag_checkbox(path, flagged=self.saved_flags.get(path, False))
    self.path_to_flag_cb[path] = flag_cb

    row = FlowPanel(spacing="none", spacing_above="none", spacing_below="none")
    row.add_component(w)
    row.add_component(flag_cb)
    return row

  def collect(self, original, path=""):
    if _is_excluded(path):
      return original

    if isinstance(original, dict):
      return {k: self.collect(v, f"{path}.{k}" if path else k)
              for k, v in original.items()}

    if isinstance(original, list):
      rp = self.path_to_widget[path]
      collected = []
      for i, itm in enumerate(rp.items):
        collected.append(self.collect(itm, f"{path}[{i}]"))
      return collected

    w = self.path_to_widget[path]
    val = self._get_widget_value(w)
    return val

  def collect_flags(self):
    return fu.collect_flags(self.path_to_flag_cb)

  def _add_list_item(self, path):
    rp = self.path_to_widget.get(path)
    if rp is None:
      return
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
