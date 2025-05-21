# JsonItemTpl
from anvil import *
from .ui_builder_textbox_only import JsonTextboxBuilder

class JsonItemTpl(JsonItemTplTemplate):
  def set_item(self, item):
    self.builder = JsonTextboxBuilder()
    self.container.clear()
    self.container.add_component(self.builder.build(item))
