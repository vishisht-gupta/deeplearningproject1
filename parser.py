import re    # re = Regular Expression module in Python.

def parse_citations(answer: str, chunks: list) -> dict:    # answer LLM generated answer      and chunks from rag
    pattern = r'\[Source: (.+?), p\.(\d+)\]' 
    matches = re.findall(pattern, answer)    # find all matches
    
    sources = []
    for doc_name, page_num in matches:
        match = next((c for c in chunks 
                      if c['doc_name'] == doc_name 
                      and str(c['page_num']) == page_num), None)
        if match:
            sources.append({
                "doc_name": doc_name,
                "page": int(page_num),
                "doc_id": match['doc_id']
            })
    
    # deduplicate
    
    unique_sources =seen = set() 
    for s in sources:
        key = (s['doc_name'], s['page'])
        if key not in seen:
            seen.add(key)
            unique_sources.append(s)
    
    return {"answer": answer, "sources": unique_sources}