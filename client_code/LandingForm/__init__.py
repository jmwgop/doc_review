from ._anvil_designer import LandingFormTemplate
from anvil import *
import anvil.server

class LandingForm(LandingFormTemplate):

  def __init__(self, **properties):
    # Initialise form components
    self.init_components(**properties)

    # ----- populate the dropdown from the server -----
    try:
      # Calls the server function you just added
      items = anvil.server.call("get_document_dropdown_items")
    except Exception as e:
      alert(f"Unable to load document list:\n{e}")
      items = []

    self.doc_dropdown.items = items
    self.doc_dropdown.selected_value = None   # start blank

  # ----- event: user picks a document -----
  def doc_dropdown_change(self, **event_args):
    doc_id = self.doc_dropdown.selected_value
    if doc_id:
      # Switch to the ReviewForm with the chosen doc_id
      open_form('ReviewForm', doc_id=doc_id)
