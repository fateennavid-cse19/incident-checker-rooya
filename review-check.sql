SELECT 
    CASE 
        WHEN data_labelling_state = '2474f6f6-2255-5d95-b528-8d919704cce9' THEN 'needs-review'
        WHEN data_labelling_state = '0736aa8f-74c0-53a9-8a7e-a47b04aad903' THEN 'reviewed'
    END AS incident_check,
    COUNT(*) AS incident_count
FROM 
    dashcam_trip.event
WHERE 
    -- Filter for the specific UUIDs
    data_labelling_state IN ('2474f6f6-2255-5d95-b528-8d919704cce9', '0736aa8f-74c0-53a9-8a7e-a47b04aad903')
    -- Filter for the last 24 hours
    AND event_time_ms >= NOW() - CAST(:time_window AS INTERVAL)
GROUP BY 
    incident_check;