# ai/rag_server.py
import os
import markdown2
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

from ai.utils.chunking import MDChunker
from ai.utils.embedding import Embedder
from ai.utils.retrieval import Retriever
from ai.utils.generation import build_prompt

# load models once at the start of the server
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EMBED_DIR = os.path.join(BASE_DIR, "embeddings")

# 1- load embeddings and metadata
embedder = Embedder()
embeddings, metadata = embedder.load_embeddings(EMBED_DIR)

# 2- load sentence-transformers
from sentence_transformers import SentenceTransformer
retrieval_model = SentenceTransformer('all-mpnet-base-v2')

retriever = Retriever(embeddings, metadata, retrieval_model)

# 3- load Gemma model
MODEL_ID = "google/gemma-2-2b-it"  # change path according to your device
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
llm_model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    torch_dtype=torch.float16,
    device_map="auto"
)

def gemma_generate(prompt, max_new_tokens=256):
    dialogue_template = [{"role": "user", "content": prompt}]
    formatted_prompt = tokenizer.apply_chat_template(
        conversation=dialogue_template,
        tokenize=False,
        add_generation_prompt=True
    )
    input_ids = tokenizer(formatted_prompt, return_tensors="pt").to("cuda")
    with torch.no_grad():
        outputs = llm_model.generate(
            **input_ids,
            max_new_tokens=max_new_tokens,
            pad_token_id=tokenizer.eos_token_id,
        )
    outputs_decoded = tokenizer.decode(outputs[0], skip_special_tokens=True)
    # return only the answer after "الإجابة:" or "الجواب:"
    if "الإجابة:" in outputs_decoded:
        outputs_decoded = outputs_decoded.split("الإجابة:")[-1].strip()
    elif "الجواب:" in outputs_decoded:
        outputs_decoded = outputs_decoded.split("الجواب:")[-1].strip()
    return outputs_decoded

# build prompt for rag
def build_prompt_rag(query, retrieved_chunks, max_tokens_context=1200):
    context = []
    seen = set()
    total_length = 0
    for chunk in retrieved_chunks:
        t = chunk["chunk_text"].strip()
        if t in seen or not t: continue
        tokens = len(t.split())
        if total_length + tokens > max_tokens_context: break
        context.append(t)
        seen.add(t)
        total_length += tokens
    context_str = "\n".join(context)
    prompt = (
        f"لديك المعلومات التالية:\n{context_str}\n\n"
        f"باستخدام هذه المعلومات فقط، أجب بشكل نقاط واضحة ومنظمة على السؤال التالي:\n"
        f"{query}\n\n"
        f"الإجابة:"
    )
    return prompt


def format_answer_markdown(text):
    """
    convert markdown or plain text to HTML for better display in the chat
    """
    # clean up
    text = text.replace('* *', '-').replace('[UNK]', '')
    # convert Markdown to HTML
    html = markdown2.markdown(text)
    return html

def get_rag_answer(user_query, top_k=3, context_win=0):
    retrieved = retriever.retrieve(user_query, top_k=top_k, with_context_window=context_win)
    prompt = build_prompt_rag(user_query, retrieved)
    answer = gemma_generate(prompt)
    html_answer = format_answer_markdown(answer)
    return html_answer


# # main function to generate the final answer
# def get_rag_answer(user_query, top_k=3, context_win=0):
#     retrieved = retriever.retrieve(user_query, top_k=top_k, with_context_window=context_win)
#     prompt = build_prompt_rag(user_query, retrieved)
#     answer = gemma_generate(prompt)
#     # process the answer: convert \n to <br> or HTML lists if you want
#     answer = answer.replace('\n', '<br>')
#     return answer

