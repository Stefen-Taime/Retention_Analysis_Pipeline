-- Création de la base de données (optionnel car 'default' existe déjà)
CREATE DATABASE IF NOT EXISTS default;

-- Table principale pour les événements bruts
CREATE TABLE IF NOT EXISTS default.viewer_events_raw (
    event_id UUID,
    video_id String,
    user_id String,
    session_id String,
    event_timestamp DateTime64(3, 'UTC'),
    event_type LowCardinality(String),
    video_time_sec UInt32,
    delta_viewers Int8
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(event_timestamp)
ORDER BY (video_id, event_timestamp, video_time_sec, user_id)
SETTINGS index_granularity = 8192;

-- Table pour le résumé de rétention (approche différentielle)
CREATE TABLE IF NOT EXISTS default.video_retention_summary (
    video_id String,
    video_time_sec UInt32,
    event_date Date,
    cumulative_viewers AggregateFunction(sum, Int64)
) ENGINE = AggregatingMergeTree()
PARTITION BY toYYYYMM(event_date)
ORDER BY (video_id, event_date, video_time_sec);

-- Vue matérialisée pour calculer la rétention en temps réel
CREATE MATERIALIZED VIEW IF NOT EXISTS default.video_retention_mv TO default.video_retention_summary AS
SELECT
    video_id,
    video_time_sec,
    toDate(event_timestamp) AS event_date,
    sumState(CAST(delta_viewers AS Int64)) AS cumulative_viewers
FROM default.viewer_events_raw
WHERE event_type IN ('VIEW_SEGMENT_START', 'VIEW_SEGMENT_END')
GROUP BY video_id, video_time_sec, event_date;