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
WHERE quoter = :quoter