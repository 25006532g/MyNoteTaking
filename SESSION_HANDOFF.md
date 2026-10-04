# Session Handoff

## Project
Flask note-taking app with a single-page frontend in `src/static/index.html`, SQLAlchemy models/routes, and OpenRouter-backed note translation.

## Current State
- Vercel deployment previously failed because `src/main.py` tried to create SQLite files beneath the read-only `/var/task` directory.
- `src/main.py` now uses `src/database_config.py:get_database_uri`. It selects the pooled PostgreSQL URL when configured, requires a remote database on Vercel, and uses repository-local SQLite only for local development.
- Psycopg 3 is declared in `requirements.txt`; the current app URI helper rewrites PostgreSQL URLs to the Psycopg SQLAlchemy driver.
- The frontend layout is constrained to the viewport. Sidebar note list, editor text area, and translation comparison panes scroll internally.
- Saved-note editor heading is hidden because the title is already in the title input; the `New Note` heading remains visible for drafts.
- Translation preview uses side-by-side original/translated fields with Undo and Confirm actions. The language selector appears only in the translation preview. Traditional Chinese source defaults to English; other sources default to Traditional Chinese. The detected source language is excluded from selectable target languages, and selecting another target retranslates the original text.
- **Current uncommitted change:** `src/static/index.html` adds a post-confirm `Revert to original` button. Confirmation saves the original title/content in `translationOriginal`; Revert restores them and hides the button. Switching notes or creating a draft clears that revert state. Preserve this change.

## Validation
- Run tests with: `.venv/bin/python -m unittest discover -s tests`
- Most recent full run: 13 tests passed.
- Frontend browser checks covered saved/new note heading behavior, translation defaults and manual target changes, and Confirm → Revert behavior.
- `get_errors` reported no errors and `git diff --check` passed after the last UI edit.
- `pytest` is not installed; this repo uses `unittest` tests.

## Deployment Notes
- Configure Vercel project environment variables for `DATABASE_URL` (pooled Neon URL) and `OPEN_ROUTER_KEY`; redeploy after changing variables. Vercel does not read the local `.env` file.
- Keep the direct `DATABASE_URL_UNPOOLED` URL for migration operations, not regular serverless traffic.
- The `.env` attachment exposed live OpenRouter and Neon credentials in a conversation. Revoke/rotate those credentials and update local/Vercel environment values. Never copy secret values into this handoff or commit `.env`.

## Relevant Files
- `src/main.py`: Flask app setup and database initialization.
- `src/database_config.py`: Neon/PostgreSQL versus local SQLite selection.
- `src/services/translation.py`: OpenRouter request and detected-language normalization.
- `src/routes/translation.py`: language validation and translation API endpoint.
- `src/static/index.html`: UI, comparison flow, language selection, and local scrolling.
- `tests/test_database_config.py`, `tests/test_translation.py`: focused database and translation tests.
