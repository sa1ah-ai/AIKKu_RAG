import re
from transformers import AutoTokenizer

class MDChunker:
    def __init__(self, model_name="sentence-transformers/all-mpnet-base-v2", max_tokens=380, overlap=30):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.max_tokens = max_tokens
        self.overlap = overlap

    def load_md_file(self, filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()

    def split_sections(self, md_text):
        # التقسيم على العناوين الفرعية (#, ##, ###)
        headings = list(re.finditer(r'^(#+)\s+(.*)', md_text, flags=re.MULTILINE))
        chunks = []
        for i, heading in enumerate(headings):
            start = heading.end()
            end = headings[i+1].start() if i+1 < len(headings) else len(md_text)
            section_text = md_text[start:end].strip()
            chunks.append({
                'title': heading.group(2).strip(),
                'level': len(heading.group(1)),
                'text': section_text
            })
        return chunks

    def chunk_long_text(self, text, section_title="", section_idx=0):
        tokens = self.tokenizer.encode(text, add_special_tokens=False)
        chunks = []
        i = 0
        chunk_id = 0
        while i < len(tokens):
            chunk_tokens = tokens[i:i+self.max_tokens]
            chunk_text = self.tokenizer.decode(chunk_tokens)
            meta = {
                "chunk_text": chunk_text.strip(),
                "section_title": section_title,
                "section_idx": section_idx,
                "chunk_id": chunk_id,
                "token_start": i,
                "token_end": i+len(chunk_tokens)
            }
            chunks.append(meta)
            i += self.max_tokens - self.overlap
            chunk_id += 1
        return chunks

    def process_md_file(self, filepath):
        md_text = self.load_md_file(filepath)
        sections = self.split_sections(md_text)
        all_chunks = []
        for idx, sec in enumerate(sections):
            sec_text = sec['text'].strip()
            # ignore empty sections
            if not sec_text:
                continue
            token_count = len(self.tokenizer.encode(sec_text, add_special_tokens=False))
            if token_count > self.max_tokens:
                all_chunks.extend(self.chunk_long_text(sec_text, sec['title'], idx))
            else:
                meta = {
                    "chunk_text": sec_text,
                    "section_title": sec['title'],
                    "section_idx": idx,
                    "chunk_id": 0,
                    "token_start": 0,
                    "token_end": token_count
                }
                all_chunks.append(meta)
        return all_chunks

# مثال استخدام
# chunker = MDChunker()
# all_chunks = chunker.process_md_file("data/kk_data.md")
