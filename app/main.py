from fastapi import FastAPI
from sqlalchemy import text

from app.db.database import engine
from app.routers.auth import router as auth_router
from app.routers.customers import router as customers_router
from app.routers.orders import router as orders_router
from app.routers.tickets import router as tickets_router
from app.routers.refunds import router as refunds_router
from app.routers.products import router as products_router
from app.routers.knowledge import router as knowledge_router
from app.routers.rag import router as rag_router
from app.routers.agent import router as agent_router
app = FastAPI(
    title="AI Customer Support Resolution Agent",
    description="Production-style AI customer support backend",
    version="1.0.0",
)


app.include_router(auth_router)
app.include_router(customers_router)
app.include_router(orders_router)
app.include_router(tickets_router)
app.include_router(refunds_router)
app.include_router(products_router)
app.include_router(knowledge_router)
app.include_router(rag_router)
app.include_router(agent_router)


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/health/db")
def database_health_check():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return {"database": "connected"}                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   