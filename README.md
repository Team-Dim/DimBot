# DimBot
### dimsecret.py
In order to run the bot, you have to provide some tokens for it to work.
They should be stored inside `dimsecret.py` in the root directory.

The following are the variables that should be in the file:

| Name              | Type | Description                                                               |
|-------------------|------|---------------------------------------------------------------------------|
| discord           | str  | Discord bot token. Obtained from Discord Developer Portal ALWAYS REQUIRED |
| youtube           | str  | YouTube API token Required for YouTube subscription processing            |
| debug             | bool | Whether the bot is in debug mode. ALWAYS REQUIRED                         |
| bruck_instance_id | str  | An Amazon Web Services(AWS) EC2 Instance ID. Required for Verstapen       |
| aws_access_key    | str  | Access Key from AWS IAM User security credentials Required for Verstapen  |
| aws_secret_key    | str  | Secret key from AWS IAM User security credentials Required for Verstapen  |