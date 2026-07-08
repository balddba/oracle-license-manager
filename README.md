# Oracle License Tracker

[![Python](https://img.shields.io/badge/Python-3.13+-blue?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-6.0-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-v4-06B6D4?style=flat-square&logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)
[![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com/)

Take control of your Oracle software compliance. **Oracle License Tracker** is a modern, web-based license management and compliance calculator that tracks your Oracle Customer Support Identifiers (CSIs), maps physical CPU core inventory, and computes real-time license requirements.

Eliminate manual spreadsheets, automate complex processor core factor math, and audit-proof your deployments before Oracle calls.

---

## 🌟 Key Features

### 📊 Real-Time Compliance Dashboard
Know your compliance posture at a glance. The dashboard aggregates all purchased entitlements across contracts and contrasts them against live host CPU core usage, displaying a real-time surplus or shortfall balance.
![Dashboard Overview](docs/images/dashboard.png)

### ⚙️ Automated Core Factor Calculator
Tackle complex Oracle processor core licensing rules automatically.
* Input server CPU details (e.g. `Intel Xeon Platinum` or `AMD EPYC`) and the application automatically queries the preloaded **Oracle Processor Core Factor Table** (e.g., resolving the standard `0.5` factor).
* Supports manual Core Factor overrides for custom virtualization rules (e.g., hard partitioning, IBM PowerVM, or LPARs).
* Calculates both **Processor (CPU)** and **Named User Plus (NUP)** requirements.
![Host Configuration & CPU Profile](docs/images/host_detail.png)

### 📜 Contract & Agreement Repository (CSI)
Keep your Oracle contracts organized.
* Store contracts mapped by their **Customer Support Identifier (CSI)**.
* Log support levels (Standard, Gold, Premier), validity dates, and active renewal alerts.
* Tightly linked to the preloaded **Oracle Technology Price List Catalog** for error-free product selection.
![Agreements List](docs/images/agreements.png)

### 📈 Executive Reports & PDF Exports
Compile auditable snapshots of your compliance estate with a single click.
* **Visual Insights**: Interactive bar charts on the Reports page display compliance balances.
* **Professional PDF Exports**: Generates executive-ready PDF audit reports featuring embedded visual compliance charts, structured summaries, and auto-wrapped inventory tables.
* **Spreadsheet CSV Exports**: Export clean, tabular datasets for integration with third-party tools.
![Executive Reporting Page](docs/images/reports.png)

---

## 🛠️ Tech Stack

### Backend API
* **FastAPI**: Modern, high-performance web framework for building APIs with Python.
* **SQLAlchemy (Async)** & **Alembic**: Asynchronous SQL toolkit and database migration tool.
* **python-oracledb**: Oracle Database thin driver for Python.
* **SQLite (aiosqlite)**: Light-weight, zero-config relational database engine used by default for local development.
* **fpdf2**: PDF generation library for Python.
* **Pydantic**: Data validation and settings management using Python type annotations.
* **Loguru**: Structured, developer-friendly logging.

### Frontend Client
* **React 19**: Modern component-based frontend library.
* **TypeScript**: Typed superset of JavaScript for reliable, robust application development.
* **Vite 8**: Fast frontend build tool and dev server.
* **Tailwind CSS v4**: Utility-first CSS framework for modern styling.
* **HeroUI**: Accessible and beautiful UI component library.
* **React Query (TanStack)**: Asynchronous state management and data fetching.
* **ECharts (echarts-for-react)**: High-performance interactive charting library.

### Tooling & Infrastructure
* **Docker & Docker Compose**: Containerization and multi-container service orchestration.
* **uv**: Lightning-fast Python package installer and resolver.
* **Ruff**: Extremely fast Python linter and formatter.
* **Oxlint**: High-speed JavaScript/TypeScript linter.
* **MkDocs (Material Theme)**: Fast and beautiful documentation site generator.
* **Nginx**: High-performance HTTP server and reverse proxy used for frontend distribution.

---

## 🚀 Quick Start

Get the application running locally in minutes. The default setup uses an embedded SQLite database.

### Running with Docker (Recommended)
Build and spin up the complete application stack (Backend API + React UI) with a persistent volume:
```bash
docker compose up --build
```
* **Web UI**: http://localhost:8080
* **API Endpoints**: http://localhost:8080/api/v1

### Manual Development Setup

#### 1. Backend API (FastAPI)
Ensure you have [uv](https://github.com/astral-sh/uv) installed:
```bash
cd backend
uv sync --extra dev
uv run uvicorn license_tracker.main:app --reload --port 8000
```

#### 2. Frontend App (React + Vite)
```bash
cd frontend
npm install
npm run dev
```
* Access the local development server at http://localhost:5173 (proxies requests to port 8000).

---

## 📖 Documentation & Guides

For deep-dive topics, production setup guides, and database configurations:
* [Getting Started Guide](docs/getting-started.md)
* [Configuration (YAML & Environment)](docs/configuration.md)
* [Oracle Price List Catalog Seed](docs/catalog.md)
* [API Reference](docs/api.md)
* [Development & Contributing](docs/development.md)

*To preview the full MkDocs site locally, run `uv run python scripts/generate_docs.py --serve` and open http://localhost:8000.*
