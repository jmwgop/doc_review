from ._anvil_designer import ReviewFormTemplate
import anvil.server, json
from anvil.js.window import encodeURIComponent

class ReviewForm(ReviewFormTemplate):

  def __init__(self, doc_id, **properties):
    self.init_components(**properties)
    self.doc_id = doc_id
    self._load_document()

  # ---------- helpers ----------
  def _load_document(self):
    pdf_url, original_json_str, active_json_str = anvil.server.call(
      "get_document", self.doc_id
    )

    # ---- PDF on the left ----
    if pdf_url:
      self.pdf_frame.url = pdf_url          # one line does it
    else:
      self.pdf_frame.url = "about:blank"

    # ---- JSON on the right ----
    self.json_area.text = active_json_str
  # ---------- events ----------
  def save_btn_click(self, **event_args):
    res = anvil.server.call("save_corrected_json", self.doc_id, self.json_area.text)
    alert("Saved!" if res["ok"] else res["msg"], title="Save result", large=not res["ok"])
