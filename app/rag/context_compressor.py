def compress_context(
    results: list[dict],
    max_chars: int = 6000,
) -> str:
    """
    Combine retrieved chunks into a limited-size context.

    This prevents unnecessarily large context from
    being sent to the LLM.
    """

    if not results:
        return ""

    context_parts = []
    current_length = 0

    for result in results:
        content = result["content"].strip()

        if not content:
            continue

        chunk_text = (
            f"[Knowledge Chunk {result['chunk_id']}]\n"
            f"{content}"
        )

        additional_length = len(chunk_text)

        if current_length + additional_length > max_chars:
            remaining = max_chars - current_length

            if remaining > 100:
                chunk_text = chunk_text[:remaining]
                context_parts.append(chunk_text)

            break

        context_parts.append(chunk_text)
        current_length += additional_length

    return "\n\n".join(context_parts)