--name: add-who-ping!
INSERT INTO WhoPing
VALUES (:victim, :pinger, :content, :time, :guild);

--name: get-who-ping
SELECT DISTINCT pingerID
FROM WhoPing
WHERE guildID = :guild AND victimID = :victim;

--name: delete-who-ping
DELETE FROM WhoPing
WHERE victimID = :victim;