--name: get-guild-prefix$
SELECT prefix
FROM GuildCfg
WHERE guildID = :guildID;

--name: update-guild-prefix!
UPDATE GuildCfg
SET prefix = :prefix
WHERE guildID = :guildID;