# Personal expense bot

Telegram photos of October 2026 bills are written into spreadsheet `1OjR2aknpcvH8BJuAcoR6ksbKm7JZpPXgdbsSxX7MdbI` (`2026.10 Personal Expence`).

## Setup

1. Create a Google service account with the Sheets API enabled and no project role. Share only this workbook with the service-account `client_email` as Editor. Leave the Drive API off. Store the JSON key outside the repo, for example `~/.config/personal-expense/sheets-sa.json`.
2. Download `Qwen3VL-8B-Instruct-Q4_K_M.gguf` and `mmproj-Qwen3VL-8B-Instruct-F16.gguf` from https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct-GGUF into `~/models`.
3. Run `scripts/run-llama-server.sh`. `curl -sf http://127.0.0.1:8080/health` succeeds. If the installed llama.cpp build rejects the GGUF, upgrade the Homebrew formula and run the script again. Keep this model.
4. Copy `deploy/.env.example` to `deploy/.env`. Set `TELEGRAM_BOT_TOKEN`, `SPREADSHEET_ID`, `GOOGLE_APPLICATION_CREDENTIALS`, and `HERMES_HOME`. `TELEGRAM_ALLOWED_USERS` is required: the numeric Telegram user id from `@userinfobot`, not the `@username`. Without it anyone who finds the bot can write to the sheet.
5. Copy `deploy/config.yaml` to `$HERMES_HOME/config.yaml`. It enables the `expense` plugin, limits Telegram to the `expense` toolset (`platform_toolsets`), and sets the bot instruction (`agent.system_prompt`). These keys were not checked against Hermes docs; confirm them against your Hermes version.
6. From `deploy/`, run `HERMES_UID=$(id -u) HERMES_GID=$(id -g) docker compose up -d --build`.

## Check

Send one bill photo to the bot. The reply lists each row as `sheet`, `amount`, and `description`. Those rows are on the named tabs. Summary totals are `SUM` of column C and do not show `#REF!`.
