# Brief: the deer's new route

This replaces every earlier instruction about the deer, including the previous version of this file. Remove the old path completely; do not adapt it.

## The problem

The deer is the reward for the Cabin Fever achievement. In every version so far it has walked along the water's edge at the foot of the waterfall, and it reads as walking on the pond. The owner wants it off the water entirely.

## The idea

The deer is first seen small and far away, up on top of the cliff beside the waterfall. It wanders along the rim, then walks off behind the trees and is gone. A few seconds later it reappears lower down and closer, stepping out of the forest onto the bank of the pool, where it drinks and then slips back into the trees.

The gap while it is out of sight is what sells it: the visitor fills in the walk down the hillside. It also means the deer is never asked to cross open water, because each of its two appearances happens on solid ground.

All of this takes place on the left of the waterfall. Nothing the deer does should put a pixel of it to the right of x = 151.

## Assets

All in this folder, each in `_morning`, `_day`, `_afternoon`, and `_night` versions. `achievements.json` has the exact numbers; read them from there.

| File | What it is |
|---|---|
| `deer_far_<time>.png` | New. The distant deer: 2 frames of 7x6, 240 ms each, anchor (3, 5). Faces right. Frame 0 is also its standing pose. |
| `far_trees_cover_<time>.png` | New. A 16x23 patch of the far trees left of the cliff, placed at (120, 90). Drawn over the distant deer so it passes behind them. |
| `pond_bank_<time>.png` | New. A 36x4 strip of grassy bank at (118, 124), along the left edge of the pool. |
| `deer_walk_<time>.png` | Existing. The near deer walking: 4 frames of 14x10, 170 ms, anchor (6, 9). Faces right. |
| `deer_graze_<time>.png` | Existing. The near deer drinking: 6 frames of 14x10, 320 ms, anchor (6, 9). Frame 0 is the plain standing pose. |

`deer_route_check.png` shows each stage as it should look.

## The pond bank is scenery

Draw `pond_bank` always, for every visitor, whether or not the achievement is earned. It goes straight after the waterfall patch (which repaints the water every frame, so the bank must come after it) and before the deer and the near forest. Most of it sits behind the front trees; its job is to make sure there is ground, not water, under the deer.

## One visit, step by step

**Act one: on the clifftop.**

1. The distant deer starts at the left end of the path in `deer_far.placement.path`, where the tree cover hides it completely.
2. It walks right along the path, one entry per animation frame, emerging from behind the trees onto the cliff rim.
3. Near the right end of the path, a little short of the waterfall, it stops. Hold the standing frame for two to four seconds.
4. It turns (mirror the sprite) and walks back left along the same path, passing behind the trees until it is fully hidden.

While the distant deer is on screen, draw `far_trees_cover` immediately after it. Do not draw the cover at any other time.

**Intermission.** Nothing is visible for four to seven seconds.

**Act two: at the pool.**

5. The near deer starts hidden in the front trees at x = 100, feet on y = 123, facing right.
6. It walks right at about one pixel per animation frame, glimpsed through the treetops. Once, at a random point, it pauses for a second or two on the standing frame.
7. It stops at x = 144, on the tip of the bank. At that position it spans x = 138-151 with its head lowered.
8. After a short beat it plays `deer_graze` two or three times, with a brief random pause between each.
9. It turns (mirror the sprite, and mirror the anchor to (7, 9)) and walks back to x = 100, where it is hidden again.

The near deer's lowest pixel is always on y = 123. The water and the bank begin at y = 124, so it stands above the bank and never overlaps the pond.

## Draw order for this part of the scene

background, waterfall, pond bank, distant deer, far trees cover, near deer, near forest. The sasquatch sits at the same depth as the near deer.

## Rules that keep it in keeping

- Only one of the two deer sprites is ever on screen.
- The deer and the sasquatch share this stretch of forest. Never show both; if one is active when the other is due, skip that turn.
- Do not begin a visit in rain or snow. If weather starts mid-visit, finish the current act and end the visit there.
- Frequency is unchanged: every few minutes, and only once Cabin Fever is earned.
- Use the sprites for the current time of day. If it changes mid-visit, swap sets without restarting.
- Clicking either deer startles it: it turns toward the trees and leaves at double pace, and the visit ends. Build this only if the bird and sasquatch click handling makes it cheap.

## How to structure it

One state machine in the deer's own module: hidden, clifftop out, clifftop pause, clifftop back, intermission, approach, pause, drink, leave. Each state knows how it ends and what follows. Every timing, range, and position that is not in `achievements.json` goes in the site's config file with a plain name and units. The scheduler only starts a visit and asks whether one is running.

## Checking your work

Do not report anything as working unless you ran it.

- **Not on the pond:** over a full visit in test mode, record the largest x and the largest y covered by the near deer on any frame. The largest x must be 151 or less and the largest y must be 123. Report both numbers.
- **Clean entrances and exits:** capture the first and last frame of each act. In all four the deer is completely hidden, with no pop-in and no sprite left behind.
- **The cover:** with the distant deer at the left end of its path, no deer pixel is visible. With no visit running, toggling the cover on and off changes nothing on screen (it is identical to the background beneath it).
- **The bank:** present with the achievement unearned, at all four times of day, and unaffected by the waterfall animation.
- **Match the reference:** compare each stage against `deer_route_check.png`.
- **Conflicts and regression:** sasquatch and deer never overlap; no deer appears before Cabin Fever is earned; the console has no errors.

## What to send back

The changed files, the two measured numbers, screenshots of each stage by day and by night, and a short report that leads with anything the owner must decide or that you could not verify.
