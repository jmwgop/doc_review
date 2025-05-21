from ._anvil_designer import ReviewFormTemplate
from anvil import *
import anvil.server
import anvil.js
from datetime import date
from anvil import PDFViewer

class ReviewForm(ReviewFormTemplate):
  def __init__(self, row_id=None, **properties):
    self.init_components(**properties)

    # If no row_id supplied, grab the first doc automatically
    if row_id is None:
      docs = anvil.server.call('list_documents')
      if docs:
        row_id = docs[0]['row_id']
      else:
        alert("No documents in the database.")
        return

    self.load_doc(row_id)

  def load_doc(self, row_id):
    details = anvil.server.call("get_document", row_id)
    self.row_id = row_id

    # Use Anvil's built-in PDF viewer (if available in your version)
    if "pdf" in details and details["pdf"]:
      self.pdf_viewer.content = ""  # Clear existing content
      self.pdf_viewer.add_component(PDFViewer(pdf=details["pdf"]))
    else:
      self.pdf_viewer.content = "No PDF available"

    # Display JSON (simple version)
    if "json" in details:
      self.form_container.clear()
      text_area = TextArea(text=str(details["json"]), height="100%")
      self.form_container.add_component(text_area)

  def btn_save_click(self, **event_args):
    alert("Save functionality will be implemented later", title="Info")