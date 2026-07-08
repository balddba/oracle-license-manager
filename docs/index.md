# Oracle License Tracker

Web application for tracking Oracle license agreements, product entitlements, and host CPU inventory.

## Stack

- **Backend:** FastAPI, Pydantic, Alembic, async SQLAlchemy (Oracle, PostgreSQL, or SQLite)
- **Frontend:** React 19, Vite, HeroUI v3, TanStack Query

## Project layout

```
backend/     FastAPI API and Pydantic models with custom SQL queries
frontend/    React UI
config/      YAML configuration
data/        SQLite database directory and Oracle catalog seed data
docs/        MkDocs documentation (this site)
```

## Quick links

| Topic | Description |
|-------|-------------|
| [Getting started](getting-started.md) | Run the API and UI locally with SQLite |
| [Docker](docker.md) | Containerized stack with persistent storage |
| [Configuration](configuration.md) | YAML settings and environment variables |
| [Oracle catalog](catalog.md) | Price list import and product picker |
| [API reference](api.md) | REST endpoints |
| [Development](development.md) | Tests, migrations, and linting |
