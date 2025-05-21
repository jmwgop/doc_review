# field_config.py  (CLIENT module)
#
# Central place for UI behaviour rules.
# ------------------------------------------------------------
# 1. EXCLUDE_PATHS   → any field that matches is *not* rendered.
# 2. FIELD_WIDGETS   → per-field widget overrides.
#
# Path syntax:
#   • Dot notation for dict keys        e.g.  "document_details.analysis"
#   • Use [*] to wildcard list indices  e.g.  "parties[*].address"
# Matching is plain string equality after substituting indices with [*].
# ------------------------------------------------------------

# ---------- 1. Hide fields from the reviewer UI ----------
EXCLUDE_PATHS = [
  # Don’t surface party addresses – users rarely edit them here
  "parties[*].address",
  # Depth info seldom needs manual edits
  # Long auto-analysis blob – keep it, just don’t show it
]

# ---------- 2. Force widget types for certain fields ----------
FIELD_WIDGETS = {
  # special_provisions → dropdown for controlled vocab
  "special_provisions[*].provision_type": {
    "type": "dropdown",
    "choices": [
      "continuous_operations",
      "surface_retained_acreage",
      "depth_retained_acreage",
      "pugh_clause",
      "shut_in_royalty",
    ],
  },

  # Dates – render with DatePicker
  "instrument_date":          {"type": "datepicker"},
  "primary_term.start_date":  {"type": "datepicker"},  # example of nested path

  # Long-form narrative fields – force TextArea even if short now
  "legal_description":        {"type": "textarea"},
  "document_details.open_interest_reasoning": {"type": "textarea"},
  "document_details.lease_complexity_reasoning": {"type": "textarea"},
  "document_details.analysis": {"type": "textarea"},
}

# ---------- Helper ---------------------------------------------------------
ALLOWED_WIDGET_TYPES = {"textbox", "textarea", "dropdown", "datepicker"}
