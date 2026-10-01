from app.core.logging_setup import configure_logging
from app.core.config_loader import ConfigLoader
from app.core.db import Database
from app.pipeline.pipeline_factory import PipelineFactory

configure_logging()

settings = ConfigLoader.load_settings()
db = Database(settings)

loader = ConfigLoader("./config/sources.yaml")
sources = loader.load_enabled_sources()

factory = PipelineFactory(db)

print("=== FIRST RUN (expect new rows for all 3 sources) ===")
for source in sources:
    pipeline = factory.build(source)
    pipeline.run()

print("\n=== SECOND RUN (expect 0 new rows, watermark should prevent re-extraction) ===")
for source in sources:
    pipeline = factory.build(source)
    pipeline.run()