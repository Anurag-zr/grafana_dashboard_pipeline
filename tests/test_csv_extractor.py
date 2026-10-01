from app.core.logging_setup import configure_logging
from app.core.config_loader import ConfigLoader
from app.extract.csv_extractor import CSVExtractor

configure_logging()

loader = ConfigLoader("./config/sources.yaml")
sources = loader.load_enabled_sources()
extractor = CSVExtractor()

for source in sources:
    print(f"\n--- {source.source_name} ---")

    # Simulate first-ever run (watermark = 0)
    new_rows = extractor.extract(source, last_watermark=0)
    print(f"Rows extracted (watermark=0): {len(new_rows)}")
    print(new_rows.head(2))

    # Simulate a second run with watermark = total rows already (no new rows expected)
    new_rows_again = extractor.extract(source, last_watermark=len(new_rows))
    print(f"Rows extracted (watermark={len(new_rows)}): {len(new_rows_again)} (expect 0)")