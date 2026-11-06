# Security Policy

## Supported versions

| Version | Supported |
|---|---|
| Latest `main` | ✅ |
| Latest `vX.Y.Z` tag | ✅ |
| Older tags | ❌ — upgrade to the latest tag for fixes |

We ship fixes as a new tagged release; the version discipline is documented in
`docs/23-RELEASE.md`.

## Reporting a vulnerability

Please use **GitHub Security Advisories** (private report) on this repository, or open an issue
without exploit details if advisories are unavailable. Do **not** paste credentials, tokens, or
reproducible attack payloads into a public issue.

Include: affected version/tag, steps to reproduce, impact, and (if available) a suggested fix.
We will confirm receipt, assess against the local-only threat model below, and publish a fix in a
new tagged release. We do not publish a fixed response SLA because this project is maintained
alongside client work.

## Threat model: local-only, no telemetry

- The pipeline runs **entirely on the operator's machine**: frame rendering (headless Chrome via
  CDP), QA (NumPy/Pillow), audio (edge-tts / local synthesis), assembly (ffmpeg).
- There is **no account system, no server, no telemetry, and no outbound data upload** from the
  pipeline itself. Artifacts are written only into the local project directory.
- Model API keys, if used for planning/creative steps, are held by the operator. **We never host,
  proxy, or collect them.**
- `scripts/env.ps1` and `scripts/env-creative.ps1` contain **placeholders only**. Real keys belong
  in a local, uncommitted copy. Check `git diff` for key fragments before every commit;
  `CONTRIBUTING.md` documents the rule.
- The site (`site/index.html`) is a static, dependency-free page with no analytics, no trackers,
  and no third-party requests.

## Dependencies and upstream notices

- Python: `numpy`, `pillow`, `edge-tts` (see `pipeline/requirements.txt`).
- Node: no npm runtime dependency; rendering uses a local Chrome/Chromium binary.
- ffmpeg: system binary or `imageio-ffmpeg`.
- Upstream style metrics and their licenses are listed in the `LICENSE` third-party notice.
- CI executes only scripts from this repository and does not run external install hooks.

## Out of scope

- Security of model providers' accounts or their APIs.
- The operator's own host, browser profile, network, or any third-party hosting used to publish
  the generated videos or the static site.
- Content rights for source material the operator supplies.

## Hard rule for contributors

Never commit a real `sk-` token, an `.env` file with credentials, or a rendered frame containing
private client material to a public sample. If it happens, rotate the key first, then clean the
history — do not simply delete the file in a later commit.
