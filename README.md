# LabelCheck

AI-powered alcohol label compliance checker for TTB (Alcohol and Tobacco Tax and Trade Bureau) regulatory verification.

## What It Does

Upload photos of alcohol labels and get instant compliance analysis against TTB/COLA regulations. The system uses:

1. **OCR** (Azure Vision) to extract text from label images
2. **Regex rules** for deterministic checks (government warning, alcohol content, net contents)
3. **LLM analysis** (Azure OpenAI) for nuanced compliance checks (brand name, class/type, origin)

Each label receives a verdict: **Pass**, **Fail**, or **Warnings** with detailed findings.

## Quick Start (Docker)

```bash
cp .env.example .env
# Edit .env with your Azure keys, or leave USE_MOCK_SERVICES=true for demo mode

docker-compose up --build
```

Open http://localhost:3000

## Local Development

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API available at http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Dev server at http://localhost:5173 (proxies /api to backend)

## Testing

```bash
cd backend
source .venv/bin/activate
pytest
```

## Environment Variables

See `.env.example`. Key settings:

| Variable | Description |
|----------|-------------|
| `USE_MOCK_SERVICES` | `true` for demo mode (no Azure keys needed) |
| `AZURE_VISION_ENDPOINT` | Azure Computer Vision endpoint |
| `AZURE_VISION_KEY` | Azure Computer Vision key |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint |
| `AZURE_OPENAI_KEY` | Azure OpenAI API key |
| `AZURE_OPENAI_DEPLOYMENT` | Model deployment name (default: gpt-4o-mini) |

## Architecture

- **Backend:** Python 3.12, FastAPI, SQLAlchemy (async), SQLite
- **Frontend:** React, TypeScript, Vite, Tailwind CSS
- **AI Services:** Azure Vision (OCR), Azure OpenAI (compliance analysis)
- **Deployment:** Docker Compose
