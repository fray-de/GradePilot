# GradePilot

Human-in-the-loop grading assistant for browser-based exam platforms
(initial target: 智学网 / Zhixue). Reads the on-screen answer region,
proposes a score against a rubric using an LLM, and — after teacher
confirmation — types the score and clicks submit.

**Status:** M1 — skeleton, config loader, logging, SQLite schema. UI / OCR /
LLM / automation are stubbed and land in later milestones (see the project
brief).

## Install (development)

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
pip install pytest          # for the test suite
```

## Configure

```bash
cp config.example.yaml config.yaml
cp .env.example .env
# edit .env and set LLM_API_KEY
```

API keys are read from environment variables only. `config.yaml`
references them by name (e.g. `llm.api_key_env: LLM_API_KEY`).

## Run (M1 commands only)

```bash
python -m gradepilot --version
python -m gradepilot --check-config       # prints parsed config; API key masked
python -m gradepilot --init-db            # creates data/gradepilot.db
pytest -q                                 # run the test suite
```

`data/`, logs, screenshots, and the SQLite DB are gitignored.

## Pre-built Windows EXE

GitHub Actions builds a one-file `gradepilot.exe` on every push (workflow:
`.github/workflows/build-windows.yml`). To get a build:

- **Latest commit:** open the Actions tab → pick the most recent run → download
  the `gradepilot-windows-<sha>` artifact (kept 30 days).
- **Tagged release:** push a tag like `v0.1.0`; the workflow attaches
  `gradepilot.exe` to a GitHub Release auto-generated from commit messages.

```bash
git tag v0.1.0
git push origin v0.1.0
```

The exe is portable; drop it next to a `config.yaml` + `.env` and run it from
a terminal.

## Layout

```
gradepilot/
  __main__.py            CLI entry
  config.py              YAML + .env loader, dataclass schema
  logging_setup.py       Console + rotating file logs, API key redaction
  profiles.py            Region/coordinate profile JSON (used from M2)
  capture/               Screen overlay + region screenshot (M2/M3)
  ocr/                   OcrEngine ABC + VLM/Paddle backends (M3)
  grading/               LlmClient ABC + OpenAI-compatible client + prompts (M4)
  automation/            Type-score / click-submit with dry-run + hotkey (M5)
  session/               Runner + SQLite store (papers/sessions tables)
  ui/                    PyQt6 control + rubric editor (M4/M6)
```

## Safety notes

- Default config has `automation.dry_run: true` — submit clicks are simulated
  only. Flip to `false` after you've verified behavior end-to-end.
- A global stop hotkey (default `Esc`) will be wired in M5 to abort mid-action.
- Automating a third-party web platform via simulated input may conflict with
  that platform's Terms of Service. Use responsibly.
