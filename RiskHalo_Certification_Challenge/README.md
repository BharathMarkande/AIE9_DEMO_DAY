# AIE09 Certification Challenge

## RiskHalo – Behavioral Risk Intelligence Engine for Intraday Traders

### Project Structure (latest)

```
RiskHalo_Certification_Challenge/
│
├── app/                        # Deterministic analytics & session processing
├── rag/                        # Memory & retrieval (embeddings, vector DB, retrievers)
├── agents/                     # Agentic RAG layer (e.g. coach agent)
├── evaluation/                 # RAGAS evaluation scripts & configs
├── deliverables/               # Challenge deliverables (docs, videos, images)
├── ui/                         # React + Vite frontend
├── config/                     # Config files (models, retrievers, evaluation, etc.)
├── data/                       # Input / synthetic data and processed artifacts
├── tests/                      # Automated tests
├── chroma_db/                  # Local vector DB (created at runtime)
├── api_server.py               # FastAPI backend (upload + ask endpoints)
├── main.py                     # Core processing entrypoint
├── pyproject.toml              # Python project & dependencies
└── uv.lock                     # Locked dependency versions
```

### Backend Setup

- **1. Create & activate virtual environment (optional if already using `.venv`):**

```bash
uv sync
```

- **2. Configure environment:**

Create a `.env` file in the project root and set required keys (OPENAI_API_KEY, TAVILY_API_KEY) and ensure `data/Weekly_Trade_Data_Uploads` exists.

- **3. Run the FastAPI server from project root:**

```bash
uvicorn api_server:app --reload --port 8000
```

The backend will be available at `http://localhost:8000`.

### Frontend Setup

From the `ui` directory:

```bash
cd ui
npm install
npm run dev
```

The frontend runs at `http://localhost:5173` and will call the backend at `http://localhost:8000` by default (configurable via `VITE_API_BASE`).

### Running RAGAS Evaluation

- **Multi-query retriever (default):**

```bash
python -m evaluation.run_ragas_evaluation
```

- **Baseline single-query retriever:**

```bash
python -m evaluation.run_ragas_evaluation --baseline
```
