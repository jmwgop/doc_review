# JsonItemTpl
from ._anvil_designer import JsonItemTplTemplate
from anvil import *
from ..ui_builder_textbox_only import JsonTextboxBuilder

class JsonItemTpl(JsonItemTplTemplate):

  def __init__(self, **properties):
    print('Loaded JsonItemTpl')
    self.init_components(**properties)

  @property
  def item(self):
    return getattr(self, '_item', None)

  @item.setter
  def item(self, item):
    self._item = item
    self.set_item(item)

  def set_item(self, item):
    self.container.clear()
    self.container.add_component(
      Label(text=item.get("description", "NO DESCRIPTION FOUND"))
    )
    self.builder = JsonTextboxBuilder()
    index = None
    try:
      index = self.parent.items.index(item)
      path = f"{self.parent_path}[{index}]" if hasattr(self, 'parent_path') else ""
    except Exception:
      path = ""

    self.container.add_component(
      self.builder.build(item, path=path)
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
