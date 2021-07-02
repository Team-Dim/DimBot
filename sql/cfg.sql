--name: add-guild-cfg!
INSERT INTO GuildCfg(guildID)
VALUES (:guildID);

--name: get-mod-role$
SELECT modRole
FROM GuildCfg
WHERE guildID = :guild;

--name: set-mod-role!
UPDATE GuildCfg
SET modRole = :role
WHERE guildID = :guild;

--name: remove-guild-cfg!
DELETE FROM GuildCfg
WHERE guildID = :guildID;