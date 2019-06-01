import json


class BotGlob:
    rss_data: dict

    def __init__(self):
        self.readied = False
        with open('rss.json', 'r') as f:
            self.rss_data = json.load(f)
        self.ch = None
