--name: get-bbm-roles
SELECT *
FROM BbmRole;

--name: get-subscribed-addons
SELECT *
FROM BbmAddon;

--name: get-bbm-addons
SELECT title
FROM BbmData
WHERE addonID = :id;

--name: update-bbm-addon!
UPDATE BbmData
SET title = :new
WHERE title = :old;

--name: is-addon-subscribed$
SELECT EXISTS(
    SELECT 1
    FROM BbmAddon
    WHERE bbmChID = :ch AND addonID = :addon
           );

--name: has-bbm-role$
SELECT EXISTS(
    SELECT 1
    FROM BbmRole
    WHERE bbmChID = :ch
           );

--name: add-bbm-role!
INSERT INTO BbmRole
VALUES (:ch, :role);

--name: add-bbm-addon!
INSERT INTO BbmAddon
VALUES (:ch, :addon);

--name: delete-bbm-addon
DELETE FROM BbmAddon
WHERE bbmChID = :ch AND addonID = :addon;

--name: bbm-addon-subscribed$
SELECT EXISTS(
    SELECT 1
    FROM BbmAddon
    WHERE bbmChID = :ch
           );

--name: delete-bbm-role!
DELETE FROM BbmRole
WHERE bbmChID = :id;

--name: update-bbm-role!
UPDATE BbmRole
SET roleID = :role
WHERE bbmChID = :ch;