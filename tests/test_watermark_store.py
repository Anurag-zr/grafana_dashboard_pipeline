from app.core.logging_setup import configure_logging
from app.core.config_loader import ConfigLoader
from app.core.db import Database
from app.extract.watermark_store import WatermarkStore

configure_logging()

settings = ConfigLoader.load_settings()
db = Database(settings)
store = WatermarkStore(db)

source_name = "TEST_SOURCE"

initial = store.get_last_watermark(source_name)
print("Initial watermark (expect 0):", initial)

store.update_watermark(source_name, 42)
updated = store.get_last_watermark(source_name)
print("After update (expect 42):", updated)

store.update_watermark(source_name, 100)
final = store.get_last_watermark(source_name)
print("After second update (expect 100):", final)