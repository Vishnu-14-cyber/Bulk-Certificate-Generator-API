import os
import shutil
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
import app.database as database
from app.database import Base, get_db
from app.main import app
from app.service import certificate_service


@pytest.fixture(scope="session")
def test_temp_dir():
    temp_dir = Path(tempfile.mkdtemp(prefix="cert_test_storage_"))
    original_storage = settings.STORAGE_DIR
    settings.STORAGE_DIR = temp_dir
    certificate_service.generator.storage_dir = temp_dir

    yield temp_dir

    # Cleanup after test session
    settings.STORAGE_DIR = original_storage
    certificate_service.generator.storage_dir = original_storage
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def test_db(test_temp_dir):
    test_db_path = test_temp_dir / "test.db"
    test_engine = create_engine(
        f"sqlite:///{test_db_path}",
        connect_args={"check_same_thread": False}
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    # Store originals
    orig_engine = database.engine
    orig_sessionmaker = database.SessionLocal

    # Swap in test database engine and sessionmaker so background threads share it
    database.engine = test_engine
    database.SessionLocal = TestingSessionLocal

    # Create tables
    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # Yield session
    session = TestingSessionLocal()
    yield session
    session.close()

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)

    # Restore originals
    database.engine = orig_engine
    database.SessionLocal = orig_sessionmaker


@pytest.fixture
def client(test_db):
    with TestClient(app) as c:
        yield c
