# ui_builder_textbox_only.py
from anvil import *

class JsonTextboxBuilder:
  def __init__(self):
    self.path_to_widget = {}

    # ---------- build ----------
  def build(self, value, path=""):
    if isinstance(value, dict):
      cp = ColumnPanel()
      for k, v in value.items():
        cp.add_component(Label(text=k, bold=True))
        cp.add_component(self.build(v, f"{path}.{k}" if path else k))
      return cp

    if isinstance(value, list):
      rp = RepeatingPanel()
      rp.item_template = "JsonItemTpl"      # a simple form you create once
      rp.items = value or []
      self.path_to_widget[path] = rp
      return rp

    tb = TextBox(text=self._to_str(value))
    self.path_to_widget[path] = tb
    return tb

    # ---------- collect ----------
  def collect(self, original, path=""):
    if isinstance(original, dict):
      return {
        k: self.collect(v, f"{path}.{k}" if path else k)
        for k, v in original.items()
      }

    if isinstance(original, list):
      rp = self.path_to_widget[path]
      return [self.collect(item, f"{path}[{i}]")
              for i, item in enumerate(rp.items)]

    txt = self.path_to_widget[path].text.strip()
    return self._from_str(txt)

    # ---------- helpers ----------
  def _to_str(self, v):
    if v is None:             return ""
    if isinstance(v, bool):   return "true" if v else "false"
    return str(v)

  def _from_str(self, s):
    if s == "":               return None
    if s.lower() in ("true","false"): return s.lower() == "true"
    try:  return int(s)
    except ValueError:
      try:  return float(s)
      except ValueError:
        return s
