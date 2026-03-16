# RiskHalo Frontend

React + Vite frontend for the RiskHalo Behavioral Risk Intelligence dashboard.

## Setup

```bash
npm install
```

## Development

```bash
npm run dev
```

Runs at [http://localhost:5173](http://localhost:5173). Set the backend URL via env or use the default `http://localhost:8000` (see `src/services/api.js`).

## Backend

From the **project root** (RiskHalo_Certification_Challenge):

```bash
uvicorn api_server:app --reload --port 8000
```

Ensure `.env` is configured (e.g. OpenAI API key) and `data/Weekly_Trade_Data_Uploads` exists.

## Build

```bash
npm run build
npm run preview   # preview production build
```

## Environment

- `VITE_API_BASE` – API base URL (default: `http://localhost:8000`)
