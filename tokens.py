"""Design tokens and theme constants for CompostMitra Linnaean Herbarium UI.

World: The Linnaean Herbarium (Archival Cream & Deep Forest Moss)
Features:
  - Surface Duality: Warm Parchment Canvas + Integrated Midnight Evergreen Consoles
  - Typography: Fraunces (Editorial Display Serif) + Plus Jakarta Sans + Space Mono
  - Badges: Soft organic pills with botanical leaf glyphs

All color values are centralized strictly here. No other python file
should contain raw hex strings.
"""

from __future__ import annotations

# Core Brand Palette (The Linnaean Herbarium)
COLOR_PRIMARY = "#1B4D3E"       # Deep Linnaean spruce / moss ink
COLOR_BG = "#F6F4EB"            # Warm French archival vellum / parchment
COLOR_SAGE = "#E5EFE7"          # Soft botanical sage wash
COLOR_SECONDARY = "#2E6F40"     # Verdigris botanical leaf green
COLOR_ACCENT = "#C88A35"        # Weathered amber resin / brass
COLOR_TEXT = "#15221B"          # Deep forest naturalist ink
COLOR_TEXT_MUTED = "#5A6B60"    # Muted botanical slate
COLOR_CARD_BG = "#FCFAF3"       # Pressed ivory specimen card
COLOR_BORDER = "#DED9C8"        # Warm deckled hairline border
COLOR_BADGE_BG = "#E5EFE7"      # Soft botanical pill background
COLOR_BADGE_TEXT = "#1B4D3E"    # Linnaean pill text
COLOR_WARN_BG = "#FDF6E2"       # Warm amber pill background
COLOR_WARN_TEXT = "#8C5E1E"     # Amber resin pill text
COLOR_SUCCESS = "#2E6F40"       # Verdigris leaf green

# Integrated Dark Consoles (Midnight Evergreen Slate)
COLOR_CONSOLE_BG = "#0E1813"     # Midnight evergreen slate
COLOR_CONSOLE_BORDER = "#1F3327" # Dark console structural border
COLOR_CONSOLE_TEXT = "#E1EFE6"   # Phosphor / parchment readout text
COLOR_CONSOLE_MUTED = "#768E80"  # Console secondary text
COLOR_CONSOLE_ACCENT = "#4EBA6F" # Luminescent sprout lime

# Typography & Spacing
FONT_DISPLAY = "'Fraunces', Georgia, serif"
FONT_FAMILY = "'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
FONT_MONO = "'Space Mono', 'Courier New', monospace"
FONT_SIZE_BASE = "16px"
FONT_SIZE_LG = "18px"
FONT_SIZE_XL = "24px"
FONT_SIZE_TITLE = "32px"
BORDER_RADIUS_CARD = "14px"
BORDER_RADIUS_PILL = "9999px"
