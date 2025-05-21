# ReviewForm
from ._anvil_designer import ReviewFormTemplate
import anvil.server, json
from ..ui_builder_textbox_only import JsonTextboxBuilder
from .. import flag_utils as fu

class ReviewForm(ReviewFormTemplate):

  def __init__(self, doc_id, **properties):
    self.init_components(**properties)
    self.doc_id = doc_id
    self._load_document()

  # ---------- helpers ----------
  def _load_document(self):
    # server now returns (pdf_url, corrected_json_str, flags_dict)
    pdf_url, json_str, flags = anvil.server.call(
      "get_document", self.doc_id
    )

    # ---- PDF left ----
    self.pdf_frame.url = pdf_url or "about:blank"

    # ---- JSON -> widgets on right ----
    self.data_obj = json.loads(json_str)
    self.flags    = flags or {}

    payload = (self.data_obj.get("output") or [{}])[0]

    print("TRACTS:", payload.get("tracts"))
    print("PARTIES:", payload.get("parties"))

    self.builder = JsonTextboxBuilder(saved_flags=self.flags)
    self.dynamic_container.clear()
    self.dynamic_container.add_component(
      self.builder.build(payload)
    )
    self.payload_path = "output[0]"

  # ---------- save ----------
  def save_btn_click(self, **event_args):
    # gather edits
    self.data_obj["output"][0] = self.builder.collect(
      self.data_obj["output"][0], self.payload_path
    )
    # gather flags
    updated_flags = self.builder.collect_flags()

    res = anvil.server.call(
      "save_corrected_json",
      self.doc_id,
      json.dumps(self.data_obj),   # corrected_json
      updated_flags                # flags dict
    )

    alert("Saved!" if res["ok"] else res["msg"],
          title="Save result", large=not res["ok"])
