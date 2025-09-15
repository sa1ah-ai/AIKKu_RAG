from sentence_transformers import SentenceTransformer
import numpy as np
import json
import os

class Embedder:
    def __init__(self, model_name="all-mpnet-base-v2"):
        self.model = SentenceTransformer(model_name)

    def encode_chunks(self, chunks, batch_size=32):
        texts = [chunk['chunk_text'] for chunk in chunks]
        embeddings = self.model.encode(texts, show_progress_bar=True, batch_size=batch_size)
        return embeddings

    def save_embeddings(self, embeddings, chunks, out_dir="embeddings"):
        os.makedirs(out_dir, exist_ok=True)
        np.save(os.path.join(out_dir, "embeddings.npy"), embeddings)
        # حفظ كل الميتاداتا مع chunk النص الأصلي
        with open(os.path.join(out_dir, "metadata.json"), "w", encoding="utf-8") as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)

    def load_embeddings(self, out_dir="embeddings"):
        embeddings = np.load(os.path.join(out_dir, "embeddings.npy"))
        with open(os.path.join(out_dir, "metadata.json"), encoding="utf-8") as f:
            metadata = json.load(f)
        return embeddings, metadata

# مثال استخدام:
# embedder = Embedder()
# embeddings = embedder.encode_chunks(all_chunks)
# embedder.save_embeddings(embeddings, all_chunks)
