# Chronos Pipeline

**Data pipeline orchestration and scheduling platform.**

Chronos Pipeline is a lightweight workflow automation platform for orchestrating data processing tasks. It provides a REST API for defining, scheduling, and monitoring multi-step pipelines, with a React dashboard for visualization.

## Features

- **Workflow Engine**: Define multi-step pipelines with dependency resolution
- **Task Scheduling**: Cron-based and event-driven scheduling
- **Analytics Dashboard**: Real-time metrics, success rates, execution history
- **Topological Execution**: Automatic task ordering based on dependencies
- **REST API**: Full CRUD + execution endpoints

## Architecture

```
chronos-pipeline/
├── backend/          # Python FastAPI backend
│   ├── app/          # Application source
│   └── tests/        # Test suite
├── frontend/         # React TypeScript dashboard
│   ├── src/          # Frontend source
│   └── src/__tests__ # Frontend tests
└── docker-compose.yml
```

## Quick Start

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Run Tests

```bash
# Backend
cd backend && python -m pytest tests/ -v

# Frontend
cd frontend && npm test
```

## API

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## License

MIT
