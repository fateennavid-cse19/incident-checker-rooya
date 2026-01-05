WITH filtered_events AS (
    SELECT 
        data_labelling_state,
        media,
        -- Extract the JSON string once here so we don't do it multiple times
        violation_history[-1]->>'modified_at' as last_mod_str,
        violation_history[-1]->>'modified_by' as raw_annotator,
        event_time_ms
    FROM 
        dashcam_trip.event
    WHERE 
        event_time_ms >= NOW() - INTERVAL '180 days'
        AND data_labelling_state IN ('2474f6f6-2255-5d95-b528-8d919704cce9', '0736aa8f-74c0-53a9-8a7e-a47b04aad903')
)
SELECT
    'summary' AS report_type,
    'reviewed' AS label,
    NULL AS annotator,
    COUNT(DISTINCT media) AS count
FROM 
    filtered_events
WHERE 
    data_labelling_state = '0736aa8f-74c0-53a9-8a7e-a47b04aad903'
    AND (last_mod_str)::timestamp >= NOW() - CAST(:time_window AS INTERVAL)

UNION ALL

SELECT
    'summary' AS report_type,
    'needs-review' AS label,
    NULL AS annotator,
    COUNT(*) AS count
FROM 
    filtered_events
WHERE 
    data_labelling_state = '2474f6f6-2255-5d95-b528-8d919704cce9'
    AND event_time_ms >= NOW() - CAST(:time_window AS INTERVAL)

UNION ALL

SELECT 
    'leaderboard' AS report_type,
    'reviewed' AS label,
    SPLIT_PART(raw_annotator, '@', 1) AS annotator,
    COUNT(DISTINCT media) AS count
FROM 
    filtered_events
WHERE 
    data_labelling_state = '0736aa8f-74c0-53a9-8a7e-a47b04aad903'
    AND (last_mod_str)::timestamp >= NOW() - CAST(:time_window AS INTERVAL)
    AND SPLIT_PART(raw_annotator, '@', 1) NOT IN ('dashcam-post-driving-event', 'anwar','tabasher')
GROUP BY 
    annotator;