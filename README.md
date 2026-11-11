# shortforge 🎬

**Tema → roteiro com retenção → sua aprovação → vídeo vertical 3D pronto + descrições para todas as plataformas.**

Skill para Claude (Claude Code / Claude.ai) que transforma um tema em um short animado para TikTok, Reels e YouTube Shorts:

- 🔎 pesquisa o tema e escreve o roteiro com ganchos, loops de curiosidade e final que gera comentário
- ✅ **para e pede aprovação** antes de renderizar
- 🎙️ usa a sua narração (ElevenLabs ou outra) e sincroniza legendas e cortes com a voz
- 🧊 cenas **3D** (three.js): rua à noite com chuva, quarto, estúdio de TV, mundo neon; personagens com expressões e poses; moto, pacote, explosão de dinheiro, pilhas de caixas, telões com imagens
- ⚡ edição dinâmica 2D por cima: legendas grandes com palavras destacadas, carimbos, contadores, celular, cronômetro, cartões A/B, comentários animados, tremidas e flashes
- 🔊 efeitos sonoros e trilhas originais (sem direitos autorais) com **o narrador sempre audível** (fundo ≥15 dB abaixo da voz)
- 📝 entrega **`descricoes.md`** com legenda + hashtags para TikTok, Instagram, YouTube Shorts, Kwai e Facebook, e o comentário fixado

## Instalação

```bash
git clone https://github.com/<seu-usuario>/shortforge ~/.claude/skills/shortforge
bash ~/.claude/skills/shortforge/scripts/setup.sh
```
Requisitos: Python 3 (Pillow, numpy), Node.js, ffmpeg, Playwright com Chromium (o setup instala o que faltar).

No Claude.ai: compacte a pasta e envie em *Configurações → Skills*.

## Uso

Só peça um vídeo:

> "Faz um vídeo sobre o lançamento do GTA 6"
> "Episódio 2 do Você Decide: o Léo atendeu o celular"
> "Vídeo polêmico sobre [notícia], com perguntas pro público"

O Claude mostra o roteiro → você aprova → manda o MP3 da narração → recebe `out/<nome>.mp4` + `out/descricoes.md`.

Render: ~0,6 s por quadro por núcleo (um vídeo de 50 s leva ~15–20 min em 4 núcleos).

## Estrutura

```
SKILL.md                    fluxo completo que o Claude segue
scripts/build.py            orquestra: prévia, render 3D, composição 2D, áudio, montagem, QA
scripts/world3d/            mundo 3D (three.js) e renderizador headless
scripts/compose.py          camada 2D (overlays, legendas, efeitos)
scripts/audio_mix.py        trilhas, efeitos e mixagem com sidechain
scripts/analyze_audio.py    tempos da narração
references/                 guia de roteiro, formato do plano, estilo visual, descrições por plataforma
assets/examples/leo_ep1/    episódio completo de exemplo (plano + narração)
```

## Licenças
Código: MIT. Fonte Montserrat: SIL OFL 1.1 (ver `assets/fonts/README.md`).
A narração de exemplo foi gerada pelo autor do canal no ElevenLabs; substitua pela sua.
