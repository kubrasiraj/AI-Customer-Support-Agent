from pathlib import Path

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.core.dependencies import require_role
from app.db.database import get_db
from app.models.knowledge_document import KnowledgeDocument
from app.models.user import User
from app.schemas.knowledge import KnowledgeDocumentResponse
from app.services.knowledge_service import process_knowledge_document


router = APIRouter(
    prefix="/knowledge",
    tags=["Knowledge Base"],
)


UPLOAD_DIR = Path("app/knowledge")

ALLOWED_EXTENSIONS = {
    ".txt",
}


@router.post(
    "/documents",
    response_model=KnowledgeDocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_knowledge_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(...),
    category: str = Form(...),
    description: str | None = Form(None),
    version: str = Form("1.0"),
    current_user: User = Depends(
        require_role("admin", "support")
    ),
    db: Session = Depends(get_db),
):
    """
    Upload a company knowledge document.

    Only admin and support users can add
    documents to the knowledge base.
    """

    # Check file extension.
    extension = Path(
        file.filename or ""
    ).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .txt files are currently supported",
        )

    # Make sure the knowledge directory exists.
    UPLOAD_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Generate a safe file name.
    file_name = Path(
        file.filename or "document.txt"
    ).name

    file_path = UPLOAD_DIR / file_name

    # Save uploaded file.
    with file_path.open("wb") as buffer:
        buffer.write(
            file.file.read()
        )

    # Create database document record.
    document = KnowledgeDocument(
        title=title,
        file_name=file_name,
        file_path=str(file_path),
        category=category,
        description=description,
        version=version,
        status="uploaded",
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    # Process the document in the background.
    background_tasks.add_task(
        process_knowledge_document,
        db,
        document,
    )

    return document