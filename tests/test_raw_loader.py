from app.core.logging_setup import configure_logging
from app.core.config_loader import ConfigLoader
from app.core.db import Database
from app.extract.csv_extractor import CSVExtractor
from app.load.raw_loader import RawLoader

configure_logging()

settings = ConfigLoader.load_settings()
db = Database(settings)

loader = ConfigLoader("./config/sources.yaml")
sources = loader.load_enabled_sources()

extractor = CSVExtractor()
raw_loader = RawLoader(db)

for source in sources:
    print(f"\n--- {source.source_name} ---")
    new_rows = extractor.extract(source, last_watermark=0)
    raw_ids = raw_loader.load(new_rows, source)
    print(f"Inserted {len(raw_ids)} rows, raw_ids (first 5): {raw_ids[:5]}")