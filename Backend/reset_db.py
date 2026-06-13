from Backend.database import engine
from Backend.models import Base
import time

from sqlalchemy import text

def reset_database():
    print("Beginning database reset...")
    try:
        # Forcefully drop everything using raw SQL with CASCADE
        # This handles legacy tables that SQLAlchemy doesn't know about
        print("Dropping all tables (CASCADE)...")
        with engine.connect() as conn:
            conn.execute(text("DROP SCHEMA public CASCADE;"))
            conn.execute(text("CREATE SCHEMA public;"))
            conn.execute(text("GRANT ALL ON SCHEMA public TO postgres;"))
            conn.execute(text("GRANT ALL ON SCHEMA public TO public;"))
            conn.commit()
        print("All tables dropped.")
        
        # Give it a second
        time.sleep(2)
        
        # Recreate all tables
        print("Creating new tables...")
        Base.metadata.create_all(bind=engine)
        print("Database schema successfully rebuilt!")
        
    except Exception as e:
        print(f"Error during reset: {e}")

if __name__ == "__main__":
    reset_database()
