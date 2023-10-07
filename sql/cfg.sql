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

--name: set-anti-afk!
UPDATE GuildCfg
SET antiVCAFK = :antiafk
WHERE guildID = :guild;

--name: remove-guild-cfg!
DELETE FROM GuildCfg
WHERE guildID = :guildID;

--name: get-anti-invisible$
SELECT antiInvisible
FROM GuildCfg
WHERE guildID = :guild;

--name: set-anti-invisible!
UPDATE GuildCfg
SET antiInvisible = :invisible
WHERE guildID = :guild;

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

--name: add-role-ping!
INSERT INTO RolePing
VALUES (:role);

--name: remove-role-ping!
DELETE FROM RolePing
WHERE roleID = :role;

/*
 * User cfg
 */

--name: set-user-lang!
INSERT INTO UserCfg (ID, LocalePref)
VALUES (:user, :locale)
ON CONFLICT (ID) DO UPDATE SET LocalePref = :locale;