# SkyNet Phase 1 MVP

Organizational Intelligence System - Meeting Intelligence + Institutional Memory

**Repository**: https://github.com/ScrumMaster3/Skynetskynet-mvp.git

## Overview

SkyNet Phase 1 MVP implements the foundational infrastructure for capturing meeting conversations, synthesizing insights, and distributing them to participants via email.

**Architecture**: Modular monolith with clean service layer separation
**Tech Stack**: FastAPI + Supabase PostgreSQL + GPT-4/Mini + Railway
**Development Approach**: Daily demos, iterative feedback, cloud-native

## Project Structure

```
phase-1-mvp/
├── src/
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration management (Pydantic)
│   │
│   ├── models/              # Database models (SQLAlchemy)
│   ├── schemas/             # Pydantic schemas (API contracts)
│   ├── services/            # Business logic layer
│   ├── repositories/        # Database access layer
│   ├── api/v1/              # FastAPI routes (v1)
│   ├── integrations/        # External API clients
│   ├── database/            # Database connection management
│   └── utils/               # Shared utilities (logging, etc.)
│
├── tests/                   # Test suite
│   ├── test_services/       # Service layer tests
│   └── test_api/            # API endpoint tests
│
├── alembic/                 # Database migrations
│   └── versions/            # Migration scripts
│
├── docker-compose.yml       # Local development environment
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variable template
└── README.md                # This file
```

## Prerequisites

- **Python 3.11+** (or 3.14 for latest features)
- **Supabase Account** (free tier available at https://supabase.com)
- **Git**

**Note:** No Docker required! Supabase provides managed PostgreSQL.

## Quick Start

### 1. Set up Supabase Database

1. Create a free Supabase project at https://supabase.com
2. Go to **Settings → Database → Connection string**
3. Copy the **Session pooler** connection string (IPv4 compatible)
4. Save your credentials for next steps

### 2. Clone and Navigate

```bash
cd "1-implementations/phase-1-mvp"
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add:
# - DATABASE_URL (Supabase pooler connection string)
# - SUPABASE_URL (your Supabase project URL)
# - SUPABASE_PUBLISHABLE_KEY (from Supabase dashboard)
# - OPENAI_API_KEY (required for synthesis)
# - SMTP credentials (for email notifications)
```

### 5. Run Database Migrations

```bash
alembic upgrade head
```

This creates in Supabase:
- **conversations** table (meetings)
- **participants** table (attendees)
- **syntheses** table (AI-generated summaries)

### 6. Start API Server

```bash
# Development mode (with auto-reload)
python -m src.main

# Or using uvicorn directly
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 7. Verify Setup

Open your browser:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Supabase Dashboard**: https://supabase.com/dashboard (view tables)

## Architecture Guardrails

This project follows 12 mandatory architecture guardrails to ensure clean, maintainable, scalable code:

1. **Service Layer Isolation**: Business logic only in services, never in routes
2. **Repository Pattern**: Database access abstracted
3. **Dependency Injection**: All dependencies injected, zero hardcoded
4. **Interface Segregation**: Services depend on Protocols
5. **Pydantic Schemas**: All API inputs/outputs validated
6. **Config from Env**: 12-factor app, all config from environment variables
7. **Error Handling Layers**: Exceptions converted at API boundary
8. **Test Coverage 80%+**: Enforced by CI/CD
9. **Alembic Migrations**: Never manual SQL
10. **API Versioning**: All routes `/v1/` prefix
11. **Structured Logging**: JSON logs with correlation IDs
12. **Pre-commit Hooks**: Automated code quality checks

See `0-Fundamentals/IMPLEMENTATION-PLAN.md` for detailed patterns and examples.

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_services/test_synthesis_service.py
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type check
mypy src/
```

### Database Migrations

```bash
# Create a new migration
alembic revision -m "description of change"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# View migration history
alembic history
```

### Docker Commands

```bash
# Start databases
docker-compose up -d

# Stop databases
docker-compose down

# View logs
docker-compose logs -f

# Rebuild containers
docker-compose up -d --build

# Remove volumes (⚠️ deletes all data)
docker-compose down -v
```

## API Endpoints

### System Endpoints (Not Versioned)

- `GET /` - Root endpoint with API info
- `GET /health` - Health check for monitoring

### v1 API Endpoints (Coming Soon)

- `POST /v1/meetings` - Create new meeting
- `GET /v1/meetings/{id}` - Get meeting details
- `GET /v1/meetings/{id}/synthesis` - Get meeting synthesis
- `POST /v1/search` - Search across meetings

## Environment Variables

See `.env.example` for all available configuration options. Key variables:

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | Supabase PostgreSQL pooler connection string | Yes |
| `SUPABASE_URL` | Supabase project URL | Yes |
| `SUPABASE_PUBLISHABLE_KEY` | Supabase anon/public key | Yes |
| `OPENAI_API_KEY` | OpenAI API key for synthesis | Yes |
| `SMTP_HOST` | SMTP server for emails | Yes |
| `SMTP_USER` | SMTP username | Yes |
| `SMTP_PASSWORD` | SMTP password | Yes |

## Troubleshooting

### Database Connection Errors

**Problem:** Can't connect to Supabase

**Solution:**
```bash
# 1. Verify your DATABASE_URL uses the pooler connection (not direct)
# Example: postgresql://postgres.PROJECT:PASSWORD@aws-1-REGION.pooler.supabase.com:5432/postgres

# 2. Check Supabase project is active (not paused)
# Visit: https://supabase.com/dashboard

# 3. Verify connection pooling is enabled
# Supabase Dashboard → Settings → Database → Connection Pooling

# 4. Test connection with psql
psql "$DATABASE_URL" -c "SELECT version();"
```

### Import Errors

```bash
# Ensure virtual environment is activated
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Port Already in Use

```bash
# Find process using port 8000 (Windows)
netstat -ano | findstr :8000

# Find process using port 8000 (macOS/Linux)
lsof -i :8000

# Kill process or change API_PORT in .env
```

## Development Timeline

### Week 1 - COMPLETE ✅
- ✅ Day 1: Project scaffold, Docker, FastAPI minimal app
- ✅ Day 2: Database models, repositories, migrations
- ✅ Day 3: Transcription service (Whisper + Soniox stub), file upload, API endpoints
- ✅ Day 4: Synthesis service (GPT-4), extract decisions/actions/questions, API endpoints
- ✅ Day 5: Email service (SMTP), HTML templates, delivery tracking, API endpoints

### Architecture Migration - COMPLETE ✅ (Feb 2026)
- ✅ Migrated from local Docker to Supabase PostgreSQL
- ✅ Removed Neo4j dependency (planned for Phase 2)
- ✅ Implemented connection pooling for IPv4 compatibility
- ✅ Updated all configuration for cloud-native deployment
- ✅ Verified database migrations with Supabase

### MVP Status
**Complete End-to-End Pipeline**: Audio → Transcript → Synthesis → Email ✅
**Production Ready**: Supabase + Railway deployment configured ✅

**Next steps:**
- Deploy to Railway for production testing
- Implement Phase 2 knowledge graph features
- Add meeting bot integration (Zoom/Teams)

## Contributing

This is currently a solo development project with daily progress demos.

### Code Style
- Follow PEP 8
- Use Black for formatting
- Use type hints everywhere
- Write docstrings for all public functions

### Commit Messages
- Use present tense ("Add feature" not "Added feature")
- Reference issue numbers when applicable
- Keep first line under 50 characters

## Deployment

For production deployment to Railway with Supabase, see:
- **[Supabase + Railway Deployment Guide](SUPABASE-RAILWAY-DEPLOYMENT.md)** ⭐

## Resources

- **Deployment Guide**: `SUPABASE-RAILWAY-DEPLOYMENT.md`
- **Project Documentation**: `../../0-Fundamentals/`
- **Implementation Plan**: `../../0-Fundamentals/IMPLEMENTATION-PLAN.md`
- **Competitive Analysis**: `../../0-Fundamentals/COMPETITIVE-ANALYSIS.md`
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **SQLAlchemy Docs**: https://docs.sqlalchemy.org/
- **Supabase Docs**: https://supabase.com/docs
- **Railway Docs**: https://docs.railway.app

## License

[To be determined]

## Contact

[To be added]

---

**Built with ❤️ by Claude (AI Agent) + Human Collaboration**
