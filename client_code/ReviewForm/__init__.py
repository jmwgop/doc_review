from ._anvil_designer import ReviewFormTemplate
import anvil.server, json
from ..ui_builder_textbox_only import JsonTextboxBuilder   # ← new
# no need for encodeURIComponent any more

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
    self.pdf_frame.url = pdf_url or "about:blank"

    # ---- build editable widgets on the right ----
    self.data_obj = json.loads(active_json_str)
    payload = (self.data_obj.get("output") or [{}])[0]

    self.builder = JsonTextboxBuilder()
    self.dynamic_container.clear()                       # ← your empty ColumnPanel
    self.dynamic_container.add_component(
      self.builder.build(payload)                      # generate nested text boxes
    )
    self.payload_path = "output[0]"                      # remember where it sits

  # ---------- events ----------
  def save_btn_click(self, **event_args):
    # collect edits back into the JSON object
    self.data_obj["output"][0] = self.builder.collect(
      self.data_obj["output"][0], self.payload_path
    )
    res = anvil.server.call(
      "save_corrected_json", self.doc_id, json.dumps(self.data_obj)
    )
    alert("Saved!" if res["ok"] else res["msg"],
          title="Save result", large=not res["ok"])
