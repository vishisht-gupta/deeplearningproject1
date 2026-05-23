import json
import redis

r = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)

def get_history(conversation_id: str) -> list:
    data = r.get(f"conv:{conversation_id}")
    return json.loads(data) if data else []

def save_history(conversation_id: str, query: str, answer: str):
    history = get_history(conversation_id)
    history.append({"query": query, "answer": answer})
    history = history[-10:]  # keep last 10 turns
    r.setex(f"conv:{conversation_id}", 86400, json.dumps(history))  # 24hr TTL