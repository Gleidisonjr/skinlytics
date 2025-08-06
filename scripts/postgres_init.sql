
            -- Skinlytics Production Database Setup
            CREATE DATABASE skinlytics_prod;
            CREATE USER skinlytics WITH ENCRYPTED PASSWORD 'secure_password_here';
            GRANT ALL PRIVILEGES ON DATABASE skinlytics_prod TO skinlytics;
            
            -- Performance tuning
            ALTER DATABASE skinlytics_prod SET shared_preload_libraries = 'pg_stat_statements';
            ALTER DATABASE skinlytics_prod SET max_connections = 200;
            ALTER DATABASE skinlytics_prod SET shared_buffers = '2GB';
            ALTER DATABASE skinlytics_prod SET effective_cache_size = '6GB';
            ALTER DATABASE skinlytics_prod SET work_mem = '256MB';
            