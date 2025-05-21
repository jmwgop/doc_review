# JsonItemTpl
from ._anvil_designer import JsonItemTplTemplate
from anvil import *
from ..ui_builder_textbox_only import JsonTextboxBuilder

class JsonItemTpl(JsonItemTplTemplate):

  def set_item(self, item):
    """
    Called automatically by the RepeatingPanel for each list element.
    `item` is the dict / scalar representing that row.
    """
    # 1. rebuild the inner widgets
    self.builder = JsonTextboxBuilder()       # fresh builder per row
    self.container.clear()
    self.container.add_component(
      self.builder.build(item)              # drop generated widgets
    )

  # 2. remove-row logic
  def remove_btn_click(self, **event_args):
    """
    Remove this item from the parent RepeatingPanel's items list.
    """
    rp = self.parent   # the repeating panel that hosts this template
    if not isinstance(rp, RepeatingPanel):
      return
    new_items = [itm for itm in rp.items if itm is not self.item]
    rp.items = new_items
