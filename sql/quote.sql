--name: get-quote^
SELECT *
FROM Quote
WHERE ROWID = :id;

--name: get-random-quote^
SELECT *, ROWID
FROM Quote
WHERE ROWID = (
    SELECT ROWID FROM Quote ORDER BY random() LIMIT 1
    );

--name: get-quotes-count$
SELECT COUNT(ROWID)
FROM Quote;

--name: get-quoter-quotes
SELECT ROWID, msg
FROM Quote
WHERE (:quoter is '' OR quoter = :quoter)
  AND (:QuoterGroup is null OR QuoterGroup = :QuoterGroup);

--name: get-uploader-quotes
SELECT ROWID, msg, quoter
FROM Quote
WHERE uid = :uid;

--name: get-keyword-quotes
SELECT *, ROWID
FROM Quote
WHERE msg LIKE '%' + :kw + '%';

--name: quote-exists$
SELECT ROWID
FROM Quote
WHERE msg = :msg;

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