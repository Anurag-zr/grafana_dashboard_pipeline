from app.core.logging_setup import configure_logging
from app.core.config_loader import ConfigLoader
from app.core.db import Database

configure_logging()

settings = ConfigLoader.load_settings()
db = Database(settings)

result = db.test_connection()
print("Connection successful:", result)