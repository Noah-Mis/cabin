# Achievement checks

## Each achievement, earned from a reset state, then reloaded

- PASS: **Something in the Trees** (`first_sighting`): clicked the real sasquatch twice in one appearance: sasquatchClicks = 1. Earned: True; sign shown 1x, terminal line 1x; reward: next appearance uses sasquatch_wave (31/31 visible px match); after reload: still earned True, reward True, no new sign True
- PASS: **Bird Watcher** (`bird_watcher`): 3 real bird clicks counted (3), set to 49, the 50th clicked for real. Earned: True; sign shown 1x, terminal line 1x; reward: birds use bird_flap_shiny (exact: True); after reload: still earned True, reward True, no new sign True
- PASS: **Cryptid Hunter** (`cryptid_hunter`): sasquatchClicks 9 -> 10 by clicking the real sasquatch. Earned: True; sign shown 1x, terminal line 1x; reward: next appearance uses yeti_wave (31/31 visible px match); after reload: still earned True, reward True, no new sign True
- PASS: **Caffeinated** (`caffeinated`): 25 real sips from the cup (25); a click mid-sip did not count (1). Earned: True; sign shown 1x, terminal line 1x; reward: mug_camp drawn pixel-exact at its JSON placement; after reload: still earned True, reward True, no new sign True
- PASS: **Smoke Break** (`smoke_break`): cig, clicked the pack, let all 58.1 s play (not earned half-way: True). Earned: True; sign shown 1x, terminal line 1x; reward: ashtray drawn pixel-exact at its JSON placement; after reload: still earned True, reward True, no new sign True
- PASS: **Case Closed** (`case_closed`): opened the folder and clicked the other three tabs: tabsSeen = ['about', 'resume', 'projects', 'contact']. Earned: True; sign shown 1x, terminal line 1x; reward: gold-seal folder at rest / opening / closing pixel-exact: [True, True, True]; after reload: still earned True, reward True, no new sign True
- PASS: **Night Owl** (`night_owl`): `time night`: not earned mid-fade (True), earned once night is shown. Earned: True; sign shown 1x, terminal line 1x; reward: shooting stars fire at night (shootingstar: fired.); after reload: still earned True, reward True, no new sign True
- PASS: **Around the Clock** (`around_the_clock`): morning (start) then day, afternoon, night: timesSeen = ['morning', 'day', 'afternoon', 'night']. Earned: True; sign shown 1x, terminal line 1x; reward: aurora shows on a night it is rolled (6937 sky px change); after reload: still earned True, reward True, no new sign True
- PASS: **Storm Chaser** (`storm_chaser`): rain (not enough on its own: True), clear, snow: weatherSeen = ['rain', 'snow']. Earned: True; sign shown 1x, terminal line 1x; reward: rainbow fades in when rain ends (1696 px); after reload: still earned True, reward True, no new sign True
- PASS: **Stargazer** (`stargazer`): 10 real star clicks (the same star twice counted 1). Earned: True; sign shown 1x, terminal line 1x; reward: constellation in the night sky (27/27 px exact); after reload: still earned True, reward True, no new sign True
- PASS: **Power User** (`power_user`): 5 of 6 commands: not yet (True); `theme` unknown before (no such command "theme". ...); after `badges`: `theme green` -> 'green screen on.', terminal background rgb(12, 20, 14) (JSON #0C140E). Earned: True; sign shown 1x, terminal line 1x; reward: `theme green` available ('green screen on.'); after reload: still earned True, reward True, no new sign True
- PASS: **Woodsman** (`woodsman`): 11 unlocked by debug (no trophy yet: True), the 12th (Night Owl) for real. Earned: True; sign shown 1x, terminal line 1x; reward: trophy drawn pixel-exact at its JSON placement; after reload: still earned True, reward True, no new sign True

## Rewards drawn in place (site vs achieve.py-style reference)

- PASS: mug_camp_day (day): 378 px changed on the site, 378 in the reference, 100% in the same place; colours where the scenes behind agree: 378/378 exact, 378/378 within 1 - 6 reward px are under things the site draws in front (e.g. clouds), not compared
- PASS: ashtray_day (day): 240 px changed on the site, 240 in the reference, 100% in the same place; colours where the scenes behind agree: 240/240 exact, 240/240 within 1
- PASS: trophy_day (day): 251 px changed on the site, 251 in the reference, 100% in the same place; colours where the scenes behind agree: 251/251 exact, 251/251 within 1
- PASS: folder_reviewed_day (day): 66 px changed on the site, 66 in the reference, 100% in the same place; colours where the scenes behind agree: 66/66 exact, 66/66 within 1
- PASS: mug_camp_night (night): 378 px changed on the site, 378 in the reference, 100% in the same place; colours where the scenes behind agree: 378/378 exact, 378/378 within 1 - 6 reward px are under things the site draws in front (e.g. clouds), not compared
- PASS: ashtray_night (night): 240 px changed on the site, 240 in the reference, 100% in the same place; colours where the scenes behind agree: 240/240 exact, 240/240 within 1
- PASS: trophy_night (night): 256 px changed on the site, 256 in the reference, 100% in the same place; colours where the scenes behind agree: 256/256 exact, 256/256 within 1
- PASS: folder_reviewed_night (night): 66 px changed on the site, 66 in the reference, 100% in the same place; colours where the scenes behind agree: 66/66 exact, 66/66 within 1
- PASS: constellation (night): 32 px changed on the site, 32 in the reference, 100% in the same place; colours where the scenes behind agree: 21/32 exact, 32/32 within 1 - the site also twinkles stars on top; 19 reward px are under things the site draws in front (e.g. clouds), not compared
- PASS: aurora (night): 6343 px changed on the site, 6344 in the reference, 100% in the same place; colours where the scenes behind agree: 4669/6343 exact, 6343/6343 within 1 - translucent; the site draws stars and clouds over it; 840 reward px are under things the site draws in front (e.g. clouds), not compared
- PASS: shooting_star (night): 12 px changed on the site, 12 in the reference, 100% in the same place; colours where the scenes behind agree: 11/12 exact, 12/12 within 1
- PASS: folder_reviewed_place (day): 66 px changed on the site, 66 in the reference, 100% in the same place; colours where the scenes behind agree: 66/66 exact, 66/66 within 1
- PASS: rainbow (day): 1353 px changed on the site, 1353 in the reference, 100% in the same place; colours where the scenes behind agree: 565/1353 exact, 1353/1353 within 1 - translucent; 142 reward px are under things the site draws in front (e.g. clouds), not compared
- PASS: sasquatch_wave (day): 31 px changed on the site, 31 in the reference, 100% in the same place; colours where the scenes behind agree: 31/31 exact, 31/31 within 1 - behind the near forest
- PASS: yeti_wave (night): 23 px changed on the site, 23 in the reference, 100% in the same place; colours where the scenes behind agree: 23/23 exact, 23/23 within 1 - behind the near forest
- PASS: yeti_peek (day): 27 px changed on the site, 27 in the reference, 100% in the same place; colours where the scenes behind agree: 27/27 exact, 27/27 within 1 - behind the near forest
- PASS: deer_graze (night): 38 px changed on the site, 38 in the reference, 100% in the same place; colours where the scenes behind agree: 38/38 exact, 38/38 within 1 - behind the near forest; 5 reward px are under things the site draws in front (e.g. clouds), not compared
- PASS: deer_walk (day): 18 px changed on the site, 18 in the reference, 100% in the same place; colours where the scenes behind agree: 18/18 exact, 18/18 within 1 - behind the near forest
- PASS: bird_flap_shiny (day): 35 px changed on the site, 35 in the reference, 100% in the same place; colours where the scenes behind agree: 35/35 exact, 35/35 within 1
- PASS: bird_far_shiny (day): 7 px changed on the site, 7 in the reference, 100% in the same place; colours where the scenes behind agree: 7/7 exact, 7/7 within 1
- PASS: unlock sign: art and badge pixel-exact at 5x, at art y 28 (4 below the window opening), name as real text: "Bird Watcher"

## Edges

- PASS: two unlocks at once: terminal lines ['achievement unlocked: Storm Chaser. A rainbow shows over the falls after rain.', 'achievement unlocked: Woodsman. A gold trophy on the sill.']; signs shown one after the other (['Storm Chaser', 'Woodsman']), 4909 ms apart (each takes 4900 ms)
- PASS: clicking where the bird was 0.6 s ago, or on empty sky: 0 counted; on the bird now: 1
- PASS: stars by day: 0 counted; the same star on two different nights: 2 (once per night)
- PASS: `reset` asks first (this erases every achievement and all pr...; still 13 earned); `reset yes`: 0 earned, stats {'timesSeen': ['day']}; the scene matches a first visit (0 px differ); earning again shows its sign: ['Something in the Trees']
- PASS: storage throws: achievements still work in the visit (True), saved=False, gone after reload (True), console clean ([])
- PASS: saved data "not JSON": starts cleanly (unlocked [], stats {'timesSeen': ['day']}), console clean
- PASS: saved data "older version": starts cleanly (unlocked [], stats {'timesSeen': ['day']}), console clean
- PASS: saved data "wrong types": starts cleanly (unlocked [], stats {'mugClicks': 24, 'timesSeen': ['day']}), console clean
- PASS: saved data "a number": starts cleanly (unlocked [], stats {'timesSeen': ['day']}), console clean
- PASS: visible time: 3 s counted in ~3 s; 0 s while the tab was hidden; 5 s after a reload (adds up across visits); 597 s + 3 real seconds earns Cabin Fever: True

## Every reward on

- PASS: day: every reward on at once, screenshot saved (console: clean)
- PASS: night: every reward on at once, screenshot saved (console: clean)
