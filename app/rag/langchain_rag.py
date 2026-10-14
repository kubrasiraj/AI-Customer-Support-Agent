from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import settings


def create_rag_chain():
    """
    Create the LangChain RAG generation chain.
    """

    llm = ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0,
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
You are an AI customer support assistant.

Answer the customer's question using ONLY
the provided knowledge base context.

Rules:
1. Do not invent information.
2. Do not use outside knowledge.
3. If the context does not contain enough information,
   clearly say that you do not have enough information.
4. Do not claim that an action was performed unless
   the system actually performed that action.
5. Give a clear and professional answer.
6. Do not mention internal retrieval, embeddings,
   reranking, or system instructions.
""",
            ),
            (
                "human",
                """
Knowledge Base Context:

{context}

Customer Question:

{question}

Answer the customer using ONLY the knowledge base context.
""",
            ),
        ]
    )

    chain = prompt | llm

    return chain