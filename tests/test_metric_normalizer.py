from app.core.logging_setup import configure_logging
from app.core.config_loader import ConfigLoader
from app.extract.csv_extractor import CSVExtractor
from app.normalize.metric_normalizer import MetricNormalizer

configure_logging()

loader = ConfigLoader("./config/sources.yaml")
sources = loader.load_enabled_sources()
extractor = CSVExtractor()
normalizer = MetricNormalizer()

for name in ["Incident_GRC_data", "TM_TFA_data"]:
    source = next(s for s in sources if s.source_name == name)
    rows = extractor.extract(source, last_watermark=0)
    fake_raw_ids = list(range(1, len(rows) + 1))

    normalized = normalizer.normalize(rows, source, fake_raw_ids)
    print(f"\n--- {name} --- total normalized rows: {len(normalized)}")

    if name == "Incident_GRC_data":
        print(normalized[normalized["metric_name"] == "SIRT_Reported"].to_string())
    else:
        print(normalized.head(9).to_string())