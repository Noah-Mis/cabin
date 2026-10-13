# Brief: add achievements to the cabin window website

## What this is

The site is a pixel art scene: the view from a log cabin window, with a terminal command line at the bottom, built as a static site in plain HTML, CSS, and JavaScript modules. Visitors can already watch birds fly past, see a sasquatch peek from the trees, click a folder to read the owner's resume, and type commands.

Your job is to add achievements. A visitor earns them by interacting with the scene, and each one permanently changes something in the scene for that visitor: birds turn gold, a yeti starts appearing, a trophy lands on the window sill. The rewards are the point. An achievement that only prints a message is half done.

All the art is finished and in this folder. Do not draw, recolour, or substitute anything; if an asset looks wrong or is missing, say so.

## What you are given

- `achievements.json`: the source of truth. It lists the 13 achievements (id, name, description, the stat each one watches, its goal, its reward, and which assets the reward uses), the metadata for every sprite (file names, frame size, frame count, speed, anchor, placement), the badge sheet layout, the unlock sign layout, the green terminal theme colours, and the positions of the clickable stars. Read values from it at runtime instead of copying numbers into code.
- Sprite sheets for every reward, in the same format the site already uses: one row of equal frames, with `_morning`, `_day`, `_afternoon`, `_night` versions for things outdoors and a plain plus `_night` version for things on the sill.
- `badges.png`: 14 frames of 16x16. Frames 0-12 are the achievements in the order listed in the JSON; frame 13 is the locked badge.
- `achievement_sign.png`: a wooden sign, 132x24, shown when something unlocks. It has a slot for the badge and a blank area for text.
- `achievements_preview.png`: a reference picture with every reward switched on, by day and by night.

Before writing code, read the existing site's modules so that what you add follows the same structure: how scene elements register themselves, how events are scheduled, how commands are defined, and how time of day and weather are tracked. Match those patterns.

## The achievements

| Id | Earned by | What changes afterwards |
|---|---|---|
| `first_sighting` | Clicking the sasquatch once | Every later appearance uses `sasquatch_wave` instead of `sasquatch_peek` |
| `bird_watcher` | Clicking 15 birds | Every bird uses the `_shiny` sheets and drops a `sparkle` behind it every few frames |
| `cryptid_hunter` | Clicking the sasquatch 5 times | About one appearance in five is the yeti (`yeti_peek`, or `yeti_wave` since the first achievement is always earned by then) |
| `caffeinated` | Clicking the coffee cup 10 times | The cup is drawn with `mug_camp` |
| `case_closed` | Opening all four tabs in the folder pop-up | The folder uses the gold-seal art everywhere: `folder_reviewed` at rest, `folder_reviewed_place` when the `whoami` command brings it onto the sill, `folder_reviewed_open` when it opens and `folder_reviewed_close` when it closes |
| `night_owl` | Being on the site while it is night | `shooting_star` plays at random spots, every 30-90 seconds at night |
| `around_the_clock` | Having seen all four times of day | `aurora` fades in slowly on roughly one night in three and loops (60 frames, about 10 seconds a cycle) |
| `storm_chaser` | Having seen both rain and snow | `rainbow` fades in when rain ends and out about 20 seconds later |
| `stargazer` | Clicking 10 stars | `constellation_sasquatch` is drawn in the night sky |
| `power_user` | Using every command listed by `help` | A `theme green` command becomes available, using the colours in the JSON |
| `cabin_fever` | 10 minutes of the page being open and visible, in total | A deer event: `deer_walk` in, `deer_graze`, `deer_walk` out, every few minutes |
| `woodsman` | Earning the other twelve | `trophy` sits on the sill, with an occasional `sparkle` |

Details that are easy to get wrong:

- **Clicks count on what the visitor can see.** A click scores only if it lands on the creature while it is on screen. Convert the click from screen pixels to native canvas pixels first. Use a forgiving hit area: the sprite's frame plus a few pixels of padding, because these targets are small and moving. The sasquatch counts once per appearance, however many times he is clicked.
- **Stars are clickable only at night,** at the positions in `star_click_targets`, with a hit radius of about 4 native pixels. Each star counts once per night. Give a clicked star a brief `sparkle` so the visitor knows it registered.
- **Clicking the cup should feel like something.** Briefly hide the steam, or print a short line in the terminal, so the visitor notices there is something to click.
- **Time of day and weather count when they are shown,** whether they came from the clock, a timer, or a command.
- **Time on the page counts only while the tab is visible,** and adds up across visits.
- **Rewards apply immediately** when earned, and again on every later visit, without a reload.
- **Draw order.** The JSON says what each new sprite is clipped by or drawn behind. The aurora goes under the stars; the constellation, shooting stars, and anything else in the sky are clipped by the sky mask; the deer, like the sasquatch, is drawn before the near forest so the trees overlap it; sill items are drawn after the window frame.

## Unlocking

When an achievement is earned, show `achievement_sign.png` near the top of the view for about four seconds, with the badge in its slot and the achievement's name as text in the blank area, then let it slide away. Also print a line in the terminal with the name and what changed. If two unlock together, show them one after another, not on top of each other. The text is real text placed over the sign, not baked into an image.

## Commands

- `badges`: list all 13. Earned ones show name, description, and reward. Unearned ones show `???` for the name and a progress hint for countable ones, for example `Bird Watcher 17/50` once the first bird has been clicked. Do not reveal an achievement's reward before it is earned.
- `reset`: after a confirmation, clear all progress and return the scene to its starting state.

Add both to `help`. Decide whether `badges` and `reset` count toward `power_user`, and state the rule in the code where the list is defined; it must be possible to earn.

## Saving progress

There is no server. Store progress in the browser's `localStorage` under one versioned key, as a single object holding the counters and the list of unlocked ids. Guard every read and write, because storage can be unavailable or throw; in that case the site must still work, with achievements lasting only for the visit. If the stored data is missing or malformed, start fresh instead of failing.

## How to structure it

The owner is a computer science student who maintains this code, and the existing site is deliberately modular. Keep it that way.

- **Achievements are data.** One module defines them, driven by `achievements.json`: each has an id and a test against the saved stats. Adding a fourteenth should mean one new entry and, if it has a reward, one new reward function.
- **One function reports events.** The rest of the site calls something like `track(stat, value)` when a bird is clicked or a tab is opened. Game code never mentions specific achievements.
- **One place answers "is this unlocked?".** Scene elements ask that question when choosing a sprite (for example, the bird module picking the shiny sheet). No module reads storage directly except the progress store.
- **Each reward lives with the thing it changes.** The yeti logic belongs with the sasquatch, the rainbow with the weather, the trophy with the sill items.
- **No magic numbers.** Positions and sizes come from the JSON; tunables such as the yeti chance, the aurora chance, and timings sit in the site's existing config file with plain names.

## Checking your work

Verification is part of the task. Do not describe something as working unless you ran it.

- **Give yourself a way to test without grinding.** A debug command or URL parameter, off by default, that sets any stat or unlocks any achievement. Use it to exercise every reward.
- **For each of the 13:** start from a reset state, trigger it the real way at least once (click the real sasquatch; for the 15 birds, click a few for real and set the rest), confirm the sign and terminal line appear once, confirm the reward shows in a screenshot, reload, and confirm both the unlock and the reward persist.
- **Compare each reward against `achievements_preview.png`** for position and layering, by day and by night.
- **Check the edges:** two achievements unlocking at once; clicking where a creature was a moment ago; clicking a star by day; `reset` followed by earning something again; storage disabled; a stored value from a hand-edited or older version.
- **Check nothing regressed:** with no achievements earned, the site looks and behaves exactly as it did before your change, and the console is free of errors.

## What to send back

The changed and new files, the test notes for all 13, screenshots of the scene with every reward on by day and by night, and a short report that leads with anything the owner must decide or that you could not verify.
