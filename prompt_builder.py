
def build_prompt(query, chunks, history=[]): 
    context = "\n\n".join([    # it joins the source and file name and pages and chunks 
        f"[Source: {c['doc_name']}, p.{c['page_num']}]\n{c['raw_text']}"
        for c in chunks
    ])
    
    history_text = "\n".join([
        f"User: {h['query']}\nAssistant: {h['answer']}"
        for h in history[-3:]  # last 3 turns only
    ])
    
    return f"""You are a knowledge assistant. Answer only using the context below.
Cite every claim inline as [Source: filename, p.N].
If the answer is not in the context, say "I don't have that information."

Context:
{context}

{"Previous conversation:" + history_text if history_text else ""}

Question: {query}"""