# Parallel Security Scanner

A FastAPI application that performs comprehensive security scans on target URLs using multiple specialized tools in parallel.

## Overview

This scanner orchestrates four security testing tools to identify vulnerabilities in web applications:

- **Nuclei** - Template-based vulnerability scanner that checks for known security issues and misconfigurations
- **OWASP ZAP** - Dynamic security analysis tool that performs baseline scanning for web application vulnerabilities
- **Giskard** - LLM-based security testing tool that evaluates language models for harmful outputs and safety issues

All tools run in parallel Docker containers, generating HTML and JSON reports in the `/reports` directory.

## Requirements

- Docker Desktop (with Docker Compose)
- Ollama running locally on port 11434 (for Giskard LLM scanning)
- Python 3.10+

## Quick Start

### 1. Start the Scanner Server

```bash
cd Part4
docker compose build
docker compose up -d
```

The server will be available at `http://localhost:8000`

### 2. Start a Security Scan

```bash
curl -X POST "http://localhost:8000/scan/all?target=https://example.com&model_name=llama3"
```

**Parameters:**
- `target` - Target URL to scan (default: http://testphp.vulnweb.com)
- `model_name` - Ollama model for Giskard (default: llama3)

**Response:**
```json
{
  "scan_id": "uuid-string",
  "status": "all_tools_triggered",
  "target": "https://example.com"
}
```

### 3. Check Scan Status

```bash
curl "http://localhost:8000/scan/status/{scan_id}"
```

### 4. View Reports

Reports are generated in the `./reports` directory:
- `nuclei_{scan_id}.html` - Template-based scan report
- `nuclei_{scan_id}.json` - Raw Nuclei findings
- `zap_{scan_id}.html` - ZAP baseline scan report
- `giskard_{scan_id}.html` - LLM safety assessment report

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/scan/all` | Start a new security scan |
| GET | `/scan/status/{scan_id}` | Get scan progress and status |
| GET | `/scans` | List all scans in memory |

## Project Structure

```
Part4/
├── main.py                    # FastAPI application with scan orchestration
├── giskard_wrapper.py         # LLM security testing wrapper
├── nuclei_html_report.py      # Nuclei JSON to HTML converter
├── docker-compose.yml         # Container definitions
├── Dockerfile                 # Python environment setup
├── requirements.txt           # Python dependencies
└── reports/                   # Output directory for scan reports
```

## Stopping the Service

```bash
docker compose down
```

## Notes

- Scans run asynchronously in background threads
- Reports are written to disk as soon as each tool completes
- Nuclei JSON output is automatically converted to an HTML report
- ZAP returns exit code 2 for warnings, which is treated as success
