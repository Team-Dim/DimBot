--name: get-quote^
SELECT *
FROM Quote
WHERE ROWID = :id;

--name: get-random-id^
SELECT ROWID
FROM Quote
ORDER BY random()
LIMIT 1;

--name: get-quotes-count$
SELECT COUNT(ROWID)
FROM Quote;

--name: get-quoter-quotes
SELECT ROWID, *
FROM Quote
WHERE (:quoter is '' OR quoter = :quoter)
  AND (:QuoterGroup is null OR QuoterGroup = :QuoterGroup);

--name: get-uploader-quotes
SELECT ROWID, *
FROM Quote
WHERE uid = :uid;

--name: get-keyword-quotes
SELECT ROWID, *
FROM Quote
WHERE msg LIKE :kw;

--name: quote-msg-exists$
SELECT ROWID
FROM Quote
WHERE msg = :msg;

--name: quote-id-exists$
SELECT EXISTS(
    SELECT 1
    FROM Quote
    WHERE ROWID = :id
           );

--name: get-next-row-id$
SELECT id
FROM QuoteRowID
LIMIT 1;

--name: add-quote-with-rowid<!
INSERT INTO Quote(ROWID, msg, quoter, uid, QuoterGroup, Time)
VALUES (:rowid, :msg, :quoter, :uid, :QuoterGroup, :time);

--name: add-quote<!
INSERT INTO Quote
VALUES (:msg, :quoter, :uid, :QuoterGroup, :time);

--name: delete-rowid<!
DELETE FROM QuoteRowID
WHERE id = :id;

--name: delete-quote!
DELETE FROM Quote
WHERE ROWID = :id;

--name: add-next-rowid!
INSERT INTO QuoteRowID
VALUES (:id);

--name: update-quote!
UPDATE Quote
SET msg = :msg, quoter = :quoter, QuoterGroup = :QuoterGroup
WHERE ROWID = :id;

--name: get-previous-quote^
SELECT ROWID, *
FROM Quote
WHERE ROWID < :id
ORDER BY ROWID DESC
LIMIT 1;

--name: get-next-quote^
SELECT ROWID, *
FROM Quote
WHERE ROWID > :id
ORDER BY ROWID
LIMIT 1