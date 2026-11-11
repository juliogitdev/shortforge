---
name: shortforge
description: Turns a topic into a finished vertical short video (TikTok, Reels, YouTube Shorts) in animated 3D. It researches the topic, writes a high-retention script with hooks and a comment-bait ending, waits for the user to approve it, then renders a 1080x1920 video with 3D scenes and characters, dynamic 2D edit, subtitles, sound effects and original music. It always delivers ready-to-paste descriptions and hashtags for every platform alongside the video. Use this skill whenever the user asks for a short, reel, TikTok or Shorts video, a "vídeo para o TikTok/Instagram", a script plus video about any theme (games, news, stories, curiosities, controversies, countdowns, "você decide" interactive stories), or says something like "faz um vídeo sobre X". Use it even if the user only names a theme and expects the full pipeline.
---

# shortforge

Topic → researched script → **user approval** → narration → 3D + 2D render → video + descriptions for every platform.

The video style is a 3D world rendered with three.js: a night street, a bedroom, a TV studio or a neon dream void, with stylized characters that have facial expressions and poses. On top of that sits a fast 2D layer: big subtitles with highlighted keywords, slam stamps, counters, phone screens, timers, A/B choice cards and comment bubbles. The audio mixes the narration with synthesized SFX and original music. A sidechain keeps the narrator clearly audible the whole time.

Talk to the user in their language. The pipeline below is written in English, and the examples are in Brazilian Portuguese, the language of the original channel.

## Stage 0: setup (once per machine or session)

```bash
bash <skill>/scripts/setup.sh      # installs three.js, checks ffmpeg / Pillow / numpy / Playwright Chromium
```
Rendering uses headless Chromium with software WebGL (SwiftShader). It takes about 0.6 s per frame per worker, so a 50 s video takes **15 to 20 min on 4 cores**. Tell the user up front, and run full builds in the background.

## Stage 1: research and script

1. If the topic involves facts, news or dates, **search the web first**. Note your sources, because you will list them for the user.
2. Pick the format that fits the topic. Read `references/script-writing.md` for the formats, hook formulas, retention devices and the legal checklist. That file is what makes these scripts perform, so read it every time.
3. Write the script as **plain narration text, ready to paste into ElevenLabs**. Spell out numbers that the voice reads badly ("GTA seis"), and use "..." for dramatic pauses. Aim for about 130 to 150 words per 60 s.
4. Present it to the user with:
   - the narration text in a copyable block
   - a short scene-by-scene visual idea, so they can picture the video
   - the comment-bait ending you chose
   - sources and any legal notes (allegations, real people, copyright)

## Stage 2: approval gate

**Stop and wait for the user to approve the script.** Rendering is expensive and the script is the part the user cares most about, so never render an unapproved script. Apply any edits they ask for and confirm again. If they approve with changes, update the text before moving on.

## Stage 3: narration

Ask the user to generate the narration (ElevenLabs or any TTS) and send the MP3. If the session has a TTS tool or API key the user wants to use, you may generate it yourself. Save it next to the plan as `narration.mp3`.

## Stage 4: timing

```bash
python <skill>/scripts/analyze_audio.py narration.mp3
```
This returns speech segments. Map each segment to its sentence in order, then build the `subs` list from that. Scene cuts land on sentence starts, so visuals change on every beat.

## Stage 5: build the plan

Create a work folder (for example `./shorts/<slug>/`) holding `narration.mp3` and `plan.json`. Read `references/plan-schema.md` for the full vocabulary and `references/visual-style.md` for layout and pacing rules. **Start by copying `assets/examples/leo_ep1/plan.json`.** It is a complete, tested episode, and adapting it beats writing from scratch.

Design rules that matter:
- **3D is the default for every scene.** Each scene has a 3D shot (camera move plus actors plus props). 2D backgrounds (`neon`, `image:`) are fallbacks for things the 3D world can't show.
- Make a **new shot every 2 to 5 s**. Give each shot a camera move: a push-in, a pull-back, an orbit or a follow.
- **Open with the climax** (a flash-forward or the most shocking image), then rewind or explain. Put the first visual change within 1.5 s.
- Keep faces readable. Put big text in the upper band (y 200 to 450) or over the torso (y 900 to 1130), never over a face. Subtitles live at y about 1470.
- **Use 1 s of silence before a big reveal**, then hit it with impact, a deep boom and a flash.
- When the user supplies photos of real people or official game images, show them as `card` overlays or as 3D `billboard` props, and add `credit` when needed.
- Write `captions` for every platform, following `references/platforms.md`. They become `descricoes.md`, which is mandatory.

## Stage 6: preview, then look before rendering

```bash
python <skill>/scripts/build.py plan.json --preview 1.5,6,10,...   # one time inside each scene
```
Open `out/preview_sheet.jpg` and check it yourself:
- Is each face visible and lit, and is the camera outside walls?
- Does any text cover a face?
- Is the subject in frame and the money or props visible?

Fix camera and positions, then preview again. Two or three preview rounds are normal and far cheaper than a bad full render.

## Stage 7: full build

```bash
python <skill>/scripts/build.py plan.json            # 3D frames → 2D compose → audio mix → mux → QA
python <skill>/scripts/build.py plan.json --skip-3d  # after editing only overlays, subs or audio
```
Run it in the background and give the user progress updates. Outputs go to `out/`: `<output_name>.mp4`, `descricoes.md`, `contact_sheet.jpg` and `clarity.json`.

## Stage 8: QA and delivery

- Look at `contact_sheet.jpg`.
- Check `clarity.json`. `voice_over_background_db_mean` should be at least 15, and `windows_below_10db` should be empty or nearly empty. If not, lower the `sfx` gains near those times, or raise `voice_margin_db`, then run `--skip-3d`.
- Deliver the **MP4 plus `descricoes.md`**. Show the user the descriptions in chat as well, ready to copy, and mention the pinned comment and cover-frame tip.
- For Instagram and TikTok, the user may prefer adding a trending licensed sound in the app. Offer a version with `audio.music.mood = "none"` for that.

## Series and follow-ups

- **"Você decide" stories:** keep the same `cast` entry so the character stays consistent across episodes. Recap the previous choice in the first 3 s of the next episode. When the votes are in, write both branches (A and B) in advance if the user asks.
- **Countdown series:** keep the HUD badge and the same opening structure every day, and change only the content.

## Files

- `scripts/build.py`: orchestrator (preview / full / skip-3d)
- `scripts/world3d/scene.html` + `render3d.js`: the 3D world, characters, props and camera system
- `scripts/compose.py` + `engine2d.py`: the 2D layer (overlays, subtitles, shakes, flashes)
- `scripts/audio_mix.py`: SFX library, music generator, sidechain mix and clarity report
- `scripts/analyze_audio.py`: speech-segment timing
- `references/script-writing.md`, `plan-schema.md`, `visual-style.md`, `platforms.md`
- `assets/examples/leo_ep1/`: a full working example (plan and narration)
