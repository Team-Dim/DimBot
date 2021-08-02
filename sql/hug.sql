--name: get-hug^
SELECT streak, hugged
FROM HugStreak
WHERE hugger = :hugger AND huggie = :huggie;

--name: add-hug!
INSERT INTO HugStreak (hugger, huggie, hugged)
VALUES (:hugger, :huggie, :hugged);

--name: update-hug!
UPDATE HugStreak
SET streak = :streak, hugged = :hugged
WHERE hugger = :hugger AND huggie = :huggie;