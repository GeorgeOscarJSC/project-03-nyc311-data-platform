DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM nyc311_requests
        WHERE created_date IS NULL
           OR agency IS NULL
           OR TRIM(agency) = ''
           OR closed_date < created_date
    ) THEN
        RAISE EXCEPTION 'DATA QUALITY FAILED';
    END IF;

    RAISE NOTICE 'DATA QUALITY PASS';
END $$;

