--name: is-guild-banned$
SELECT EXISTS(
    SELECT 1
    FROM Banned
    WHERE ID = :id AND type = 0
);

--name: ban-guild!
INSERT INTO Banned
VALUES (:id, 0);