# Focus App Agent Instructions

This app is a lightweight personal helper. Keep it tight, reliable, quiet, and
cross-platform. The user has built it over years, so preserve their data and
preferences unless they explicitly ask for a migration or deletion.

## Hard Rules

- Do not reintroduce the VS Code extension or any editor integration unless the
  user explicitly asks for it. The old `vscode-extension/` surface was removed
  because it interfered with the user's VS Code setup.
- Keep the daemon opt-in. Do not auto-start background services by default.
- Target idle resource usage below 50 MB RAM for normal GUI use and near-zero
  CPU while idle. Avoid new polling loops shorter than 60 seconds.
- Keep heavy imports lazy. Dashboard, plotting, audio, tray, Google, and OS hook
  dependencies should load only when the feature needs them.
- Use `src.system.APP_HOME`, `FOCUS_HOME`, and `pathlib` for runtime files. Do
  not hardcode machine-specific paths such as `C:\Users\...` in application code.
- Preserve user data: `config.yml`, `data/daily_tasks.json`,
  `data/sync_queue.json`, Google credential/token files, and logs. Back up or
  quarantine corrupt data before replacing it.
- Runtime JSON/YAML writes must be atomic. Never truncate task/config/sync files
  and then hope the process survives.
- Google sync must be polite: use retry backoff, max retries, a dead queue for
  exhausted actions, and treat remote 404/410 delete responses as success.
- Keep generated files out of the project: `__pycache__/`, `.pytest_cache/`,
  pid files, root runtime logs, exports, `node_modules/`, and
  `vscode-extension/`.
- Prefer the standard library and existing dependencies. Add a dependency only
  when it removes real risk or complexity.

## Cross-Platform Shape

- GUI entry point: `focus_app:main`.
- CLI and legacy launcher: `main.py`.
- Runtime state belongs under `APP_HOME` except when running directly from this
  source checkout, where the existing local data/config remain in place.
- Windows-specific behavior must be guarded behind platform checks or optional
  imports.

## Required Checks

Run these before handing off code changes when the environment allows it:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall -q main.py focus_app.py src tests
.\.venv\Scripts\python.exe -m pip check
```

If formatting Python files, use the repo formatter rather than manual whitespace
churn. If a check is unavailable, state exactly why.

## Documentation

Keep docs close to the real app. Do not describe removed features, stale flags,
or hype-heavy architecture. Prefer short, practical notes that help maintain the
app without making it bigger.
