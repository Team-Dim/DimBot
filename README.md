# DimBot
Minimum Python version: `3.6` (f-strings are used, but I haven't tested whether 3.6 actually works.)

Recommended Python version: `3.9.2+` (.2 matters)

For `Albon` to work, you need root/sudo in Linux as it uses port 80 for HTTP server port
### dimsecret.py
In order to run the bot, you have to provide some tokens for it to work.
They should be stored inside `dimsecret.py` in the root directory.

The following are the variables that should be in the file:

| Name              | Type | Description                                                               |
|-------------------|------|---------------------------------------------------------------------------|
| discord           | str  | Discord bot token. Obtained from Discord Developer Portal<br>ALWAYS REQUIRED |
| youtube           | str  | YouTube API token<br>Required for YouTube subscription processing            |
| debug             | bool | Whether the bot is in debug mode.<br>ALWAYS REQUIRED                         |
| aws_access_key    | str  | Access Key from AWS IAM User security credentials<br>Required for Vireg  |
| aws_secret_key    | str  | Secret key from AWS IAM User security credentials<br>Required for Vireg  |

# Codenames
`Barbados` is the codename given to the discord.py implementation of DimBot.
|Name|Represents|English|
|------|-----------|---------|
|뾆|0.9|Bbwaelp|
|ζ|0.8|Zeta|