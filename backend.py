from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel
import tempfile, os
from vector_search import hybrid_search, rerank, ingest_pdf
from prompt_builder import build_prompt
from llm_client import generate_answer, explain_image
from parser import parse_citations
from memory import get_history, save_history
from pdf_extractor import extract_images_from_pdf

router = APIRouter()

class QueryRequest(BaseModel):
    query: str
    conversation_id: str

@router.post("/query")
async def query(body: QueryRequest):
    try:
        chunks = hybrid_search(body.query, top_k=10)
        chunks = rerank(body.query, chunks, top_k=5)
    except Exception as e:
        print(f"Search error: {e}")
        chunks = []

    try:
        history = get_history(body.conversation_id)
    except Exception as e:
        print(f"History error: {e}")
        history = []

    if chunks:
        prompt = build_prompt(body.query, chunks, history)
    else:
        prompt = body.query

    try:
        answer = await generate_answer(prompt)
    except Exception as e:
        print(f"LLM error: {e}")
        return {"answer": f"Error: {str(e)}", "sources": []}

    if chunks:
        try:
            result = parse_citations(answer, chunks)
        except:
            result = {"answer": answer, "sources": []}
    else:
        result = {"answer": answer, "sources": []}

    try:
        save_history(body.conversation_id, body.query, result['answer'])
    except Exception as e:
        print(f"Save history error: {e}")

    return result


@router.post("/analyze-pdf")
async def analyze_pdf(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        # 1 — ingest text into vector DB
        doc_name = file.filename
        total_chunks = ingest_pdf(tmp_path, doc_name)

        # 2 — extract images and explain
        images = extract_images_from_pdf(tmp_path)
        results = []
        for img_data in images:
            explanation = await explain_image(img_data["image"])
            results.append({
                "page": img_data["page"],
                "explanation": explanation
            })

        return {
            "total_pages": len(results),
            "total_chunks": total_chunks,
            "results": results
        }
    finally:
        os.unlink(tmp_path)