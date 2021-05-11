--name: get-xp$
SELECT xp
FROM XP
WHERE uid = :uid AND guildID = :guildID;


--name: get-global-xp$
SELECT xp
FROM XP
WHERE uid = :uid AND guildID is null;

--name: user-xp-exists$
SELECT EXISTS(
    SELECT 1
    FROM XP
    WHERE uid = :uid AND guildID = :guildID);


--name: user-global-xp-exists$
SELECT EXISTS(
    SELECT 1
    FROM XP
    WHERE uid = :uid AND guildID is null);

--name: add-xp!
INSERT INTO XP VALUES (:uid, 0, :guildID);

--name: add-global-xp!
INSERT INTO XP VALUES (:uid, 0, null);

--name: update-xp!
UPDATE XP SET xp = :xp WHERE uid = :uid AND guildID = :guildID;

--name: update-global-xp!
UPDATE XP SET xp = :xp WHERE uid = :uid AND guildID is null;

--name: get-xp-ranks
SELECT uid
FROM XP
WHERE guildID = :guildID
ORDER BY xp DESC;

--name: get-global-xp-ranks
SELECT uid
FROM XP
WHERE guildID is null
ORDER BY xp DESC;

--name: get-xp-count$
SELECT COUNT(uid)
FROM XP
WHERE guildID = :guildID;

--name: get-global-xp-count$
SELECT COUNT(uid)
FROM XP
WHERE guildID is null;

--name: get-xp-leaderboard
SELECT uid, xp
FROM XP
WHERE guildID = :guildID
ORDER BY xp DESC
LIMIT 10
OFFSET :offset;

--name: get-global-xp-leaderboard
SELECT uid, xp
FROM XP
WHERE guildID is null
ORDER BY xp DESC
LIMIT 10
OFFSET :offset;

--name: get-xp-graph
SELECT xp
FROM XP
WHERE guildID = :guildID
ORDER BY xp DESC;

--name: get-global-xp-graph
SELECT xp
FROM XP
WHERE guildID is null
ORDER BY xp DESC;