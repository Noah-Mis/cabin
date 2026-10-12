# Pixel comparison: site vs compose()

Each row is one page load, compared at ticks 0-47 (100 ms each) on the native 320x180 canvas.
Pass A leaves out the waterfall rectangle (compose() draws the old waterfall); pass B includes the new one.

| pass | time | weather | wind | ticks exact | differing pixels (total) | worst tick | max channel delta |
|---|---|---|---|---|---|---|---|
| A | morning | clear | no | 48/48 | 0 | - | 0 |
| A | day | clear | yes | 48/48 | 0 | - | 0 |
| A | afternoon | clear | yes | 48/48 | 0 | - | 0 |
| A | night | clear | no | 48/48 | 0 | - | 0 |
| A | morning | rain | no | 0/48 | 22317 | 0 | 1 |
| A | day | rain | no | 0/48 | 27278 | 19 | 1 |
| A | afternoon | rain | no | 0/48 | 35760 | 23 | 1 |
| A | night | rain | no | 0/48 | 30158 | 2 | 1 |
| A | morning | snow | no | 3/48 | 25200 | 45 | 1 |
| A | day | snow | no | 3/48 | 25347 | 13 | 2 |
| A | afternoon | snow | no | 8/48 | 21130 | 39 | 2 |
| A | night | snow | no | 5/48 | 23028 | 37 | 2 |
| B | morning | clear | no | 48/48 | 0 | - | 0 |
| B | day | clear | no | 48/48 | 0 | - | 0 |
| B | afternoon | clear | no | 48/48 | 0 | - | 0 |
| B | night | clear | no | 48/48 | 0 | - | 0 |
| B | morning | rain | no | 0/48 | 23994 | 14 | 1 |
| B | day | rain | no | 0/48 | 28306 | 20 | 1 |
| B | afternoon | rain | no | 0/48 | 37520 | 13 | 1 |
| B | night | rain | no | 0/48 | 31625 | 9 | 1 |
| B | morning | snow | no | 3/48 | 27230 | 45 | 1 |
| B | day | snow | no | 3/48 | 27362 | 24 | 2 |
| B | afternoon | snow | no | 8/48 | 22810 | 39 | 2 |
| B | night | snow | no | 5/48 | 24847 | 37 | 2 |

Browser console problems during the run: 0
