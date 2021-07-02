--name: get-tag-content^
SELECT content
FROM Tag
WHERE name = :name AND guildID = :guildID;

--name: get-tags-name
SELECT name
FROM Tag
WHERE guildID = :guildID
ORDER BY name;

--name: tag-exists$
SELECT EXISTS(
    SELECT 1
    FROM Tag
    WHERE (name = :name OR content = :content) AND guildID = :guildID
);

--name: add_tag!
INSERT INTO Tag
VALUES (:name, :content, :guildID);

--name: tag-name-exists$
SELECT EXISTS(
    SELECT 1
    FROM Tag
    WHERE name = :name AND guildID = :guildID
);

--name: delete-tag!
DELETE FROM Tag
WHERE name = :name AND guildID = :guildID;

--name: delete-guild-tags!
DELETE FROM Tag
WHERE guildID = :guildID;