import numpy as np
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

intents = {
    "historical": [
        "show past sales","give me revenue by year","list customers from database",
        "fetch historical data","show the list of unique CompanyName","get customer details",
        "list all suppliers","show employees","what were last year sales",
        "historical report of revenue","show me existing data"
    ],
    "forecast": [
        "predict future sales","forecast next year growth","future market trends",
        "sales prediction","expected revenue","forecast sales trend",
        "predict upcoming revenue","what will be sales next year","future report",
        "estimate growth rate"
    ]
}

intent_embeddings = {
    intent: [model.encode(example) for example in examples]
    for intent, examples in intents.items()
}

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def detect_intent(user_query: str) -> str:
    query_embedding = model.encode(user_query)
    scores = {}
    for intent, vectors in intent_embeddings.items():
        sims = [cosine_similarity(query_embedding, v) for v in vectors]
        scores[intent] = max(sims)
    best_intent = max(scores, key=scores.get)
    if scores[best_intent] < 0.55:
        return "historical"
    return best_intent
