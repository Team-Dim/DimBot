--name: get-activity^
SELECT *
FROM Activity
WHERE ROWID = (
    SELECT ROWID FROM Activity ORDER BY random() LIMIT 1
    )