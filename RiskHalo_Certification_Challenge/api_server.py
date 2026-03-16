"""
RiskHalo API server: POST /upload and POST /ask (streaming).
Run from project root: uvicorn api_server:app --reload --port 8000
"""
import os
import json
import tempfile
import traceback

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from main import process_single_file, DATA_FOLDER
from rag.embedder import OpenAIEmbedder
from rag.vector_store import RiskHaloVectorStore
from agents.coach_agent import stream_coach_response

app = FastAPI(title="RiskHalo API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(DATA_FOLDER, exist_ok=True)
_embedder = None
_vector_store = None


def get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = OpenAIEmbedder()
    return _embedder


def get_vector_store():
    global _vector_store
    if _vector_store is None:
        _vector_store = RiskHaloVectorStore()
    return _vector_store


@app.post("/upload")
async def upload(
    file: UploadFile = File(...),
    risk_per_trade: float = Form(...),
):
    if not file.filename or not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(400, "Please upload an Excel file (.xlsx or .xls)")

    if risk_per_trade <= 0:
        raise HTTPException(400, "risk_per_trade must be positive")

    try:
        suffix = os.path.splitext(file.filename)[1] or ".xlsx"
        fd, path = tempfile.mkstemp(suffix=suffix, dir=DATA_FOLDER)
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(await file.read())
            embedder = get_embedder()
            vector_store = get_vector_store()
            analysis = process_single_file(path, embedder, vector_store, declared_risk=risk_per_trade)
            return {
                "success": True,
                "message": "Session analyzed successfully.",
                "behavioral_state": analysis["behavioral_state"],
                "severity_score": analysis["severity_score"],
                "expectancy_summary": analysis["expectancy_summary"],
                "discipline_score": analysis["discipline_score"],
                "narrative_summary": analysis["narrative_summary"],
                "rule_narrative": analysis["rule_narrative"],
            }
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass
    except Exception as e:
        traceback.print_exc()
        msg = str(e) if str(e) else "Upload failed"
        raise HTTPException(500, msg)


@app.post("/ask")
async def ask(request: Request):
    body = await request.json()
    question = body.get("question") if isinstance(body, dict) else None
    if not question or not str(question).strip():
        raise HTTPException(400, "question is required")

    def generate():
        try:
            for chunk in stream_coach_response(str(question).strip()):
                yield f"data: {json.dumps({'text': chunk})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            traceback.print_exc()
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
