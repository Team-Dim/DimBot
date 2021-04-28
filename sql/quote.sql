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
WHERE quoter = :quoter;

--name: get-uploader-quotes
SELECT ROWID, msg, quoter
FROM Quote
WHERE uid = :uid;

--name: quote-exists$
SELECT ROWID
FROM Quote
WHERE msg = :msg;

--name: get-next-row-id$
SELECT id
FROM QuoteRowID
LIMIT 1;

--name: add-quote-with-rowid!
INSERT INTO Quote(ROWID, msg, quoter, uid, QuoterGroup, Time)
VALUES (:rowid, :msg, :quoter, :uid, :QuoterGroup, :time);

--name: add-quote<!
INSERT INTO Quote
VALUES (:msg, :quoter, :uid, :QuoterGroup, :time);

--name: delete-row-id<!
DELETE FROM QuoteRowID
WHERE id = :id;