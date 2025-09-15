def build_prompt(query, retrieved_chunks, max_tokens_context=1800):
    """
    دمج الـchunks مع حذف التكرار إذا أمكن، وبناء برومبت قوي.
    """
    context = []
    used = set()
    total_length = 0

    # أضف عناوين chunk لسهولة تفسير المصدر بالنص النهائي
    for chunk in retrieved_chunks:
        t = chunk["chunk_text"].strip()
        title = chunk.get("section_title", "")
        unique = f"{title}:::{t}"
        tokens = len(t.split())
        if unique not in used and total_length + tokens <= max_tokens_context:
            context.append(f"[{title}]\n{t}\n")
            used.add(unique)
            total_length += tokens

    context_str = "\n\n".join(context)
    prompt = (
        "استخدم المعلومات التالية للإجابة عن السؤال بدقة، مع ذكر التفاصيل عند توفرها.\n\n"
        f"المعلومات:\n{context_str}\n"
        f"السؤال: {query}\n"
        "الإجابة:"
    )
    return prompt
