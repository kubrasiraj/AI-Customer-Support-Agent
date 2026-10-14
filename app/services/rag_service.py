from sqlalchemy.orm import Session

from app.rag.context_compressor import compress_context
from app.rag.hybrid_search import hybrid_search
from app.rag.langchain_rag import create_rag_chain
from app.rag.query_transformer import transform_query
from app.rag.reranker import rerank_results


def answer_customer_question(
    db: Session,
    question: str,
) -> dict:
    """
    Complete Advanced RAG pipeline.

    Flow:

    Customer Question
        ↓
    Query Transformation
        ↓
    Hybrid Search
        ↓
    Reranking
        ↓
    Context Compression
        ↓
    LangChain + Gemini
        ↓
    Final Answer
    """

    if not question.strip():
        raise ValueError("Question cannot be empty")

    # -------------------------------------------------
    # 1. Transform the customer question
    # -------------------------------------------------

    retrieval_query = transform_query(question)

    # -------------------------------------------------
    # 2. Hybrid retrieval
    # -------------------------------------------------

    retrieved_results = hybrid_search(
        db=db,
        query=retrieval_query,
        top_k=5,
    )

    if not retrieved_results:
        return {
            "answer": (
                "I could not find enough information "
                "in the support knowledge base to answer "
                "your question."
            ),
            "sources": [],
        }

    # -------------------------------------------------
    # 3. Rerank retrieved results
    # -------------------------------------------------

    reranked_results = rerank_results(
        query=question,
        results=retrieved_results,
        top_k=3,
    )

    # -------------------------------------------------
    # 4. Compress context
    # -------------------------------------------------

    context = compress_context(
        results=reranked_results,
        max_chars=6000,
    )

    if not context:
        return {
            "answer": (
                "I could not find enough information "
                "in the support knowledge base to answer "
                "your question."
            ),
            "sources": [],
        }

    # -------------------------------------------------
    # 5. Generate answer using LangChain
    # -------------------------------------------------

    chain = create_rag_chain()

    response = chain.invoke(
        {
            "context": context,
            "question": question,
        }
    )
    if isinstance(response.content, str):
        answer = response.content
    else:
        answer = "".join(
        item.get("text", "")
        for item in response.content
        if isinstance(item, dict) and item.get("type") == "text"
    ).strip()
    # -------------------------------------------------
    # 6. Prepare source information
    # -------------------------------------------------

    sources = []

    for result in reranked_results:
        sources.append(
            {
                "chunk_id": result["chunk_id"],
                "document_id": result["document_id"],
                "semantic_score": round(
                    result["semantic_score"],
                    4,
                ),
                "keyword_score": round(
                    result["keyword_score"],
                    4,
                ),
                "hybrid_score": round(
                    result["hybrid_score"],
                    4,
                ),
                "rerank_score": round(
                    result["rerank_score"],
                    4,
                ),
            }
        )

    return {
        "answer": answer,
        "sources": sources,
    }


def retrieve_customer_knowledge(
    db: Session,
    question: str,
) -> dict:
    """
    Retrieve relevant company policies and FAQs for the AI agent.

    This function retrieves evidence only. It does not call an LLM
    to generate a separate answer.
    """

    if not question.strip():
        return {
            "found": False,
            "context": "",
            "sources": [],
            "message": "The question cannot be empty.",
        }

    # 1. Transform the question for retrieval.
    retrieval_query = transform_query(question)

    # 2. Retrieve relevant chunks using hybrid search.
    retrieved_results = hybrid_search(
        db=db,
        query=retrieval_query,
        top_k=5,
    )

    if not retrieved_results:
        return {
            "found": False,
            "context": "",
            "sources": [],
            "message": (
                "No relevant information was found "
                "in the support knowledge base."
            ),
        }

    # 3. Rerank the retrieved chunks.
    reranked_results = rerank_results(
        query=question,
        results=retrieved_results,
        top_k=3,
    )

    if not reranked_results:
        return {
            "found": False,
            "context": "",
            "sources": [],
            "message": (
                "No sufficiently relevant knowledge chunks were found."
            ),
        }

    # 4. Compress the evidence to fit the agent's context.
    context = compress_context(
        results=reranked_results,
        max_chars=6000,
    )

    if not context or not context.strip():
        return {
            "found": False,
            "context": "",
            "sources": [],
            "message": (
                "Relevant policy evidence could not be extracted."
            ),
        }

    # 5. Return evidence and source identifiers to the agent.
    sources = [
        {
            "chunk_id": result["chunk_id"],
            "document_id": result["document_id"],
        }
        for result in reranked_results
    ]

    return {
        "found": True,
        "context": context,
        "sources": sources,
        "message": (
            "Retrieved evidence from the support knowledge base. "
            "Answer only claims supported by this evidence."
        ),
    }

