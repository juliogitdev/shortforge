# Visual and audio style

## Layout (1080x1920)
- **HUD badge** at the top left, y about 110 (series name / episode).
- **Big titles and stamps** go either in the upper band (y 200 to 450) or over the torso (y 900 to 1130). **Never over a face.** In 3D close-ups the head sits around y 250 to 700, so check the preview.
- **Subtitles** sit at y about 1470, with up to 3 lines. TikTok's UI covers about the bottom 350 px and a right strip of about 150 px, so keep key info out of there.
- A few elements per scene: 1 or 2 overlays plus subtitles. Clarity beats density.

## Pacing
- A new 3D shot every 2 to 5 s, and a new overlay or stamp every 1 to 3 s.
- **Slam stamps** (`"slam": true`, red or yellow badge) on the key word of a sentence ("NINGUÉM", "ADIADO!", "AGORA.").
- A camera shake (`shakes`) of 15 to 35 px on impacts, and a white flash (`flash: true`) on big cuts. Use them sparingly, about 6 to 10 per minute.
- **Silence + reveal:** about 1 s near-silence (`music.silence`), then impact + boom_deep + flash + counter.
- The decision or ending runs a timer that ticks, sweat on the character, red mood, then the A/B cards.

## Color language
- Yellow means emphasis and numbers. Red means danger, a negative, urgency. Green means money and positive. Cyan or blue is the "B" option and calm. Pink is the brand or a person's name.
- Brand palette: pink #FF2E88, purple #7B2FF7, orange #FF8A00, yellow #FFD400, dark #0D0D1A. The font is Montserrat Black (bundled).

## Sound map (what to put on each event)
| Event | SFX |
|---|---|
| Hard cut | whoosh (0.3 to 0.4 s) |
| Text or stamp appears | pop (or stamp for slams) |
| Reveal / shock | impact + boom_deep (+ cash for money) |
| Rising tension | heartbeat, riser, crickets (night), tape (opening) |
| Phone | ringback → voicemail, vibrate + ringtone |
| Countdown | tick/tock every 0.75 s + drumroll before the answer |
| Rewind | rewind (clean sweep, no hiss: the user disliked static) |
| Vehicle | engine, siren |
| End card | whoosh + ding |

Music moods: `tension` for stories and suspense, `heist` for controversy and crime, `synthwave` for games and GTA, `upbeat` for fun and lists. Lower the music under the narration, which the sidechain does automatically. Use `levels` to drop it at dramatic moments.

**The narrator must always be clear.** The user complained when SFX covered the voice. Keep `clarity.json` at a mean of 15 dB or more.

## 3D quality checklist (look at the preview sheet)
- The face is lit and visible (fill light on, camera in front, not behind the head).
- The camera is not inside a building, a pole or a prop. Watch the house box and the lamp poles in `street_night`.
- The subject is centered and the props of the moment are in frame. Money bursts start at the package, so frame both.
- Keep characters' feet on the ground or sidewalk (y=0.25 on sidewalks).
