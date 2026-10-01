from app.core.models import SourceConfig, GlobalSettings

#Valid EVENT config
event_cfg = SourceConfig(
    source_name="IM_Incident_data",
    source_system="IM_Incident",
    source_type="event",
    file_path="./data/IM_Incident_data_updated.csv",
    poll_interval="1d",
    id_column="Incident_ID",
    date_column="Created_Date",
    column_mapping={"Incident_Status": "status", "Category": "category", "Analyst": "owner"},
)
print("Event config OK:", event_cfg.source_name)


#Valid METRIC config (wide)
metric_wide_cfg = SourceConfig(
    source_name="Incident_GRC_data",
    source_system="GRC",
    source_type="metric",
    file_path="./data/Incident_GRC_data.csv",
    poll_interval="1d",
    date_column="Date",
    period_days=7,
    period_anchor="end",
    metric_mode="wide",
    metric_columns=["SIRT_Reported", "EDR", "LogRhythm", "Sentinel", "Incident_"],
)
print("Metric wide config OK:", metric_wide_cfg.source_name)


#Valid METRIC config (long)
metric_long_cfg = SourceConfig(
    source_name="TM_TFA_data",
    source_system="TrendMicro",
    source_type="metric",
    file_path="./data/TM_TFA_data.csv",
    poll_interval="1d",
    date_column="Date",
    period_days=7,
    period_anchor="end",
    metric_mode="long",
    dimension_column="Usecase",
    value_column="Triggers",
    rank_column="Rank",
    row_key_column="RowKey",
)
print("Metric long config OK:", metric_long_cfg.source_name)


#Invalid config -- should raise
try:
    bad_cfg = SourceConfig(
        source_name="Bad_Source",
        source_system="Bad",
        source_type="metric",
        file_path="./data/bad.csv",
        poll_interval="1d",
        # missing period_days, period_anchor, metric_mode -- should fail
    )
except Exception as e:
    print("Correctly rejected bad config:\n", e)



#GlobalSettings test
settings = GlobalSettings()
print("DB URL:", settings.db_url)
print("Log level:", settings.log_level)