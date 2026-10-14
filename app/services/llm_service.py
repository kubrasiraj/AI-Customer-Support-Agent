
from openai import OpenAI

from app.core.config import settings


client = OpenAI(
    api_key=settings.GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
)


def generate_answer(
    system_prompt: str,
    user_prompt: str,
) -> str:
    """Generate an answer using the Groq API."""

    response = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0,
    )

    answer = response.choices[0].message.content

    if not answer or not answer.strip():
        raise ValueError("Groq returned an empty response")

    return answer.strip()
