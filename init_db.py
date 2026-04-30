import sys
sys.path.insert(0, "/app")
from app.db.models import User, URL, ClickEvent
from app.db.database import engine
from sqlmodel import SQLModel
SQLModel.metadata.create_all(engine)
print("All tables created successfully!")
