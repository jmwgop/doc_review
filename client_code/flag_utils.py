# flag_utils.py  (CLIENT module)

from anvil import CheckBox

# ---------------------------------------------------------------------------
#  Public helpers
# ---------------------------------------------------------------------------

def create_flag_checkbox(path: str, flagged: bool = False) -> CheckBox:
  """
    Return a CheckBox configured as a per-field flag.

    Args:
        path   : The dot-notation path for the field (e.g. "parties[0].name").
        flagged: Initial checked state (from stored flags).

    Returns:
        anvil.CheckBox – fully configured widget (tiny, tooltip, etc.)
    """
  cb = CheckBox(checked=flagged, tooltip=f"Flag field: {path}")
  cb.role = "flag-checkbox"        # let you style globally via theme CSS
  cb.text = ""                     # no label; purely an icon-sized box
  cb.spacing_above = "none"
  cb.spacing_below = "none"
  return cb


def collect_flags(path_to_checkbox: dict) -> dict:
  """
    Walk the path→checkbox dict built by the form and return a flat flags dict.

    Only paths whose checkbox is checked are returned.

    Example output:
        {
            "legal_description": true,
            "tracts[1].aliquot": true
        }
    """
  return {path: True
          for path, cb in path_to_checkbox.items()
          if getattr(cb, "checked", False)}


def apply_flags(path_to_checkbox: dict, saved_flags: dict):
  """
    Set each checkbox's checked state based on an existing saved_flags dict.
    """
  for path, cb in path_to_checkbox.items():
    cb.checked = bool(saved_flags.get(path, False))
