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

--name: get-lockdown
SELECT roleID, perm
FROM GuildLockdown
WHERE guildID = :guild;

--name: remove-lockdown!
DELETE FROM GuildLockdown
WHERE guildID = :guild;

--name: add-lockdown!
INSERT INTO GuildLockdown
VALUES (:guild, :role, :perm);

--name: get-joinable-role^
SELECT requiredRoleID, checkHighestRole
FROM RoleJoinable
WHERE roleID = :role;

--name: add-joinable-role!
INSERT INTO RoleJoinable
VALUES (:role, :required, :checkHighest);

--name: update-joinable-role!
UPDATE RoleJoinable
SET requiredRoleID = :required, checkHighestRole = :checkHighest
WHERE roleID = :role;

--name: remove-joinable-role!
DELETE FROM RoleJoinable
WHERE roleID = :role;