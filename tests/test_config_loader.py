from app.core.logging_setup import configure_logging
from app.core.config_loader import ConfigLoader

configure_logging()

loader = ConfigLoader("./config/sources.yaml")

sources = loader.load_enabled_sources()
print(f"\nLoaded {len(sources)} enabled sources:")
for s in sources:
    print(f" - {s.source_name} ({s.source_type}) -> {s.file_path}")

settings = ConfigLoader.load_settings()
print("\nDB URL:", settings.db_url)
