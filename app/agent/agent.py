from langchain.agents import create_agent
from langchain_groq import ChatGroq

from app.agent.prompts import SUPPORT_AGENT_SYSTEM_PROMPT
from app.core.config import settings


def create_support_agent(tools: list):
    """Create the AI customer support agent using Groq."""

    llm = ChatGroq(
        model=settings.GROQ_MODEL,
        api_key=settings.GROQ_API_KEY,
        temperature=0,
        max_retries=1,
    )

    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=SUPPORT_AGENT_SYSTEM_PROMPT,
    )

    return agent