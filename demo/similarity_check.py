from openai import OpenAI

client = OpenAI()

def get_embedding(phrase):
    response = client.embeddings.create(
        model="text-embedding-3-large",
        input=phrase
    )

    # Extract and print embedding vector
    embedding = response.data[0].embedding
    return embedding

import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from typing import List, Dict, Any, Optional

def cluster_words_with_helper(
    words: List[str],
    k: Optional[int] = None,
    k_min: int = 2,
    k_max: int = 11,
    random_state: int = 42,
) -> Dict[str, Any]:

    embeddings = np.array([get_embedding(w) for w in words], dtype=np.float32)

    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    X = embeddings / norms

    chosen_k = k
    best_sil = None
    if chosen_k is None:
        k_max_eff = max(k_min, min(k_max, len(words) - 1))
        best = (None, -1.0)
        for kk in range(k_min, k_max_eff + 1):
            km = KMeans(n_clusters=kk, n_init="auto", random_state=random_state)
            labels_tmp = km.fit_predict(X)
            try:
                sil = silhouette_score(X, labels_tmp)
            except Exception:
                sil = -1.0
            if sil > best[1]:
                best = (kk, sil)
        chosen_k, best_sil = best

    if chosen_k == 1:
        labels = np.zeros(len(words), dtype=int)
    else:
        km = KMeans(n_clusters=chosen_k, n_init="auto", random_state=random_state)
        labels = km.fit_predict(X)

    clusters: Dict[int, List[str]] = {}
    for w, lab in zip(words, labels):
        clusters.setdefault(int(lab), []).append(w)

    return {
        "labels": labels.tolist(),
        "clusters": clusters,
        "embeddings": X,
        "k": int(chosen_k),
        "silhouette": best_sil,
    }

words = ["START_NAVIGATE", "VIEW_ROUTES", "CREATE_CALENDER_EVENT", "SET_PLAYBACK_STATE", "OPEN_CAMERA", "TAKE_PHOTO", "CALL_MEETIME", "GET_CURRENT_LOCATION", "START_CALL", "SEARCH_CALL_RECORD", "VIEW_CALL_RECORD", "MAKE_CALL", "READ_EMAIL", "SEND_EMAIL", "WRITE_EMAIL", "PAY_REPAYMENT"]

result = cluster_words_with_helper(words)
print("Chosen k:", result["k"])
for cid, ws in result["clusters"].items():
    print(f"Cluster {cid}: {ws}")
