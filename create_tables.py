# create_tables.py
from api.app.models.database import Base, engine
from api.app.models.document import DocumentUpload, DocumentChunk

if __name__ == "__main__":
    print("⏳ Dropping existing tables...")
    Base.metadata.drop_all(bind=engine)
    print("✅ Tables dropped successfully.")
    
    print("⏳ Creating tables in database...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully.")