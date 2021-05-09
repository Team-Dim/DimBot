--name: get-yt-data
SELECT *
FROM YtData;

--name: get-yt-subs
SELECT ytChID
FROM YtSub
WHERE channelID = :id;

--name: update-yt-data!
UPDATE YtData
SET videoID = :video
WHERE channelID = :ch;

--name: has-yt-sub$
SELECT EXISTS(
    SELECT 1
    FROM YtSub
    WHERE ytChID = :ch AND channelID = :yt
           );

--name: yt-channel-exists$
SELECT EXISTS(
    SELECT 1
    FROM YtData
    WHERE channelID = :yt
           );

--name: add-yt-channel!
INSERT INTO YtData
VALUES (:yt, :yt);

--name: add-yt-sub!
INSERT INTO YtSub
VALUES (:ch, :yt);

--name: delete-yt-sub
DELETE FROM YtSub
WHERE ytChID = :ch AND channelID = :yt;

--name: yt-sub-exists$
SELECT EXISTS(
    SELECT 1
    FROM YtSub
    WHERE channelID = :yt
           );

--name: delete-yt-channel!
DELETE FROM YtData
WHERE channelID = :yt;