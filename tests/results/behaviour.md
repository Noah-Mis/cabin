# Behaviour checks

## Layout and crispness

- PASS: desktop_1920x1080: scale 6, whole-number=True, fills the screen=True, window and sill fully visible above the prompt=True, prompt 32 px tall=True, every visible pixel a clean 6x6 block=True
- PASS: laptop_1366x768: scale 5, whole-number=True, fills the screen=True, window and sill fully visible above the prompt=True, prompt 32 px tall=True, every visible pixel a clean 5x5 block=True
- PASS: hidpi_1440x900_dpr2: scale 10, whole-number=True, fills the screen=True, window and sill fully visible above the prompt=True, prompt 32 px tall=True, every visible pixel a clean 10x10 block=True
- PASS: odd_1000x700_dpr1.25: scale 5, whole-number=True, fills the screen=True, window and sill fully visible above the prompt=True, prompt 32 px tall=True, every visible pixel a clean 5x5 block=True
- PASS: phone_390x844_dpr3: scale 4, whole-number=True, fills the screen=False, window and sill fully visible above the prompt=True, prompt 34 px tall=True, every visible pixel a clean 4x4 block=True
- PASS: phone_landscape_844x390_dpr3: scale 8, whole-number=True, fills the screen=True, window and sill fully visible above the prompt=True, prompt 32 px tall=True, every visible pixel a clean 8x8 block=True

## Commands (typed into the terminal, test mode, compared with a page that did not run them)

- PASS: `bird` is not a command any more: scene unchanged (0 differing pixels), bubble said "no such command "bird". type "help" to see what you can do."
- PASS: `sasquatch` is not a command any more: scene unchanged (0 differing pixels), bubble said "no such command "sasquatch". type "help" to see what you can do."
- PASS: `wind` is not a command any more: scene unchanged (0 differing pixels), bubble said "no such command "wind". type "help" to see what you can do."
- PASS: `farbird` is not a command any more: scene unchanged (0 differing pixels), bubble said "no such command "farbird". type "help" to see what you can do."
- PASS: `time morning`: mid-fade frame differs from both palettes; 3.5 s later the frame is identical to a page started at morning (0 differing pixels), so every layer swapped
- PASS: `time afternoon`: mid-fade frame differs from both palettes; 3.5 s later the frame is identical to a page started at afternoon (0 differing pixels), so every layer swapped
- PASS: `time night`: mid-fade frame differs from both palettes; 3.5 s later the frame is identical to a page started at night (0 differing pixels), so every layer swapped
- PASS: `weather rain`: identical to a page started with rain; terminal said "it starts to rain."
- PASS: `weather snow`: identical to a page started with snow; terminal said "it starts to snow."
- PASS: `weather clear`: identical to a page started with clear; terminal said "the sky clears."

## Terminal

- PASS: input has focus on load, so typing works straight away
- PASS: clicking the scene keeps focus in the input
- PASS: no bubble before anything is typed (test mode has no greeting)
- PASS: `help` shows one bubble listing help, clear, whoami, badges and not bird, wind, sasquatch, cig, time, weather, reset
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
- PASS: `time auto` returns to the clock (local hour 22 -> night)
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
- PASS: 1440x900_dpr2: pop-up drawn at a whole-number scale (10 device px per art px), art pixel-exact against popup_folder.png + active tab: True
- PASS: 1440x900_dpr2: every string in folder_content.json appears exactly as written (left side: 10 strings; tabs: about, resume, projects, contact); missing: none
- PASS: 1440x900_dpr2: the long resume tab scrolls inside the page (785 px of content in 625 px)
- PASS: 1440x900_dpr2: the resume link downloads a real PDF (download attribute, HTTP 200, starts '%PDF-')
- PASS: 1440x900_dpr2: clicking inside the pop-up keeps focus there (not the terminal input)
- PASS: 1440x900_dpr2: closes on the X (True), Escape (True) and a click outside (True); the folder on the sill closes again too (True)
- PASS: 1440x900_dpr2: no console problems ([])
- PASS: phone 390x844: plain single-column panel (True), all content shown (missing: none), fits the width (True), Escape closes it (True)

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

## Scheduler (real clock, config.js served with short timers)

- PASS: bird fired by itself 22 times in 10 s (8 actually started)
- PASS: farbird fired by itself 21 times in 10 s (3 actually started)
- PASS: wind fired by itself 23 times in 10 s (23 actually started)
- PASS: sasquatch fired by itself 7 times in 10 s (3 actually started)
  sasquatch chance check: about 22 rolls at chance 0.3, expected about 7 fires, got 7
- PASS: no console problems on the live (non-test) page: []
- PASS: front trees: 49 sways in 10 minutes (they used to sway non-stop), each a full cycle ['0123'], rests 7.0-14.9 s (config [7, 15])
- PASS: sasquatch timer over 20,000 seeded rolls: fired 30.6% of the time (config 30%), waits between 181 s and 600 s (config 180-600 s)

## Console

- PASS: no console errors/warnings or failed requests across every page above (0)
