# Folder pop-up: notes for implementation

Clicking the folder on the sill opens a pop-up styled as that same folder lying open, seen from above. The art is in this directory; `popup_layout.json` has every position and size. `popup_mockup_<tab>.png` shows the intended result for each tab, with the real content drawn in.

## What the art provides

- `popup_folder.png` (288x164): the open folder with all four tabs in their inactive state and every content area left blank.
- `popup_tab_<name>_active.png` (40x14): the lit version of each tab. Draw the active one over the folder at the tab position in the layout file.
- Blank regions, listed under `regions` in the layout file:
  - `page`: the large sheet on the right. The main content for the selected tab goes here.
  - `photo`: the clipped photograph, for a portrait.
  - `card`: the index card with a red header, for name and a one-line summary.
  - `sticky`: the yellow note, for a few links or quick facts.
  - `stamp`: the red stamp outline, for one or two words (for example a graduation year).
  - `close`: the red X button.

## How it should behave

1. On click, play `folder_open` on the sill, then fade in a dark backdrop over the scene (`colors.backdrop`) and show the pop-up centred at the canvas position in the layout file, scaled by the same whole-number factor as the canvas with smoothing off.
2. Tabs switch what is shown in `page`. The left side (photo, card, sticky, stamp) stays the same on every tab.
3. Close on the X, on Escape, or on a click outside the folder; then play `folder_open` backwards.

## Text

Do not bake text into images. Render real HTML text positioned over each region, so it is selectable, readable by screen readers, and easy to edit. Region coordinates are native pixels; multiply by the canvas scale. Text should be sized for the screen, not the native grid: aim for body text around 14-16 CSS pixels, in a monospace or pixel-style web font, coloured `colors.ink` on paper and `colors.ink_dark` on tan. Section headings on the page use `colors.stamp_red`. The `page` region scrolls when its content is longer than the sheet.

Keep all pop-up content in one data file (for example `content/folder.js`) with a field per tab and per left-side region, so it can be edited without touching layout code. The resume tab should also offer a link to download the resume as a PDF.

On narrow screens where the scaled folder would be too small to read, show the same content in a plain single-column panel using the same colours.

## Content

`folder_content.json` holds all the words, taken from the owner's resume: the index card, stamp, sticky note, and the sections for each tab. Render from this file and do not hard-code or reword any of it. Sections can contain `text` (paragraphs), `items` (a title, a muted `meta` line, and bullet `points`), `bullets`, `tags`, and `links`. The resume PDF linked from the sticky note and the Contact tab is supplied separately by the owner. The photo region has no image yet; leave the placeholder until the owner provides one.
