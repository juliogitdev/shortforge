# plan.json schema

One JSON file drives the whole video. Paths are relative to the plan file. Times are in seconds. The working example is `assets/examples/leo_ep1/plan.json`.

## Contents
1. Top level
2. `cast`: characters
3. `shots`: the 3D layer (sets and landmarks, camera, actors, props)
4. `scenes`: the 2D layer and overlays
5. `subs` / `highlights`
6. `audio`
7. `captions`

## 1. Top level
```json
{ "title": "...", "output_name": "voce-decide-ep1", "duration": 52.6, "hud": "VOCÊ DECIDE · EP.1",
  "frames_dir": "build/f3d", "output_dir": "out",
  "cast": {...}, "shots": [...], "scenes": [...], "subs": [...], "highlights": {...},
  "shakes": [[t, amplitude_px], ...], "flashes": [t, ...],
  "audio": {...}, "captions": {...},
  "studio_color": "#1b1f4a", "room_wall": "#3a4a6a", "street_sign_top": "RUA SEM", "street_sign_bottom": "SAÍDA",
  "bill_value": "100", "stack_label": "PS5", "stack_color": "#2850c8" }
```
- `duration` is the narration length plus about 1 to 2 s for the end card.
- If `flashes` is missing, a white flash plays at each scene that has `"flash": true`.

## 2. cast
```json
"cast": { "leo": { "skin": "#96603f", "hair": "#19120f", "hair_style": "curly|short|long|bun|bald",
                   "top": "#eb5523", "stripe": "#ffdc3c", "pants": "#23284a", "shoes": "#f2f2f2",
                   "backpack": "#1e6e46", "helmet": "#ffc400", "eye": "#2a170c", "lips": "#5a1e1e", "lashes": false } }
```
- `stripe` adds a reflective band, and `backpack` adds a delivery bag. Use `lashes: true` with `hair_style: "long"` for a female look.
- Keep a character's entry identical across episodes so they stay recognizable.

## 3. shots (3D)
Each shot has `start`, `end`, a `set`, a `camera`, `actors` and `props`. The shot active at time T is the last one with `start <= T`.

### Sets and landmarks (coordinates are local to the set)
| set | what it is | useful coordinates |
|---|---|---|
| `street_night` | a rainy city street that ends in a dead-end wall | road along -z from 0 to -120. Sidewalk height 0.25 (put actors at y=0.25 on sidewalks, x 5 to 9). House door at (8.8, 1.6, -110). Flickering lamp at (6.6, 6.85, -104). Dead-end sign at (-5.5, 3.6, -112). Wall at z=-122. |
| `room` | a bedroom with a bed, a desk with a glowing monitor and a window | floor 12x12 centered at (0,0,0). Bed at (-4.5, 0.3, -3.5). Desk at (2, 1.1, -5.2). Walls at z=-6 and x=-6. |
| `studio` | a TV studio with a curved backdrop, a neon floor ring and colored spotlights | stage center (0,0,0), ring radius 7. Good for presenters and `billboard` screens behind the actor. |
| `neon_void` | synthwave grid with a striped sun | center (0,0,0), sun at (0,18,-90). Use it for dreams, imagination and "what if". |

Shot options: `"rain": true`, `"fog": 0.022`, `"mood": "night|red|neon|warm|day"`, `"flicker": true` (street lamp), `"fill": false` (turns off the face fill light), `"fill_intensity": 9`, `"time_map": {"type": "reverse", "at": 2.9, "speed": 1.6}` (plays time backwards after `at`, for a rewind after a flash-forward).

### camera
```json
"camera": { "from": [x,y,z], "to": [x,y,z], "look": [x,y,z], "look_to": [x,y,z], "fov": 45, "shake": 0 }
"camera": { "orbit": { "center": [x,y,z], "radius": 7.5, "height": 1.7, "start_angle": -0.4, "speed": 0.12 }, "fov": 48 }
"camera": { ..., "follow_moto": true }   // keeps the from/look offsets relative to a moving moto
```
The camera moves from `from` to `to` over the shot with smoothstep easing. Typical values:
- Close-up on a face: distance 3 to 4, at head height (actor y + 2.6), fov 38 to 42.
- Medium shot: distance 5 to 6, fov 50 to 55.
- Aerial: y 15 to 25, looking down the street.

**Camera in front of an actor** standing at (ax, az) and facing angle `rot`:
`pos = [ax + sin(rot+side)*d, h, az + cos(rot+side)*d]`. Here `side` is a small angle offset, from -0.3 to 0.3. Actors face +z when rot=0. rot=π/2 faces +x.
In `street_night`, the house occupies x 9 to 19 and z -115 to -105. Keep cameras out of it, and away from lamp poles at (5.5,-20), (-5.5,-48), (5.5,-76) and (6.6,-104).

### actors
```json
{ "id": "leo", "pos": [6.0, 0.25, -108.6], "rot": 0.5, "expr": "shock", "pose": "stand",
  "helmet": false, "look_down": false, "head_turn": 0, "move_to": [x,y,z], "move_dur": 2.0 }
```
- `expr`: neutral, happy, sus, shock, nervous (adds sweat), angry, sad.
- `pose`: stand, walk (use it with `move_to`), ride, phone, point, arms_up, think, reach, sit, shrug.

### props
| type | fields |
|---|---|
| `moto` | `pos`, `rot` (π faces -z), `speed` (m/s along -z), `rider` (actor id), `rider_expr`, `lamp` |
| `package` | `pos`, `rot`, `open` (true) or `open_at` (s), `phone` (bool), `ring` or `ring_at`, `cash` (default true), `drop_at` |
| `money_burst` | `origin`, `start` (s in shot), `time_offset` (s already elapsed: use a large value for "bills on the floor"), `floor_y` (0.27 on the sidewalk) |
| `stack` | `center`, `count_from`, `count_to`, `start`, `dur`. Labels come from `stack_label` / `stack_color`. |
| `billboard` | `image` (path), `pos`, `rot`, `size` [w,h]. Shows a photo as a framed 3D screen (official images, news photos). |

## 4. scenes (2D layer)
```json
{ "start": 25.5, "flash": true, "bg": "3d", "blur": 0, "overlays": [ ... ] }
```
- `bg`: `3d` (default) uses the rendered 3D frame. The fallbacks are `neon`, `dark:purple|blue|red|navy|green`, `image:path` and `blur:path`.
- Times inside an overlay (`at`, `until`, `after`, `at_b`) are **relative to the scene start**. `timer.start_abs` is absolute.

| type | fields |
|---|---|
| `text` | `text`, `size`, `color`, `stroke`, `x`, `y`, `at`, `until`, `rot`, `slam`, `bob` |
| `badge` | `text`, `size`, `bg`, `fg`, `x`, `y`, `at`, `until`, `rot`, `slam` (stamp-like scale-down from 2.2x) |
| `counter` | `from`, `to`, `prefix`, `suffix`, `sep`, `dur`, `y`, `size`, `color`, `at` |
| `card` | `image`, `w`, `h`, `x`, `y`, `border`, `zoom`, `gray`, `focus` [fx,fy], `credit`, `at`, `rot` |
| `phone` | `title`, `status`, `status_after`, `after`, `ring`, `x`, `y`, `scale`, `rot` |
| `timer` | `seconds`, `start_abs`, `speed` (default 0.75 = a 10 s countdown over about 13 s of video), `x`, `y`, `r` |
| `choice` | `a` "LINE1\|LINE2", `b`, `a_color`, `b_color`, `at`, `at_b`, `y` |
| `bubbles` | `items` [[text, user, color, at], ...], `y0` (fake comments are illustrative, so keep them generic) |
| `endcard` | `at`, `lines` [main, second], `mascot` (bool) |
| `tint` | `color` [r,g,b,a], `at`, `until`, `pulse`, `blink`, `flash` |
| `vignette` | `strength` |
| `progress` | `to` (0 to 1), `label` ("{p}%" is replaced), `y`, `at`, `dur`, `color` |
| `calendar` | `month`, `day`, `year`, `y`, `at`, `cross_at`, `circle_at` |
| `image` | `image`, `w`, `x`, `y`, `at`, `rot` (stickers, logos the user owns) |
| `mascot` | `x`, `y`, `scale`, `at` |

Colors: names (yellow, pink, red, green, cyan, blue, purple, orange, white, black, dark), "#hex" or [r,g,b(,a)].

## 5. subs / highlights
```json
"subs": [[0.00, 2.55, "ESSA ENTREGA IA MUDAR A VIDA DO LÉO."], ...],
"highlights": { "LÉO": "yellow", "NINGUÉM": "red", "50": "green" }
```
- Write subtitles in UPPERCASE, split at segment boundaries from `analyze_audio.py`, with at most about 8 words per subtitle.
- Highlight keys are matched per word, ignoring trailing punctuation.

## 6. audio
```json
"audio": { "narration": "narration.mp3",
  "music": { "mood": "tension|heist|synthwave|upbeat|none", "gain": 0.18, "levels": [[t, 0-1], ...], "silence": [[a, b]], "file": "optional_own_music.mp3" },
  "ambience": [{ "type": "rain", "from": 5, "to": 25.5, "gain": 1.0 }],
  "sfx": [[t, "name", gain, optional_duration], ...], "sfx_gain": 0.30, "voice_margin_db": 15 }
```
SFX names: whoosh, whoosh_down, boom, boom_deep, impact, stamp, pop, ding, tick, tock, scribble, siren, engine, crack, riser, heartbeat, ringback, voicemail, tape, cash, vibrate, ringtone, crickets, rewind, drumroll, thunder, clank.

The mix ducks music, ambience and SFX so they stay at least `voice_margin_db` under the narration while it speaks, starting 0.25 s before each phrase. It prints a clarity report.

## 7. captions
```json
"captions": { "tiktok": "...", "instagram": "...", "youtube": {"title": "...", "description": "..."},
              "kwai": "...", "facebook": "...", "pinned_comment": "...", "tips": ["..."] }
```
These are written to `out/descricoes.md`. See `platforms.md`.
