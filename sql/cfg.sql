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

--name: get-snipe-cfg$
SELECT snipe
FROM GuildCfg
WHERE guildID = :guild;

--name: set-snipe-cfg!
UPDATE GuildCfg
SET snipe = :snipe
WHERE guildID = :guild;

--name: remove-guild-cfg!
DELETE FROM GuildCfg
WHERE guildID = :guildID;