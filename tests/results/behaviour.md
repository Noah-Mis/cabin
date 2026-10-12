# Behaviour checks

## Layout and crispness

- PASS: desktop_1920x1080: scale 6 (filling needs 6), whole-number=True, fills the screen=True, window centred=True (+0.0 px), window, sill, board, terrarium pot and journal fully visible above the prompt=True, prompt 32 px tall=True, every visible pixel a clean 6x6 block=True
- PASS: fullscreen_1920x1200: scale 6 (filling needs 7), whole-number=True, fills the screen=False, window centred=True (+0.0 px), window, sill, board, terrarium pot and journal fully visible above the prompt=True, prompt 32 px tall=True, every visible pixel a clean 6x6 block=True
- PASS: laptop_1366x768: scale 4 (filling needs 5), whole-number=True, fills the screen=False, window centred=True (+0.0 px), window, sill, board, terrarium pot and journal fully visible above the prompt=True, prompt 32 px tall=True, every visible pixel a clean 4x4 block=True
- PASS: hidpi_1440x900_dpr2: scale 9 (filling needs 10), whole-number=True, fills the screen=False, window centred=True (+0.0 px), window, sill, board, terrarium pot and journal fully visible above the prompt=True, prompt 32 px tall=True, every visible pixel a clean 9x9 block=True
- PASS: odd_1000x700_dpr1.25: scale 4 (filling needs 5), whole-number=True, fills the screen=False, window centred=True (+0.0 px), window, sill, board, terrarium pot and journal fully visible above the prompt=True, prompt 32 px tall=True, every visible pixel a clean 4x4 block=True
- PASS: phone_390x844_dpr3: scale 3 (filling needs 15), whole-number=True, fills the screen=False, window centred=True (+0.0 px), window, sill, board, terrarium pot and journal fully visible above the prompt=True, prompt 34 px tall=True, every visible pixel a clean 3x3 block=True
- PASS: phone_landscape_844x390_dpr3: scale 8 (filling needs 8), whole-number=True, fills the screen=True, window centred=True (+0.0 px), window, sill, board, terrarium pot and journal fully visible above the prompt=True, prompt 28 px tall=True, every visible pixel a clean 8x8 block=True
- PASS: phone_landscape_667x320_dpr2: scale 4 (filling needs 5), whole-number=True, fills the screen=False, window centred=True (+0.0 px), window, sill, board, terrarium pot and journal fully visible above the prompt=True, prompt 28 px tall=True, every visible pixel a clean 4x4 block=True
- PASS: phone_landscape_915x360_dpr2.625: scale 6 (filling needs 8), whole-number=True, fills the screen=False, window centred=True (-0.4 px), window, sill, board, terrarium pot and journal fully visible above the prompt=True, prompt 28 px tall=True, every visible pixel a clean 6x6 block=True

## Commands (typed into the terminal, test mode, compared with a page that did not run them)

- PASS: `bird` is not a command any more: scene unchanged (0 differing pixels), bubble said "no such command "bird". type "help" to see what you can do."
- PASS: `sasquatch` is not a command any more: scene unchanged (0 differing pixels), bubble said "no such command "sasquatch". type "help" to see what you can do."
- PASS: `wind` is not a command any more: scene unchanged (0 differing pixels), bubble said "no such command "wind". type "help" to see what you can do."
- PASS: `farbird` is not a command any more: scene unchanged (0 differing pixels), bubble said "no such command "farbird". type "help" to see what you can do."
- PASS: `time morning`: mid-fade frame differs from both palettes; 3.5 s later the frame is identical to a page started at morning (0 differing pixels), so every layer swapped
- PASS: `time afternoon`: mid-fade frame differs from both palettes; 3.5 s later the frame is identical to a page started at afternoon (0 differing pixels), so every layer swapped
- PASS: `time night`: mid-fade frame differs from both palettes; 3.5 s later the frame is identical to a page started at night (0 differing pixels), so every layer swapped
- PASS: `weather rain`: once it has built up or thinned out, identical to a page started with rain; terminal said "it starts to rain."
- PASS: `weather snow`: once it has built up or thinned out, identical to a page started with snow (apart from how much snow has settled on the trees); terminal said "it starts to snow."
- PASS: `weather clear`: once it has built up or thinned out, identical to a page started with clear; terminal said "the sky clears."
- PASS: `weather rain` starts light: 183 rain pixels in the window the moment it starts, against 917 in full rain; drops join a line at a time (14 lines, then 41 10 s in, 49 at full) and none vanishes on the way (lines lost: none)
- PASS: `weather clear` thins the rain out: 49 lines, 41 10 s later, none coming back (none), and none left after 20 s (0 rain pixels)
- PASS: `weather snow` fades in: colour change in the window, averaged over each 2 s, climbs steadily: [13029, 18798, 24492, 30593, 35972, 42347, 48236, 54039, 59706, 64755]

## Terminal

- PASS: input has focus on load, so typing works straight away
- PASS: clicking the scene keeps focus in the input
- PASS: no bubble before anything is typed (test mode has no greeting)
- PASS: `help` shows one bubble listing help, clear, whoami and not bird, wind, sasquatch, cig, time, weather, reset, badges, ls, rm, touch
- PASS: unknown command replaces the help bubble with one hint line: ['no such command "dance". type "help" to see what you can do.']
- PASS: there is only ever one bubble
- PASS: a new command replaces the bubble: ['it starts to snow.']
- PASS: an empty command removes the bubble and shows nothing else
- PASS: a blank command does the same
- PASS: `time noon` shows its usage: "usage: time morning|day|afternoon|night|auto"
- PASS: `weather fog` shows its usage: "usage: weather rain|snow|clear"
- PASS: 60 rapid commands: still one bubble holding only the last reply, scene kept running, no errors
- PASS: after the last `time day` the scene is day
- PASS: up/down recall: 'help', 'time day', back to ''
- PASS: `time auto` returns to the clock (local hour 11 -> day)
- PASS: the `time auto` reply is showing
- PASS: `clear` removes the bubble

## Coffee mug: hover outline and sip (test mode)

- PASS: day: hovering the cup draws a black outline (86 px, all black True, around the cup and not the steam True) with a "pointer" cursor
- PASS: day: the click plays mug_sip on top of everything (frame 3 pixel-exact, 836 of its px over the sill and frame); a click mid-sip is ignored (1 sip counted)
- PASS: day: after 2.45 s the cup is back on the sill with its steam, identical to a page where nobody sipped (0 px differ)
- PASS: night: hovering the cup draws a black outline (86 px, all black True, around the cup and not the steam True) with a "pointer" cursor
- PASS: night: the click plays mug_sip on top of everything (frame 3 pixel-exact, 836 of its px over the sill and frame); a click mid-sip is ignored (1 sip counted)
- PASS: night: after 2.45 s the cup is back on the sill with its steam, identical to a page where nobody sipped (0 px differ)
- PASS: day (camp mug): hovering the cup draws a black outline (86 px, all black True, around the cup and not the steam True) with a "pointer" cursor
- PASS: day (camp mug): the click plays mug_camp_sip on top of everything (frame 3 pixel-exact, 836 of its px over the sill and frame); a click mid-sip is ignored (1 sip counted)
- PASS: day (camp mug): after 2.45 s the cup is back on the sill with its steam, identical to a page where nobody sipped (0 px differ)

## Folder: `whoami` (test mode)

- PASS: day: `whoami` slides the folder onto the sill, then only the closed folder remains (790 pixels, inside its box: True); bubble "you take out the folder. click it to open it."
- PASS: day: a second `whoami` says "the folder is already on the sill. click it to open it."
- PASS: day: hovering the closed folder draws a black outline (124 pixels) and a "pointer" cursor
- PASS: day: moving away removes the outline
- PASS: day: the open hook waits until the folder has finished opening ([])
- PASS: day: clicking opens the folder, then calls folderContents.open() once (['open'])
- PASS: day: hovering the open folder outlines it too (164 pixels)
- PASS: day: clicking the open folder calls folderContents.close() (['open', 'close'])
- PASS: day: it plays the opening backwards and ends identical to a folder that was never opened
- PASS: day: calling close() from the content closes the folder (['open', 'close', 'open', 'close'])
- PASS: day: with the cigarette pack also out, hovering the folder outlines only the folder
- PASS: day: no console problems ([])
- PASS: night: `whoami` slides the folder onto the sill, then only the closed folder remains (790 pixels, inside its box: True); bubble "you take out the folder. click it to open it."
- PASS: night: a second `whoami` says "the folder is already on the sill. click it to open it."
- PASS: night: hovering the closed folder draws a black outline (124 pixels) and a "pointer" cursor
- PASS: night: moving away removes the outline
- PASS: night: the open hook waits until the folder has finished opening ([])
- PASS: night: clicking opens the folder, then calls folderContents.open() once (['open'])
- PASS: night: hovering the open folder outlines it too (164 pixels)
- PASS: night: clicking the open folder calls folderContents.close() (['open', 'close'])
- PASS: night: it plays the opening backwards and ends identical to a folder that was never opened
- PASS: night: calling close() from the content closes the folder (['open', 'close', 'open', 'close'])
- PASS: night: with the cigarette pack also out, hovering the folder outlines only the folder
- PASS: night: no console problems ([])

## Folder pop-up

- PASS: 1280x752: pop-up drawn at a whole-number scale (4 device px per art px), art pixel-exact against popup_folder.png + active tab: True
- PASS: 1280x752: every string in folder_content.json appears exactly as written (left side: 10 strings; tabs: about, resume, projects, contact); missing: none
- PASS: 1280x752: the long resume tab scrolls inside the page (647 px of content in 500 px)
- PASS: 1280x752: the resume link downloads a real PDF (download attribute, HTTP 200, starts '%PDF-')
- PASS: 1280x752: clicking inside the pop-up keeps focus there (not the terminal input)
- PASS: 1280x752: closes on the X (True), Escape (True) and a click outside (True); the folder on the sill closes again too (True)
- PASS: 1280x752: no console problems ([])
- PASS: 1440x900_dpr2: pop-up drawn at a whole-number scale (9 device px per art px), art pixel-exact against popup_folder.png + active tab: True
- PASS: 1440x900_dpr2: every string in folder_content.json appears exactly as written (left side: 10 strings; tabs: about, resume, projects, contact); missing: none
- PASS: 1440x900_dpr2: the long resume tab scrolls inside the page (728 px of content in 563 px)
- PASS: 1440x900_dpr2: the resume link downloads a real PDF (download attribute, HTTP 200, starts '%PDF-')
- PASS: 1440x900_dpr2: clicking inside the pop-up keeps focus there (not the terminal input)
- PASS: 1440x900_dpr2: closes on the X (True), Escape (True) and a click outside (True); the folder on the sill closes again too (True)
- PASS: 1440x900_dpr2: no console problems ([])
- PASS: phone 390x844: plain single-column panel (True), all content shown (missing: none), fits the width (True), Escape closes it (True)

## Phone held sideways

- PASS: 667x320_dpr2: prompt at 16px so the page does not zoom (16px); a tap on the scene leaves the keyboard down (True), a tap on the prompt brings it up (True), sending a command puts it away (True) with the reply showing (True)
- PASS: 667x320_dpr2: folder pop-up drawn as art (popup fp is-compact) at a whole-number scale (3 device px per art px), fully on screen (True), no text spilling out (none), the GPA line whole (True)
- PASS: 667x320_dpr2: turning the phone with the folder open swaps to the plain panel (popup fp is-plain) and back to the art (popup fp is-compact)
- PASS: 667x320_dpr2: achievement board drawn as art (popup ab is-compact), every achievement's text inside its box (none)
- PASS: 667x320_dpr2: no console problems ([])
- PASS: 844x340_dpr3: prompt at 16px so the page does not zoom (16px); a tap on the scene leaves the keyboard down (True), a tap on the prompt brings it up (True), sending a command puts it away (True) with the reply showing (True)
- PASS: 844x340_dpr3: folder pop-up drawn as art (popup fp is-compact) at a whole-number scale (6 device px per art px), fully on screen (True), no text spilling out (none), the GPA line whole (True)
- PASS: 844x340_dpr3: turning the phone with the folder open swaps to the plain panel (popup fp is-plain) and back to the art (popup fp is-compact)
- PASS: 844x340_dpr3: achievement board drawn as art (popup ab is-compact), every achievement's text inside its box (none)
- PASS: 844x340_dpr3: no console problems ([])
- PASS: 844x390_dpr3: prompt at 16px so the page does not zoom (16px); a tap on the scene leaves the keyboard down (True), a tap on the prompt brings it up (True), sending a command puts it away (True) with the reply showing (True)
- PASS: 844x390_dpr3: folder pop-up drawn as art (popup fp is-compact) at a whole-number scale (7 device px per art px), fully on screen (True), no text spilling out (none), the GPA line whole (True)
- PASS: 844x390_dpr3: turning the phone with the folder open swaps to the plain panel (popup fp is-plain) and back to the art (popup fp is-compact)
- PASS: 844x390_dpr3: achievement board drawn as art (popup ab is-compact), every achievement's text inside its box (none)
- PASS: 844x390_dpr3: no console problems ([])
- PASS: 915x360_dpr2.625: prompt at 16px so the page does not zoom (16px); a tap on the scene leaves the keyboard down (True), a tap on the prompt brings it up (True), sending a command puts it away (True) with the reply showing (True)
- PASS: 915x360_dpr2.625: folder pop-up drawn as art (popup fp is-compact) at a whole-number scale (5 device px per art px), fully on screen (True), no text spilling out (none), the GPA line whole (True)
- PASS: 915x360_dpr2.625: turning the phone with the folder open swaps to the plain panel (popup fp is-plain) and back to the art (popup fp is-compact)
- PASS: 915x360_dpr2.625: achievement board drawn as art (popup ab is-compact), every achievement's text inside its box (none)
- PASS: 915x360_dpr2.625: no console problems ([])
- PASS: desktop window 844x390: unchanged: plain panel (popup fp is-plain), a click on the scene refocuses the prompt (True), prompt at 14px (14px)

## Welcome note

- PASS: the welcome note comes in on the sasquatch's arm (679 pixels change mid-reach), all of it inside the window opening: the frame hides where it reaches in from (0 outside)
- PASS: the note lands on the sill: only its box changes (0 pixels elsewhere), pixel-exact against note_sill_day.png (True); saved as left on the sill (1); `ls`: ['mug  note', 'put away: folder']
- PASS: hovering the note shows the hand (pointer); clicking it opens the note with every word from welcome_note.json (missing: none) and ['help', 'whoami'] as buttons
- PASS: clicking `help` in it closes the note, puts "help" on the focused prompt (input), and the note is gone from the sill (True), saved as read (2); it is never delivered again (False); `touch note`: ["touch: cannot touch 'note': you don't have one"]
- PASS: `rm note`: ['you take the note off the sill.'], the sill is bare there (True); `touch note`: ['you put the note on the sill.'], and it is back (True)
- PASS: a first visit: no note yet at 1.5 s (None), left on the sill by 6 s (1); after a reload the unread note is still there (`ls`: ['mug  note', 'put away: folder']); a visitor with progress saved from before never gets one (None)

## Cigarette easter egg (test mode)

- PASS: day: `cig` slides the pack in (181 pixels changing at 0.5 s), then only the pack remains (181 pixels, inside the pack box: True); bubble "you set your pack down on the sill."
- PASS: day: a second `cig` says "your pack is already on the sill."
- PASS: day: hovering the pack draws a black outline (52 pixels, all black: True, hugging the pack: True) and the cursor becomes "pointer"
- PASS: day: moving the mouse away removes the outline
- PASS: day: clicking starts the smoking (147 pixels differ at 6 s, 89 of them over the window frame or sill, i.e. drawn above everything); no hand cursor mid-smoke; after 69.70 s it ends and the scene is identical to "pack on the sill" (0 differing pixels)
- PASS: day: the pack can be clicked again for another cigarette
- PASS: day: no console problems ([])
- PASS: night: `cig` slides the pack in (181 pixels changing at 0.5 s), then only the pack remains (181 pixels, inside the pack box: True); bubble "you set your pack down on the sill."
- PASS: night: a second `cig` says "your pack is already on the sill."
- PASS: night: hovering the pack draws a black outline (52 pixels, all black: True, hugging the pack: True) and the cursor becomes "pointer"
- PASS: night: moving the mouse away removes the outline
- PASS: night: clicking starts the smoking (147 pixels differ at 6 s, 89 of them over the window frame or sill, i.e. drawn above everything); no hand cursor mid-smoke; after 69.70 s it ends and the scene is identical to "pack on the sill" (0 differing pixels)
- PASS: night: the pack can be clicked again for another cigarette
- PASS: night: no console problems ([])

## The sill: ls, rm, touch (test mode)

- PASS: `ls` at the start: ['mug', 'put away: folder']; `rm mug`: ['you take the mug off the sill.'], then `ls`: ['the sill is empty.', 'put away: mug  folder']; the cup is gone (412 px, all inside the cup: True) and clicking there sips nothing (0); `touch mug`: ['you put the mug on the sill.'], again: ['the mug is already on the sill.']; afterwards the scene matches a page that never moved it (0 px differ)
- PASS: mid-sip `rm mug`: ["rm: cannot remove 'mug': it's in use"]; `whoami` then `rm folder` while it slides in: ["rm: cannot remove 'folder': it's in use"]; `ls`: ['mug  folder']; once it rests, `rm folder`: ['you take the folder off the sill.'] (the scene then matches a page without it: 0 px differ); `touch folder`: ['you put the folder on the sill.'], and it slides back in
- PASS: before Woodsman: `touch trophy` ["touch: cannot touch 'trophy': you don't have one"], `rm trophy` ["rm: cannot remove 'trophy': not on the sill"] (as for `rm sofa`: ["rm: cannot remove 'sofa': not on the sill"]); earning everything: `ls` ['mug  folder  trophy  ashtray']; after `rm` of both: ['mug  folder', 'put away: trophy  ashtray']; after `reset yes`: ['mug  folder']
- PASS: trophy and ashtray put away: the scene matches a visitor without them (0 px differ, board aside); the pack before `cig`: ["touch: cannot touch 'pack': you don't have one"]; after: `ls` ['mug  pack', 'put away: folder']; `rm cigarettes`: ['you take the pack off the sill.'] (then 0 px differ from a page without it); `touch cig`: ['you put the pack on the sill.'], and it slides back in (0 px differ from a page that only ran `cig`)

## Unlock lines in the bubble (test mode)

- PASS: the 25th sip replaces the bubble ['mugClicks = 24'] with ['achievement unlocked: Caffeinated. The cup becomes an enamel camp mug.']; an unlock during `weather snow` shares its reply: ['achievement unlocked: Storm Chaser. A rainbow shows over the falls after rain.', 'it starts to snow.']

## Weather spells (test mode)

- PASS: a 2 s spell of rain: rain, still rain at 1.4 s, clear at 2.9 s; a spell of snow next earns Storm Chaser (True); `weather rain` by hand overrides the spell and stays (rain 30 s later); no spell starts unless the sky is clear (False); a rolled spell brings snow

## Snow on the trees (test mode)

- PASS: day: none while clear (0 px); snowing, it reaches stage [1, 2, 3, 4] at 3 s and every 30 s after, each one the stage art exactly (far and near: [True, True, True, True]), and stops at 4; once it clears it melts a stage every 20 s (3 after the first) and is gone (0, 0 px)
- PASS: night: none while clear (0 px); snowing, it reaches stage [1, 2, 3, 4] at 3 s and every 30 s after, each one the stage art exactly (far and near: [True, True, True, True]), and stops at 4; once it clears it melts a stage every 20 s (3 after the first) and is gone (0, 0 px)

## Scheduler (real clock, config.js served with short timers)

- PASS: bird fired by itself 21 times in 10 s (8 actually started)
- PASS: farbird fired by itself 21 times in 10 s (3 actually started)
- PASS: wind fired by itself 23 times in 10 s (23 actually started)
- PASS: sasquatch fired by itself 3 times in 10 s (2 actually started)
- PASS: weather fired by itself 9 times in 10 s (1 actually started)
  sasquatch chance check: about 22 rolls at chance 0.3, expected about 7 fires, got 3
- PASS: no console problems on the live (non-test) page: []
- PASS: front trees: 49 sways in 10 minutes (they used to sway non-stop), each a full cycle ['0123'], rests 7.5-14.8 s (config [7, 15])
- PASS: sasquatch timer over 20,000 seeded rolls: fired 30.6% of the time (config 30%), waits between 181 s and 600 s (config 180-600 s)

## Console

- PASS: no console errors/warnings or failed requests across every page above (0)
