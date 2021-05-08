--name: get-rss-data
SELECT *
FROM RssData;

--name: get-rss-subscriptions
SELECT rssChID, footer
FROM RssSub
WHERE url = :url;

--name: update-rss-data
UPDATE RssData
SET newstitle = :title, time = :time
WHERE ROWID = :id;