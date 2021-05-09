--name: get-rss-data
SELECT *
FROM RssData;

--name: get-rss-subscriptions
SELECT rssChID, footer, encode
FROM RssSub
WHERE url = :url;

--name: update-rss-data!
UPDATE RssData
SET newstitle = :title, time = :time
WHERE ROWID = :id;

--name: is-ch-already-sub$
SELECT EXISTS(
    SELECT 1
    FROM RssSub
    WHERE rssChID = :ch AND url = :url
           );

--name: is-url-in-rss-data$
SELECT EXISTS(
    SELECT 1
    FROM RssData
    WHERE url = :url
           );

--name: add-rss-url!
INSERT INTO RssData(url, newstitle)
VALUES (:url, '');

--name: add-rss-sub!
INSERT INTO RssSub
VALUES(:ch, :url, :footer, :encode);

--name: unsub-rss
DELETE FROM RssSub
WHERE rssChID = :ch AND url = :url;

--name: rss-url-in-use$
SELECT EXISTS(
    SELECT 1
    FROM RssSub
    WHERE url = :url
           );

--name: delete-rss-url!
DELETE FROM RssData
WHERE url = :url;