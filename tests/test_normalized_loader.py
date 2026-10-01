from app.core.logging_setup import configure_logging
from app.core.config_loader import ConfigLoader
from app.core.db import Database
from app.extract.csv_extractor import CSVExtractor
from app.load.raw_loader import RawLoader
from app.load.normalized_loader import NormalizedLoader
from app.normalize.event_normalizer import EventNormalizer
from app.normalize.metric_normalizer import MetricNormalizer
from app.core.models import SourceType

configure_logging()

settings = ConfigLoader.load_settings()
db = Database(settings)

loader = ConfigLoader("./config/sources.yaml")
sources = loader.load_enabled_sources()

extractor = CSVExtractor()
raw_loader = RawLoader(db)
normalized_loader = NormalizedLoader(db)
event_normalizer = EventNormalizer()
metric_normalizer = MetricNormalizer()

for source in sources:
    print(f"\n--- {source.source_name} ---")

    new_rows = extractor.extract(source, last_watermark=0)
    if new_rows.empty:
        print("No new rows, skipping.")
        continue

    raw_ids = raw_loader.load(new_rows, source)

    if source.source_type == SourceType.EVENT:
        normalized_df = event_normalizer.normalize(new_rows, source, raw_ids)
        inserted = normalized_loader.load(normalized_df, target="events")
    else:
        normalized_df = metric_normalizer.normalize(new_rows, source, raw_ids)
        inserted = normalized_loader.load(normalized_df, target="metrics")

    print(f"Inserted {inserted} new normalized row(s) (of {len(normalized_df)} total).")

    # Run again immediately with the SAME raw_ids / normalized_df to simulate
    # a retry/duplicate scenario -- should insert 0 the second time.
    if source.source_type == SourceType.EVENT:
        inserted_again = normalized_loader.load(normalized_df, target="events")
    else:
        inserted_again = normalized_loader.load(normalized_df, target="metrics")

    print(f"Second insert attempt (expect 0): {inserted_again}")