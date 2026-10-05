''''''

def build_messages(question: str, hits: list[dict]) -> tuple[list[dict], list[dict]]:

    ref_list = []
    sources = {}

    for index, hit in enumerate(hits, 1):
        metadata = hit["metadata"]
        label = metadata.get("title") or metadata.get("source", "unknown")
        page = metadata.get("page")
        if page is not None:
            label = f"{label}, p.{page}"

        ref = f"{index} (Source: So{label})\n{hit["text"]}"
        ref_list.append(ref)
        sources[str[index]] = label

    context = "\n\n".join(ref_list)
    prompt = f'''User has asked a question that you need to answer to . You are provided the following context: {hits}.
    Answer using only the context given. Cite sources as [n]. If the context doesn't cover the question, say you don't have enough information.
    Do not create answers from sources out of context.'''
    
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user",   "content": f"Question: {question}\n\n{context}"},
    ]
    
    return messages, sources
    