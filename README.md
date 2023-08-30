# DimBot
Minimum Python version: `3.6` (f-strings are used, but I haven't tested whether 3.6-3.7 still works.)

Recommended Python version: `3.11.x`

For `Albon` to work, you need root/sudo in Linux as it uses port 80 for HTTP server port
### dimsecret.py
In order to run the bot, you have to provide some tokens for it to work.
They should be stored inside `dimsecret.py` in the project root directory.

The following are the variables that should be in the file:

| Name           | Type | Description                                                                  |
|----------------|------|------------------------------------------------------------------------------|
| discord        | str  | Discord bot token. Obtained from Discord Developer Portal<br>ALWAYS REQUIRED |
| youtube        | str  | YouTube API token<br>Required for YouTube subscription processing            |
| debug          | bool | Whether the bot is in debug mode.<br>ALWAYS REQUIRED                         |
| digital_ocean  | str  | Token from DigitalOcean<br>Required for Vireg                                |
| openai.api_key | str  | Token for OpenAI service.<br>Required for Nene                               |
| coc            | str  | Token for Clash of Clans.<br>Required for Hyperstellar                       |
