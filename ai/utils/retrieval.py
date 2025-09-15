import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class Retriever:
    def __init__(self, embeddings, metadata, model=None):
        self.embeddings = embeddings
        self.metadata = metadata
        self.model = model  # sentence-transformers model لاستخدامه عند الحاجة

    def retrieve(self, query, top_k=5, with_context_window=1):
        """
        مع كل chunk مسترجع، أضف سياقه (chunk قبل وبعد)
        """
        if self.model is None:
            raise ValueError("Please provide a sentence-transformers model for encoding queries.")
        query_emb = self.model.encode([query])
        sims = cosine_similarity(query_emb, self.embeddings)[0]
        top_idx = sims.argsort()[-top_k:][::-1]
        selected = set()
        # اجمع نتائج مع نافذة سياق جانبية (مثلا: chunk قبل وبعد كل نتيجة)
        for idx in top_idx:
            for offset in range(-with_context_window, with_context_window+1):
                neighbor_idx = idx + offset
                if 0 <= neighbor_idx < len(self.metadata):
                    selected.add(neighbor_idx)
        selected = sorted(selected)
        results = [self.metadata[i] for i in selected]
        return results

# مثال استخدام:
# from sentence_transformers import SentenceTransformer
# model = SentenceTransformer('all-mpnet-base-v2')
# retriever = Retriever(embeddings, metadata, model)
# results = retriever.retrieve("ماهي شروط القبول؟", top_k=3)
