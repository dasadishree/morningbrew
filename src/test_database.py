from src.database.db import initialize_database, DB_PATH

initialize_database()
print("Database created!")
print("Location:", DB_PATH)