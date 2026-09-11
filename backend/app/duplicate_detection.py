"""
Duplicate Complaint Detection (bonus feature).

Tries to use sentence-transformer embeddings + cosine similarity for a
meaningful semantic comparison. If that model isn't available (e.g. no
internet on first run, or the optional dependency isn't installed), it
degrades to difflib text similarity so the feature never hard-crashes the
demo -- it just gets less precise.
"""
from difflib import SequenceMatcher
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models import Complaint

_embedder = None
_embedder_load_attempted = False


def _get_embedder():
    global _embedder, _embedder_load_attempted
    if _embedder_load_attempted:
        return _embedder
    _embedder_load_attempted = True
    try:
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    except Exception:
        _embedder = None
    return _embedder


def _cosine(a, b) -> float:
    import numpy as np
    a, b = np.array(a), np.array(b)
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def find_likely_duplicate(
    db: Session, new_description: str, threshold: float = 0.80
) -> Tuple[Optional[int], float]:
    """Returns (complaint_id, score) of the most similar past complaint, or (None, 0.0)."""
    if not new_description:
        return None, 0.0

    existing: List[Complaint] = (
        db.query(Complaint)
        .filter(Complaint.detailed_complaint_description.isnot(None))
        .all()
    )
    if not existing:
        return None, 0.0

    embedder = _get_embedder()
    best_id, best_score = None, 0.0

    if embedder is not None:
        new_vec = embedder.encode(new_description)
        for c in existing:
            score = _cosine(new_vec, embedder.encode(c.detailed_complaint_description))
            if score > best_score:
                best_id, best_score = c.id, score
    else:
        for c in existing:
            score = SequenceMatcher(
                None, new_description.lower(), c.detailed_complaint_description.lower()
            ).ratio()
            if score > best_score:
                best_id, best_score = c.id, score

    if best_score >= threshold:
        return best_id, round(best_score, 3)
    return None, round(best_score, 3)
