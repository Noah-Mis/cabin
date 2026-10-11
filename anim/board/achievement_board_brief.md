# Brief: the achievement board

## What this is

The cabin window site already has achievements: visitors earn them by interacting with the scene, progress is saved in the browser, and a `badges` terminal command lists them. This task replaces that command with something in the scene itself: a small pin board hanging on the window's right-hand log. It shows progress at a glance, and clicking it opens a pop-up with every achievement.

You have built this kind of thing here before. The folder on the sill is a clickable scene item that shows a black outline on hover and opens a pop-up. The board should behave like a sibling of the folder: same hover outline, same way of opening and closing, same handling of scale, focus, and the dimmed backdrop. Reuse that code and those patterns; where this brief is silent, do what the folder does.

All art is finished and in this folder. Do not draw or alter any of it. If something looks wrong or is missing, say so.

## What you are given

- `board_layout.json`: every position and size, for the board in the scene and for the pop-up. Read from it at runtime.
- `achievement_board.png` and `achievement_board_night.png` (18x31): the board, with a nail, string, wooden frame, green felt, and thirteen empty pin holes. Use the night file with the night window, cross-fading like other time-of-day assets.
- `board_pin_lit.png` (2x2) and `board_star_lit.png` (4x3): a gold pin, and a gold star for the top slot.
- `achievement_board_outline.png` (20x33): a ready-made black outline of the board's silhouette, positioned one pixel up and left of the board. Use it only if that is how the existing hover outlines work; if they are generated in code, use that method and ignore this file.
- `popup_board.png` (288x164): the pop-up, with a title plaque reading ACHIEVEMENTS, thirteen recessed slots, a progress trough, a pinned paper note, and a close button. Everything that changes is left blank.
- `board_slot_selected.png` (30x30): a gold frame marking the selected slot.
- `board_mockup_scene.png` and `board_mockup_popup.png`: reference pictures of both, with six achievements earned and one selected.
- From the existing achievement assets: `badges.png` (frames 0-12 are the achievements in order, frame 13 is the locked badge) and `achievements.json` (names, descriptions, rewards, goals).

## The board in the scene

Draw the board at the canvas position in the layout file. It hangs on the right-hand frame log, so it is drawn after the window frame, with the other things attached to the cabin.

It is a live display, not a static picture:

- For each of the first twelve achievements, in the order they appear in `achievements.json`, draw `board_pin_lit.png` at the matching position in `board.pin.positions` once it is earned. Unearned ones show the empty hole already in the art.
- For the thirteenth, Woodsman, draw `board_star_lit.png` at `board.star.position`.
- When an achievement unlocks, its pin appears at once, with a single `sparkle` on it (the sparkle sprite from the achievement assets) so the eye is drawn there.

Hovering shows the black outline and the pointer cursor, exactly as the folder does. The clickable area is the board's bounding box. It must be reachable and operable from the keyboard in the same way as the folder.

## The pop-up

Clicking the board opens `popup_board.png` centred at the canvas position in the layout file, over the same dark backdrop the folder pop-up uses, at the canvas's whole-number scale with smoothing off.

**Slots (left side).** There are thirteen, listed in `popup.slots` in achievement order. In each, draw that achievement's badge at `badge_x, badge_y` if it is earned, or the locked badge if it is not.

**Selection.** One slot is always selected, shown by drawing `board_slot_selected.png` at the slot's position plus `selected_offset`. Clicking a slot selects it; arrow keys move the selection through the grid in reading order. On opening, select the most recently earned achievement, or the first slot if none are earned.

**Detail note (right side).** Shows the selected achievement:

- `detail_badge_2x`: its badge drawn at twice size (32x32, nearest-neighbour), or the locked badge.
- `detail_name`: its name.
- `detail_description`: a small heading, "HOW", then how to earn it.
- `detail_reward`: a small heading, "REWARD", then what it changes.

For an achievement that has not been earned, keep the mystery the `badges` command had: show `???` for the name and the reward. Show the description only once the visitor has made some progress toward it, and for countable ones show that progress, for example `17 / 50`. Before any progress, show a single line such as "Not yet discovered."

**Progress.** Fill the `progress_bar` region from the left in proportion to achievements earned, using `progress_fill` with a one-pixel `progress_fill_light` line along its top. In `progress_text`, write "N of 13 earned".

**Text.** All words are real text placed over the regions, never baked into images, sized for the screen and not the native pixel grid, in the same font the folder pop-up uses. Colours are in the layout file: dark ink on the paper note, the heading red for "HOW" and "REWARD", and the pale felt colour for the progress line.

**Closing.** The X button, Escape, or a click outside the board, the same as the folder.

**Small screens.** Follow whatever the folder pop-up does when the scaled art would be too small to read.

## Retiring the `badges` command

- Remove `badges` from the command table and from `help`.
- If someone types it anyway, print one line pointing them to the board by the window. Old habits and old screenshots will send people there.
- `power_user` is earned by using every command in `help`. Make sure removing a command does not leave that achievement impossible, and that a visitor who had already used `badges` is not set back.
- Keep `reset`. After a reset, every pin on the board is empty again without a reload.

## How to structure it

Keep to the site's existing modular layout. The board is one scene element and one pop-up, built the way the folder's are. It reads achievement state through the same single "is this unlocked?" function and progress store that everything else uses, and never touches storage directly. If the folder pop-up and this one share behaviour (backdrop, scaling, focus handling, closing), move that into one shared piece instead of copying it, so a third pop-up later is cheap. No positions or sizes in code; they come from `board_layout.json`.

## Checking your work

Do not report anything as working unless you ran it.

- **Scene:** with nothing earned, the board matches the left panel of `board_mockup_scene.png` apart from the pins. Earn achievements with the existing debug switch and confirm each of the twelve pins and the star lights in its own position. Check day and night.
- **Hover:** the outline matches the folder's in colour and thickness, appears and disappears cleanly, and does not shift the board by a pixel.
- **Pop-up:** compare against `board_mockup_popup.png` with the same six earned (indices 0, 1, 3, 5, 6, 8) and index 1 selected. Slots, selection frame, large badge, and progress fill should line up exactly; text will differ only by font.
- **States:** nothing earned; everything earned; a countable achievement partway; an achievement unlocking while the pop-up is open (the slot, pin, progress bar, and note all update without reopening).
- **Input:** mouse, keyboard only, and touch. Escape closes it. Focus returns to the terminal afterwards, as it does for the folder.
- **Regression:** the folder still opens and closes as before; the unlock sign and terminal line still appear; the console has no errors.

## What to send back

The changed and new files, screenshots of the board (idle, hovered, night) and of the pop-up (nothing earned, some earned, all earned), and a short report that leads with anything the owner must decide or that you could not verify.
