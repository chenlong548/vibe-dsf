<div align="center">

<img src="brand/logo.svg" width="420" alt="VIBE·DSF — knowledge video pipeline"/>

**The automated knowledge-video pipeline — from one line to a release-ready film**

[简体中文](README.md) | [Live site](site/index.html) · **v1.6.0** · [Changelog](CHANGELOG.md) · [MVP scope](docs/24-MVP.md) · [Roadmap](docs/25-ROADMAP.md) · [Commercial](docs/22-COMMERCIAL.md)

`MIT` · `QA ≥ 8 hard gate` · `Zero paid dependencies` · `Self-hosted`

</div>

---

# VIBE·DSF

> We turn one line, a paper, or a repository into a release-ready 1080p knowledge video.
> Frames are drawn by code, audio is synthesised deterministically, and a **pixel-level QA gate**
> decides whether the film is allowed to ship.

This is not an editor and not a SaaS. It is a local pipeline that produces the film, the audit
report and the reproducible render source. Models are interchangeable; the rule that numbers decide
is not.

## 1. Why we built it this way

| Problem | Our answer |
|---|---|
| A model says a frame looks fine while a caption is cut off | 11 pixel-level QA metrics, `avg < 8 → exit 1` stops the line |
| Frame density depends on taste, so quality drifts | Aesthetics become measurements: texture energy, composition centre, accent focus, subtitle occupancy |
| One changed frame means re-rendering everything | `render(t)` is a pure time function — identical SHA256 per frame, re-render by the second |
| Nobody knows where a long run got stuck | Every run writes `pipeline_report.json`: stage timings, artifacts, failed stage |

## 2. What is actually built

| Capability | Implementation | Measured |
|---|---|---|
| Frame capture | `pipeline/render/render_frames.mjs` (CDP fast mode) | 0.65 → **0.13 s/frame** (4.9×), 1080p30 |
| QA gate | `pipeline/qa/qa_check.py` (QA v4) | 11 metrics, style-aware safe area, avg ≥ 8 to pass |
| Audio | BGM + six-effect whitelist + edge-tts narration + RMS side-chain ducking | Three-layer mix, −14 LUFS assembly |
| Content lines | Topic / paper PDF / repo README → `SCENE-PLAN.json` | All three share 100% of the back half |
| Component library | `pipeline/blocks/` — 10 blocks + `registry.json` score archive | Every block QA-gated |
| Brand contract | `pipeline/palette.json` (`palette_name` references) | Only QA-passed palettes admitted |
| Human review | `pipeline/review.mjs` | Scene grid, A/B comparison, QA issue overlay |
| Run report | `pipeline/report/generate.py` | Written on success **and** failure; append-only event log |
| Regression | `test_edge_v4.py` + `test_generate.py` + `_probe` | 15 assertions in CI |

## 3. Architecture

```
topic line / paper PDF / GitHub repo
   ↓  brief contract + validator
SCENE-PLAN.json ──(validate_plan.py: 11 hard checks)──→ build_html.mjs
   ↓  10 blocks assemble into one HTML file
render_frames.mjs ──(CDP frame capture)──→ frames/*.png
   ↓
qa_check.py ──(11 metrics / avg ≥ 8 gate, stop on failure)──→ qa.json
   ↓
BGM + SFX + TTS ──(mix_audio.py ducking)──→ build.ps1 (ffmpeg) ──→ final.mp4
   ↓
generate.py ──→ pipeline_report.json ／ review.mjs ──→ human review
```

`pipeline/run_all.ps1` chains everything: render → QA gate → BGM → SFX/narration → mix →
assembly → report. Exit codes `0 / 1 / 2 / 3 / 4` point at the failing stage.

## 4. Layout

```
brand/                 logo, favicon, brand guidelines (BRAND.md)
site/                  publishable bilingual site index.html + og-card.svg + check.py
pipeline/
├── run_all.ps1        one-shot pipeline (writes the run report)
├── review.mjs         still-frame review page
├── palette.json       brand contract · requirements.txt
├── render/            CDP frame capture
├── qa/                11-metric gate + edge regression fixture
├── report/            stage events → pipeline_report.json + regression fixture
├── audio/             BGM / SFX / waveform; narrate/ holds TTS and ducking mix
├── compose/           ffmpeg assembly (build.ps1 / build.sh)
├── blocks/            10 blocks + registry.json
├── scene_writer/      topic → SCENE-PLAN (task book / hard gate / assembler)
├── paper2video/       paper → PAPER-BRIEF → SCENE-PLAN
└── project2video/     repository → PROJECT-BRIEF → SCENE-PLAN
projects/              5 reference films + _probe fixture + _archive (kept for rollback)
skills/ styles/ docs/ scripts/ .github/
docs/                  00–25 numbered playbook and engineering notes (24 MVP / 25 roadmap)
```

Full directory map, dependency direction and the "add a block" workflow: [CONTRIBUTING.md](CONTRIBUTING.md).

## 5. Quick start (three MVP steps)

To confirm the current release is complete and publishable — steps 1 and 2 need
neither Chrome nor ffmpeg:

```bash
python scripts/verify.py                 # 1) 9 checks, 9/9 PASS = MVP READY
```

```powershell
powershell -File scripts\setup.ps1       # 2) read-only environment / file health check
powershell -File pipeline\run_all.ps1 -Project projects\demo-hook-compound -SkipRender
                                       # 3) ship: QA gate + audio + assembly + run report
```

Drop `-SkipRender` and pass `-Duration <seconds>` for a full render, then read
`pipeline_report.json`. The release surface is defined in [docs/24-MVP.md](docs/24-MVP.md);
everything planned for later lives in [docs/25-ROADMAP.md](docs/25-ROADMAP.md) and does not
block this release.

Requires Python 3.10+ (`numpy` / `pillow` / `edge-tts`), Node 20+, a local Chrome, and ffmpeg.
No GPU and no paid connector required.

<details>
<summary>Step-by-step commands (when a single stage needs manual control)</summary>

```powershell
# From inside a project directory
node ..\..\pipeline\render\render_frames.mjs --fps 30 --duration 8
python ..\..\pipeline\qa\qa_check.py frames --fps 30 --json qa.json
python ..\..\pipeline\audio\synth_bgm.py bgm.wav --bpm 77 --duration 8
powershell -File ..\..\pipeline\compose\build.ps1 -Audio bgm.wav
node ..\..\pipeline\render\render_frames.mjs --start 3 --end 5

# From the repository root: human still-frame review
node pipeline\review.mjs --project projects\demo-hook-compound
```

</details>

The site is a single static file — open `site/index.html` offline, or run `python site/check.py`
as a pre-publish check.

## 6. Quality and observability

- **QA v4** detects safe-area bleed relative to each film's own background: dark films catch
  bright spill, light films catch dark spill. `--v2` / `--legacy-edge` reproduce older verdicts
  on the same frames (`docs/20`).
- **Run reports** carry stage timings, a QA summary, byte counts for 8 artifact classes,
  `verdict` and `failed_stage` — including when the QA gate blocks the run (`docs/21`).
- **One source of truth for checks**: CI runs only `python scripts/verify.py` — 9 checks
  covering version sync, release-surface files, syntax, the plan gate, assemble smoke,
  two regression fixtures and the site self-check. Local and CI never drift.
- **Honest limits**: 1920×1080 landscape only. Some methodology rules are observations, not
  controlled A/B results. Portrait was tested and deliberately dropped — we do not list it as a
  roadmap promise.

## 7. Reference films

<img src="docs/demo.gif" width="720" alt="demo-hook-entropy · 8s clip, fully generated"/>

| Film | Line | Runtime | QA |
|---|---|---|---|
| demo-hook-entropy | Four-layer composition baseline | 8s | 9.1 |
| demo-hook-compound | SCENE-WRITER + narration + SFX | 11.43s | 8.8 |
| paper-shannon1948 | PAPER2VIDEO explainer | 23.81s | 9.5 |
| paper-shannon-deep | PAPER2VIDEO long form | 180s | 9.2 |
| project-vibe-dsf | PROJECT2VIDEO self-showcase | 50s | 9.1 |

Scores come from each film's `qa.json` on the actual rendered frames (short-film scores are
item-for-item equivalent across v2/v3/v4). Frames, audio and videos are regenerated locally and
are not committed.

## 8. Commercial

The core is MIT, self-hosted and telemetry-free. Services come in three shapes:

| Tier | Fit | Pricing |
|---|---|---|
| Self-host | You have an engineering team and want full control | Free (MIT) |
| Integration | Fit it into your content stack, custom blocks and palettes | Scoped quote |
| Managed series | We deliver episodes, reviewed by our team | Per-series quote |

No SaaS subscription. You pay for your own model API usage and compute; we do not mark up tokens.
See [docs/22-COMMERCIAL.md](docs/22-COMMERCIAL.md) and the [site](site/index.html).

## 9. Documentation map

| Range | Topic |
|---|---|
| 00–09 | Inventory, model profile, flash playbook, style DNA, failure modes, layer templates |
| 10–11 | Gap analysis, engine decision (no Remotion — the engine was never the bottleneck) |
| 12–15 | SCENE-WRITER / narration / PAPER2VIDEO / PROJECT2VIDEO |
| 16 | Full project summary and the bug knowledge base |
| 17–21 | SFX, brand contract, QA v3, QA v4, run reports |
| 22–23 | Commercial positioning, release checklist |
| 24–25 | MVP release surface, one-command acceptance, optional roadmap |

## 10. Legal and maintenance

- Self-authored parts: [MIT](LICENSE); upstream style metrics follow their own licenses (see the
  notice at the end of LICENSE).
- [SECURITY.md](SECURITY.md): disclosure, credential discipline, local-only no-telemetry model,
  dependency list · [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md): community standard.
- Every GitHub push increments `VERSION`, updates `CHANGELOG.md`, and ships a matching annotated
  tag — CI enforces it. Full checklist: [docs/23-RELEASE.md](docs/23-RELEASE.md).

## References

- [DeepSeek pricing](https://api-docs.deepseek.com/zh-cn/quick_start/pricing/) · [Claude Code with DeepSeek](https://api-docs.deepseek.com/zh-cn/quick_start/agent_integrations/claude_code)
- [vibe-knowledge-video](https://github.com/xiazhuo123456789/vibe-knowledge-video) (style metrics) · [vibe-knowledge-film](https://github.com/HeyChengC/vibe-knowledge-film)
- [DSH plugin index](https://dsh.yeyupiaoling.cn/) — deliberately not used; rationale in `docs/00-INVENTORY.md`
