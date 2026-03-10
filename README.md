# React + FastAPI Chat App (`gpt-4.1-nano`)

This repository contains a simple chat application:

- **Frontend:** React (Vite)
- **Backend:** FastAPI (Python)
- **LLM:** OpenAI Responses API using `gpt-4.1-nano`

## 1) Local development setup

### Backend (FastAPI)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Set environment variables in `backend/.env`:

- `OPENAI_API_KEY`
- `OPENAI_MODEL` (defaults to `gpt-4.1-nano`)
- `SYSTEM_PROMPT` (your custom system prompt)

### Frontend (React)

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Default URL: `http://localhost:5173`

## 2) How the chat flow works

1. User enters a message in the React app.
2. Frontend sends all chat messages to `POST /api/chat`.
3. FastAPI prepends your `SYSTEM_PROMPT`.
4. FastAPI calls OpenAI Responses API with `gpt-4.1-nano`.
5. Assistant reply is returned and rendered in UI.

## 3) Azure deployment steps

Below is one common pattern using **Azure App Service** for both frontend and backend.

### Step A: Create Azure resources

1. Create a **Resource Group**.
2. Create two **App Service** apps:
   - `chat-backend-api` (Python runtime)
   - `chat-frontend-web` (Node runtime or static build served by Node)
3. Optionally create **Azure Container Registry** if deploying with containers.

### Step B: Deploy backend (FastAPI)

1. Configure startup command in backend App Service:
   - `uvicorn main:app --host 0.0.0.0 --port 8000`
2. Set application settings (environment variables):
   - `OPENAI_API_KEY`
   - `OPENAI_MODEL=gpt-4.1-nano`
   - `SYSTEM_PROMPT=...your prompt...`
3. Enable CORS to allow your frontend domain (or set strict origins in code).
4. Deploy code (GitHub Actions, Azure DevOps, or zip deploy).
5. Validate `https://<backend-app>.azurewebsites.net/health`.

### Step C: Deploy frontend (React)

1. In frontend App Service, set build commands:
   - `npm install`
   - `npm run build`
2. Set `VITE_API_BASE_URL=https://<backend-app>.azurewebsites.net`.
3. Deploy the frontend code.
4. Verify the app can send chat requests to backend.

### Step D: Production hardening

1. Replace wildcard CORS with your frontend domain.
2. Use **Azure Key Vault** for secrets and reference it from App Service.
3. Enable App Service logs and Application Insights.
4. Configure custom domain + TLS certificates.
5. Add autoscaling rules if traffic grows.

## 4) Optional architecture upgrades

- Use **Azure Static Web Apps** for frontend and **App Service** for backend.
- Use **Azure Container Apps** if you want containerized deployments.
- Add auth with **Microsoft Entra ID**.


## 5) Download source code as ZIP

Run:

```bash
bash scripts/package_source.sh
```

This creates: `dist/website-test-source.zip`.
