-- 🐘 PostgreSQL Initialization Script for Skinlytics
-- Creates database, extensions, and initial setup

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_skins_market_hash_name ON skins(market_hash_name);
CREATE INDEX IF NOT EXISTS idx_listings_skin_id ON listings(skin_id);
CREATE INDEX IF NOT EXISTS idx_listings_price ON listings(price);
CREATE INDEX IF NOT EXISTS idx_listings_created_at ON listings(created_at_csfloat);

-- Create materialized view for analytics
CREATE MATERIALIZED VIEW IF NOT EXISTS skins_analytics AS
SELECT 
    s.market_hash_name,
    s.item_name,
    COUNT(l.id) as total_listings,
    AVG(l.price) as avg_price,
    MIN(l.price) as min_price,
    MAX(l.price) as max_price,
    AVG(l.float_value) as avg_float
FROM skins s
LEFT JOIN listings l ON s.id = l.skin_id
GROUP BY s.id, s.market_hash_name, s.item_name;

-- Create function to refresh materialized view
CREATE OR REPLACE FUNCTION refresh_skins_analytics()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW skins_analytics;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO skinlytics_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO skinlytics_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO skinlytics_user;