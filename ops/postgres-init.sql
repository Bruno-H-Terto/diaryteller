-- Local development roles. Production credentials come from a secret manager.
CREATE ROLE diary_identity LOGIN PASSWORD 'diary_identity';
CREATE ROLE diary_notifications LOGIN PASSWORD 'diary_notifications';
CREATE ROLE diary_maintenance LOGIN PASSWORD 'diary_maintenance';
ALTER DATABASE diary OWNER TO diary_identity;
GRANT CONNECT ON DATABASE diary TO diary_notifications, diary_maintenance;

-- Dedicated database for exchange-owned tables.
CREATE DATABASE exchange OWNER diary;
GRANT CONNECT ON DATABASE exchange TO diary_notifications, diary_maintenance;
