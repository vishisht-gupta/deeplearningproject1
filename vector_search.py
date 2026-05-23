from sentence_transformers import SentenceTransformer, CrossEncoder
from pinecone import Pinecone
from rank_bm25 import BM25Okapi
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import numpy as np

# load once at startup
pc = Pinecone(api_key="pcsk_64xy3p_UDKR3G3iSurPSNrrkNmkembX3tinW2T2aWMjjnQsPatd21VPEn8sEQsXFBrVkoA")
index = pc.Index("deeplearningproject1")
model = SentenceTransformer("BAAI/bge-large-en-v1.5")
reranker_model = CrossEncoder("BAAI/bge-reranker-base")

# global BM25 state — updated when new PDF is uploaded
all_chunks = []
tokenized_chunks = []
bm25 = None

def ingest_pdf(pdf_path: str, doc_name: str = None) -> int:
    global all_chunks, tokenized_chunks, bm25

    if doc_name is None:
        doc_name = pdf_path.split("\\")[-1].split("/")[-1]

    # extract text from PDF
    reader = PdfReader(pdf_path)
    pages_text = []
    for page_num, page in enumerate(reader.pages):
        extracted = page.extract_text()
        if extracted:
            pages_text.append((page_num + 1, extracted))

    # chunk text
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    new_chunks = []
    vectors = []

    for page_num, text in pages_text:
        chunks = splitter.split_text(text)
        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_name}_p{page_num}_c{i}"
            embedding = model.encode(chunk).tolist()
            new_chunks.append({
                "text": chunk,
                "doc_name": doc_name,
                "page_num": page_num,
                "doc_id": chunk_id,
                "raw_text": chunk
            })
            vectors.append({
                "id": chunk_id,
                "values": embedding,
                "metadata": {
                    "text": chunk,
                    "doc_name": doc_name,
                    "page_num": page_num
                }
            })

    # upsert to pinecone in batches of 100
    # upsert to pinecone in batches of 20
    for i in range(0, len(vectors), 20):
        try:
            index.upsert(vectors=vectors[i:i+20])
        except Exception as e:
            print(f"Upsert batch {i} failed: {e}, skipping...")
            continue
    # update BM25 with new chunks
    all_chunks = new_chunks
    tokenized_chunks = [chunk["text"].split() for chunk in all_chunks]
    bm25 = BM25Okapi(tokenized_chunks)

    print(f"Ingested {len(new_chunks)} chunks from {doc_name}")
    return len(new_chunks)


def hybrid_search(query: str, org_id: str = None, top_k: int = 10) -> list:
    # vector search
    query_embedding = model.encode(query).tolist()
    vector_results = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True
    )

    hybrid = []
    for match in vector_results["matches"]:
        hybrid.append({
            "text": match["metadata"].get("text", ""),
            "doc_name": match["metadata"].get("doc_name", ""),
            "page_num": match["metadata"].get("page_num", 0),
            "doc_id": match["id"],
            "raw_text": match["metadata"].get("text", "")
        })

    # BM25 search only if chunks are loaded
    if bm25 is not None and all_chunks:
        tokenized_query = query.split()
        bm25_scores = bm25.get_scores(tokenized_query)
        top_bm25_idx = np.argsort(bm25_scores)[::-1][:top_k]
        for idx in top_bm25_idx:
            hybrid.append(all_chunks[idx])

    # deduplicate
    seen = set()
    unique = []
    for chunk in hybrid:
        if chunk["text"] not in seen:
            seen.add(chunk["text"])
            unique.append(chunk)

    return unique


def rerank(query: str, chunks: list, top_k: int = 5) -> list:
    if not chunks:
        return []
    pairs = [[query, chunk["text"]] for chunk in chunks]
    scores = reranker_model.predict(pairs)
    reranked = sorted(
        zip(chunks, scores),
        key=lambda x: x[1],
        reverse=True
    )
    return [
        chunk for chunk, score in reranked
        if score > 0.2
    ][:top_k]

