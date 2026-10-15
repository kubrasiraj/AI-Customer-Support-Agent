
from pathlib import Path
from uuid import uuid4

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
from app.db.database import get_db, SessionLocal
from app.models.knowledge_document import KnowledgeDocument
from app.models.user import User
from app.schemas.knowledge import KnowledgeDocumentResponse
from app.services.knowledge_service import process_knowledge_document


router = APIRouter(
    prefix="/knowledge",
    tags=["Knowledge Base"],
)

UPLOAD_DIR = Path("app/knowledge")
ALLOWED_EXTENSIONS = {".txt", ".pdf"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def process_document_in_background(document_id: int) -> None:
    """Process a document using an independent database session."""

    db = SessionLocal()

    try:
        document = (
            db.query(KnowledgeDocument)
            .filter(KnowledgeDocument.id == document_id)
            .first()
        )

        if document is None:
            return

        process_knowledge_document(db, document)

    except Exception:
        # The service marks processing failures as "failed".
        # Log the exception here when project logging is configured.
        db.rollback()

    finally:
        db.close()


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
    extension = Path(file.filename or "").suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .txt and .pdf files are supported",
        )

    original_name = Path(file.filename or "document").name
    safe_file_name = f"{uuid4().hex}{extension}"

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    file_path = UPLOAD_DIR / safe_file_name

    try:
        total_size = 0

        with file_path.open("wb") as buffer:
            while True:
                content = file.file.read(1024 * 1024)

                if not content:
                    break

                total_size += len(content)

                if total_size > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="File size must not exceed 10 MB",
                    )

                buffer.write(content)

        if total_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty",
            )

        document = KnowledgeDocument(
            title=title,
            file_name=original_name,
            file_path=str(file_path),
            category=category,
            description=description,
            version=version,
            status="uploaded",
        )

        db.add(document)
        db.commit()
        db.refresh(document)

    except Exception:
        db.rollback()
        file_path.unlink(missing_ok=True)
        raise

    finally:
        file.file.close()

    background_tasks.add_task(
        process_document_in_background,
        document.id,
    )

    return document

@router.post(
    "/documents/{document_id}/reindex",
    response_model=KnowledgeDocumentResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def reindex_knowledge_document(
    document_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(
        require_role("admin", "support")
    ),
    db: Session = Depends(get_db),
):
    document = (
        db.query(KnowledgeDocument)
        .filter(KnowledgeDocument.id == document_id)
        .first()
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge document not found",
        )

    if not Path(document.file_path).is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge document file not found on disk",
        )

    if document.status == "processing":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document is already being processed",
        )

    document.status = "uploaded"
    db.commit()
    db.refresh(document)

    background_tasks.add_task(
        process_document_in_background,
        document.id,
    )

    return document
