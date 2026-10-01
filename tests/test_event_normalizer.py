from app.core.logging_setup import configure_logging
from app.core.config_loader import ConfigLoader
from app.extract.csv_extractor import CSVExtractor
from app.normalize.event_normalizer import EventNormalizer

configure_logging()

loader = ConfigLoader("./config/sources.yaml")
sources = loader.load_enabled_sources()
im_source = next(s for s in sources if s.source_name == "IM_Incident_data")

extractor = CSVExtractor()
rows = extractor.extract(im_source, last_watermark=0)

fake_raw_ids = list(range(1, len(rows) + 1))  # placeholder, real ids come from RawLoader

normalizer = EventNormalizer()
normalized = normalizer.normalize(rows, im_source, fake_raw_ids)

print(normalized.head(3).to_string())
print("\nColumns:", list(normalized.columns))
print("\nSample details blob:", normalized.iloc[0]["details"])