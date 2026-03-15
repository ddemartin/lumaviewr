# Pix42 — Claude Code Instructions

## Changelog

Whenever a new feature is implemented or a significant fix is made, update
`_server/version.json` — specifically the `changelog` field — to reflect the
change. Keep the text concise and user-facing (what the user sees, not internal
implementation details).

The `changelog` field is displayed in the in-app update dialog, so write it
from the user's perspective (e.g. "Added HEIC/HEIF support" not
"Implemented HeifDecoder via pillow-heif").
