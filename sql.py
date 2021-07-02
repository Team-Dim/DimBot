import missile


class Quote:

    def __init__(self, *args):
        self.id = args[0]
        self.msg = args[1]
        self.quoter = args[2]
        self.uid = args[3]
        self.quoter_group = args[4]
        self.time = args[5]

    def embed(self):
        emb = missile.Embed(description=self.msg)
        emb.add_field('Quote ID', self.id)
        if self.quoter:
            emb.add_field('Quoter', self.quoter)
        if self.quoter_group:
            emb.add_field('Quoter Group', self.quoter_group)
        emb.add_field('Uploader', f'<@{self.uid}>')
        if self.time:
            emb.set_footer(text=f'Uploaded at {self.time.split(".")[0]}')
        return emb
