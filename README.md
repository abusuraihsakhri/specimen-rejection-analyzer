# Specimen Rejection Analyzer

Analyze laboratory specimen rejection logs with a local browser interface and a separate Python rule-based CLI/API.

## Browser application

Open `web/index.html` in a modern browser, or run a local static server:

```bash
python -m http.server 8080 --directory web
```

Then open http://localhost:8080/. The application also includes a labeled demonstration dataset.

- Import a UTF-8 comma-separated CSV (up to 2 MB).
- Calculate total specimens, rejected specimens, rejection rate, and frequency of rejection reasons.
- Inspect a Pareto summary with cumulative percentages and monthly rejection counts.
- Export the rejection-reason summary as CSV.
- Process data locally in the browser, without a server or external JavaScript libraries.

**Browser CSV schema:** A `reason` or `rejection_reason` column is required. Optional `status` values are `accepted` and `rejected` (also `yes/no`, `true/false`, or `1/0`). Optional `date` uses ISO `YYYY-MM-DD`. Alternative accepted headers include `description`, `rejection_status`, `rejection_date`, and `collection_date`.

```csv
reason,status,date
Hemolyzed sample,rejected,2026-01-05
Clotted specimen,rejected,2026-01-07
,accepted,2026-01-12
```

When there is no status column, every record is counted as a rejection and the **overall rejection rate is not estimable**. Pareto percentages use rejected specimens only. Empty reasons are classified as `Unspecified`. Monthly counts omit missing or invalid ISO dates. No statistical hypothesis test or chi-square trend analysis is implemented.

### GitHub Pages

The static app is compatible with GitHub Pages. `.github/workflows/pages.yml` publishes the `web/` directory after changes are merged to `master`, provided the repository's Pages source has been configured for **GitHub Actions**. The Python FastAPI service does not run on Pages.

## Python CLI and API

Requires Python 3.10 or newer.

```bash
git clone https://github.com/abusuraihsakhri/specimen-rejection-analyzer.git
cd specimen-rejection-analyzer
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

On Windows, activate with `.venv\Scripts\activate`.

### Rejection-reason lookup and batch mapping

```bash
python rejection_analyzer.py single "hemolyzed sample"
python rejection_analyzer.py batch --input sample.csv --output results.csv
```

This command performs **heuristic substring/token matching** against a small reason vocabulary. When no token matches, the result is `No match`. Output is not a validated diagnostic classification.

### Demonstration rule-based evaluation

```bash
specimen-rejection-analyzer audit --task-id TASK-001 --target SPECIMEN-01 --primary 28.5 --secondary 14.2 --critical --status DISCORDANT
specimen-rejection-analyzer batch -i evaluations.csv -o results.csv
specimen-rejection-analyzer verify-audit
specimen-rejection-analyzer chat "Describe the system"
specimen-rejection-analyzer serve --host 127.0.0.1 --port 8000
```

The CLI/API evaluates arbitrary numeric metrics with **unvalidated demonstration thresholds** (>25 for primary, >12 for secondary) and keyword/critical-flag checks. These are not specimen-specific clinical limits and do not constitute CAP, CLSI, ISO or HIPAA certification. The `chat` command returns a deterministic placeholder, **not** clinical inference or a live model.

The FastAPI app exposes `GET /health`, `GET /metrics` (JSON), `POST /api/audit`, `POST /api/chat`, and `GET /api/audit/logs`. Generated API documentation is at `/docs` and `/openapi.json`.

The audit-log endpoint is disabled unless `API_AUDIT_TOKEN` is set. Supply that secret in the `X-Audit-Token` header to read it. Do not expose the API publicly without additional access controls and transport security.

## Privacy and security

- Browser CSV content stays in the current browser session; the static app does not send records to a server or persist them in browser storage.
- Supply **de-identified specimen data only**. The Python regex-based identifier guard recognizes some common identifier formats but cannot establish de-identification or HIPAA Safe Harbor compliance.
- Python evaluations create an **in-memory HMAC-SHA256 audit chain** with per-block signature verification. Set `AUDIT_SECRET_KEY` for a stable signing key. Audit entries are **not persisted** across restarts and are not a durable regulatory audit record.
- The Python CLI restricts file access to the current working directory. Treat uploaded CSV content as untrusted.

## Testing

```bash
python -m pytest -q
python -m compileall -q agents cli.py rejection_analyzer.py enrichment.py simulator.py
node tests/browser-smoke.cjs
```

GitHub Actions tests Python 3.10–3.12, the installed command, browser logic, and dependencies. For the Python API, the Dockerfile and Compose configuration provide a local container option; set `AUDIT_SECRET_KEY` and `API_AUDIT_TOKEN` through a suitable secret manager in deployed environments.

## Technologies and compatibility

Python (stdlib, FastAPI, Pydantic, Uvicorn); vanilla HTML/CSS/JavaScript for the browser. The static app requires a modern browser with ES2020 syntax, `File.text()`, and `Blob` downloads. No Pyodide/PyScript is required.

## License

MIT — see [LICENSE](LICENSE).
