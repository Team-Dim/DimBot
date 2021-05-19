--name: add-who-ping!
INSERT INTO WhoPing
VALUES (:victim, :pinger, :content, :time, :guild);

--name: get-who-ping
SELECT ROWID, pingerID, content, time
FROM WhoPing
WHERE guildID = :guild AND victimID = :victim;

--name: get-all-who-ping
SELECT ROWID, pingerID, content, time, guildID
FROM WhoPing
WHERE victimID = :victim;

--name: clear-all-who-ping!
DELETE FROM WhoPing
WHERE victimID = :victim;

--name: clear-who-ping!
DELETE FROM WhoPing
WHERE victimID = :victim AND guildID = :guild;

--name: delete-who-ping!
DELETE FROM WhoPing
WHERE ROWID = :id;

--name: daily-clean-who-ping!
DELETE FROM WhoPing
WHERE time < :time;