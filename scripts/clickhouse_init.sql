
            -- Skinlytics Analytics Database Setup
            CREATE DATABASE IF NOT EXISTS skinlytics_analytics;
            
            -- Performance settings
            SET max_memory_usage = 20000000000;
            SET max_bytes_before_external_group_by = 10000000000;
            SET max_bytes_before_external_sort = 10000000000;
            