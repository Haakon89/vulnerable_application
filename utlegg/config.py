import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # TODO: move to environment before going to prod
    SECRET_KEY = os.environ.get("SECRET_KEY", "utlegg-dev-7f3a91c2")

    DATABASE_URL = os.environ.get(
        "DATABASE_URL", "postgresql://utlegg:utlegg@db:5432/utlegg"
    )

    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", os.path.join(BASE_DIR, "uploads"))
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB

    # Receipts can be photos, scans or PDFs
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "pdf", "svg"}

    APP_NAME = "Utlegg"
    APP_VERSION = "1.4.2"
    COMPANY_NAME = "Nordvik Demo AS"
