WITH filtered_events AS (
    SELECT 
        data_labelling_state,
        media,
        -- Extract the JSON string once here so we don't do it multiple times
        violation_history[-1]->>'modified_at' as last_mod_str,
        event_time_ms
    FROM 
        dashcam_trip.event
    WHERE 
        -- CRITICAL: Use the indexed column to ignore 90% of the table immediately.
        -- Even for 'reviewed' items, they likely happened in the last 180 days.
        event_time_ms >= NOW() - INTERVAL '180 days'
        AND data_labelling_state IN ('2474f6f6-2255-5d95-b528-8d919704cce9', '0736aa8f-74c0-53a9-8a7e-a47b04aad903')
)
SELECT 
    'reviewed' AS incident_check,
    COUNT(DISTINCT media) AS incident_count
FROM 
    filtered_events
WHERE 
    data_labelling_state = '0736aa8f-74c0-53a9-8a7e-a47b04aad903'
    AND (last_mod_str)::timestamp >= NOW() - CAST(:time_window AS INTERVAL)

UNION ALL

SELECT 
    'needs-review' AS incident_check,
    COUNT(*) AS incident_count
FROM 
    filtered_events
WHERE 
    data_labelling_state = '2474f6f6-2255-5d95-b528-8d919704cce9'
    -- Match the user's selected timeframe
    AND event_time_ms >= NOW() - CAST(:time_window AS INTERVAL);