--name: get-bbm-roles
SELECT *
FROM BbmRole;

--name: get-subscribed-addons
SELECT addonID
FROM BbmAddon
WHERE bbmChID = :id;

--name: get-bbm-addons
SELECT title
FROM BbmData
WHERE addonID = :id;

--name: update-bbm-addon
UPDATE BbmData
SET title = :new
WHERE title = :old;