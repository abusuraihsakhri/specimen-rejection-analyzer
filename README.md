# Specimen Rejection Analyzer

> **Domain:** Clinical Decision Support & Biomedical Computing
> **Standards:** CAP / CLSI / ISO Standards

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## Overview

Specimen Rejection Analyzer processes pre-analytical error logs to identify rejection patterns using pareto analysis and chi-square trend detection. It provides a stdlib-based parser/mapper with batch CSV processing and single lookup capabilities for clinical laboratory workflows.

---

## Key Features

### Core Analysis
- **Token-based Lookup**: Substring scoring and token overlap matching for specimen rejection reason classification
- **CSV Batch Processing**: Process multiple records with automatic column detection
- **Pareto Analysis**: Identify the most frequent rejection causes
- **Multi-worker Evaluation**: Distributed component architecture with QC, Safety, and Protocol Conformance workers

### Security
- **Zero-PHI Outbound Guard**: AST and regex inspection blocking SSNs, MRNs, phone numbers, emails, and patient identifiers
- **HMAC-SHA256 Audit Trail**: Chained, cryptographically signed logs for every evaluation
- **Path Traversal Protection**: Safe file I/O with working directory containment

### API & CLI
- **FastAPI REST Server**: OpenAPI 3.1 endpoints with Prometheus metrics
- **CLI Interface**: Interactive and parameterized modes for single and batch processing
- **WebSocket Telemetry**: Real-time streaming of evaluation events

---

## Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/specimen-rejection-analyzer.git
cd specimen-rejection-analyzer

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install fastapi uvicorn pydantic pytest
```

---

## Usage

### CLI Commands

#### Single Task Evaluation
```bash
python cli.py audit --task-id TASK-001 --target SPECIMEN-01 --primary 28.5 --secondary 14.2 --critical --status DISCORDANT
```

#### Batch CSV Processing
```bash
python cli.py batch -i sample.csv -o results.csv
```

#### Supervisory Chat
```bash
python cli.py chat "What are common rejection reasons?"
```

#### Verify Audit Integrity
```bash
python cli.py verify-audit
```

#### Launch REST Server
```bash
python cli.py serve --host 127.0.0.1 --port 8000
```

### Direct Analyzer Module
```bash
# Single lookup
python rejection_analyzer.py single creatinine

# Batch CSV processing
python rejection_analyzer.py batch --input sample.csv --output results.csv
```

### REST API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/metrics` | Prometheus metrics |
| POST | `/api/audit` | Submit task for evaluation |
| POST | `/api/chat` | Supervisory chat query |
| GET | `/api/audit/logs` | Retrieve audit trail |

---

## Input Data Schema

### CSV Batch Format
```csv
task_id,target_identifier,primary_metric,secondary_metric,status_descriptor,is_critical_flag
TASK-001,SPECIMEN-01,28.5,14.2,DISCORDANT,false
TASK-002,SPECIMEN-02,10.5,3.1,NOMINAL,false
```

### Field Descriptions

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `task_id` | string | Unique task/case identifier | Yes |
| `target_identifier` | string | Specimen or target identifier | Yes |
| `primary_metric` | float | Primary measurement value | Yes |
| `secondary_metric` | float | Secondary measurement value | No (default: 0.0) |
| `status_descriptor` | string | Status code (NOMINAL, DISCORDANT, etc.) | No (default: NOMINAL) |
| `is_critical_flag` | boolean | Critical escalation flag | No (default: false) |

---

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AUDIT_SECRET_KEY` | HMAC signing key for audit trail | Auto-generated (ephemeral) |
| `MODEL_PROVIDER` | LLM provider (mock, ollama, claude, openai) | mock |

---

## Testing

```bash
# Run full test suite
pytest -v

# Run with coverage
pytest -v --cov=agents --cov=.

# Run specific test module
pytest tests/test_cli_security.py -v
```

### Test Coverage
- PHI guard enforcement
- Worker evaluation logic
- Supervisor consensus and audit
- CLI security (path traversal, input validation)
- Enrichment engine execution

---

## Docker Deployment

```bash
# Build and run with Docker Compose
export AUDIT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
docker compose up --build

# Or use Docker directly
docker build -t specimen-rejection-analyzer .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=$AUDIT_SECRET_KEY specimen-rejection-analyzer
```

---

## Project Structure

```
specimen-rejection-analyzer/
├── agents/                  # Enterprise agent framework
│   ├── api.py              # FastAPI REST server
│   ├── base.py             # Security, PHI guard, audit trail
│   ├── learning.py         # Bayesian calibration engine
│   ├── llm_factory.py      # LLM provider abstraction
│   ├── metrics.py          # Prometheus metrics
│   ├── models.py           # Pydantic data models
│   ├── streamer.py         # WebSocket telemetry
│   ├── supervisor.py       # Multi-agent orchestrator
│   └── workers.py          # Domain-specific workers
├── tests/                  # Test suite
│   ├── test_cli_security.py
│   ├── test_enrichment.py
│   └── test_specimen_rejection_analyzer.py
├── cli.py                  # Command-line interface
├── rejection_analyzer.py   # Core analyzer module
├── enrichment.py           # Enrichment feature engines
├── simulator.py            # Stress testing simulator
├── pyproject.toml          # Project metadata
├── Dockerfile              # Container build
├── docker-compose.yml      # Container orchestration
└── web/index.html          # Operations console UI
```

---

## License

MIT License - see [LICENSE](LICENSE) for details.
