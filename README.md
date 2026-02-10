# LabelCheck

AI-powered alcohol label compliance checker for TTB (Alcohol and Tobacco Tax and Trade Bureau) regulatory verification.

## Demo

https://github.com/user-attachments/assets/placeholder

<video src="docs/assets/single_upload.mp4" controls width="600"></video>

*Single label upload and analysis*

## What It Does

Upload photos of alcohol labels and get instant compliance analysis against TTB/COLA regulations. The system uses:

1. **OCR** (Azure Vision) to extract text from label images
2. **Regex rules** for deterministic checks (government warning, alcohol content, net contents)
3. **LLM analysis** (Azure OpenAI) for nuanced compliance checks (brand name, class/type, origin)

Each label receives a verdict: **Pass**, **Fail**, or **Warnings** with detailed findings.

## Quick Start (Docker)

```bash
cp .env.example .env
# Edit .env with your Azure keys

docker compose up --build
```

Open http://localhost:3000

## Local Development

### Backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cd backend
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
source .venv/bin/activate
cd backend
pytest
```

## Environment Variables

See `.env.example`. Key settings:

| Variable | Description |
|----------|-------------|
| `AZURE_VISION_ENDPOINT` | Azure Computer Vision endpoint |
| `AZURE_VISION_KEY` | Azure Computer Vision key |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint |
| `AZURE_OPENAI_KEY` | Azure OpenAI API key |
| `AZURE_OPENAI_DEPLOYMENT` | Model deployment name (default: gpt-4o-mini) |
| `AZURE_OPENAI_API_VERSION` | Azure OpenAI API version (default: 2024-12-01-preview) |
| `DATABASE_URL` | SQLAlchemy database URL (default: sqlite+aiosqlite:///./labelcheck.db) |
| `UPLOAD_DIR` | Directory for uploaded label images (default: ./uploads) |
| `LOG_LEVEL` | Logging level (default: info) |

## Architecture

- **Backend:** Python 3.12, FastAPI, SQLAlchemy (async), SQLite
- **Frontend:** React, TypeScript, Vite, Tailwind CSS
- **AI Services:** Azure Vision (OCR), Azure OpenAI (compliance analysis)
- **Deployment:** Docker Compose (local), Azure Container Apps (production)

## Azure Deployment

### Prerequisites

- [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli) installed
- Azure subscription with Computer Vision and OpenAI resources configured
- `.env` file with your Azure keys (see `.env.example`)

### Deploy

```bash
az login
./scripts/deploy.sh
```

This creates a `labelcheck-containers` resource group with:
- Azure Container Registry (ACR)
- Container Apps Environment
- Backend container (internal ingress, FastAPI)
- Frontend container (external ingress, Nginx + React)

The deploy script outputs your public URL when complete.

### Tear Down

```bash
./scripts/teardown.sh
```

Deletes the entire `labelcheck-containers` resource group. Your AI services in `ttb-label-check` are not affected.
