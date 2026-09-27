"""Shared embedding model loader.

Both engine/commodity_matcher.py and engine/faq_matcher.py embed short text
with the same local model — factored out here so the model is loaded into
memory once at startup, not once per feature.

Backed by fastembed (onnxruntime), not sentence-transformers/torch. A memory
audit ahead of a Render free-tier (512MB) deploy found the app sitting at
~640MB RSS at idle, almost entirely from `import torch` (~180MB) plus the
model graph — and switching sentence-transformers to its own ONNX backend
did NOT help, because sentence-transformers imports torch unconditionally
at package-import time regardless of which inference backend you configure;
its Pooling/Normalize modules are torch.nn.Module subclasses. Verified
empirically before writing this: `import fastembed` never touches
sys.modules['torch'] at all.

fastembed runs the exact same checkpoint — its "sentence-transformers/
all-MiniLM-L6-v2" entry is Qdrant's ONNX export of that identical model
(qdrant/all-MiniLM-L6-v2-onnx), not a different model — through onnxruntime
directly, with no torch anywhere in the import chain.

The model files are bundled in models/embedding_cache/ (not fetched from
Hugging Face at boot), so a Render deploy never depends on outbound network
access at startup, and a cold instance can't fail to serve because Hugging
Face was unreachable.
"""

from pathlib import Path

import numpy as np

_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
_MODEL_CACHE_PATH = Path(__file__).resolve().parent.parent / "models" / "embedding_cache"
# onnxruntime's CPU arena allocator grows to fit the largest single inference
# call it has ever seen, then keeps that memory reserved for the life of the
# process — it does not shrink back down. Measured directly: embedding our
# ~80 commodities in one batch (fastembed's default batch_size=256) left the
# process ~180MB heavier than embedding them 8-at-a-time, for the exact same
# output. Small and fixed regardless of how large data/commodities.json or
# data/faq.json grow, since it bounds the batch, not the total item count.
_ENCODE_BATCH_SIZE = 8
_model = None


class _FastEmbedModel:
    """Adapter over fastembed.TextEmbedding exposing the same
    `.encode(texts, normalize_embeddings=True) -> np.ndarray` surface that
    sentence_transformers.SentenceTransformer did — so commodity_matcher.py
    and faq_matcher.py, which call `get_shared_model().encode(...)`, needed
    no changes when the backend swapped."""

    def __init__(self) -> None:
        # Imported lazily so importing this module doesn't require fastembed
        # unless embedding is actually used.
        from fastembed import TextEmbedding

        self._model = TextEmbedding(model_name=_MODEL_NAME, specific_model_path=str(_MODEL_CACHE_PATH))

    def encode(self, texts: list[str], normalize_embeddings: bool = True) -> np.ndarray:
        embeddings = np.array(list(self._model.embed(texts, batch_size=_ENCODE_BATCH_SIZE)))
        if normalize_embeddings:
            # fastembed already returns L2-normalized vectors for this model
            # (verified empirically), but normalizing explicitly here doesn't
            # depend on that staying true, and matches what callers asked for.
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            embeddings = embeddings / np.where(norms == 0, 1, norms)
        return embeddings


def get_shared_model():
    global _model
    if _model is None:
        _model = _FastEmbedModel()
    return _model
