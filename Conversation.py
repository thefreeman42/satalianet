from ast import literal_eval

class Conversation(object):

    def __init__(self):
        self.msgcount = dict()
        self.mentions = list()

    def idlist(self):
        return list(self.msgcount)

    def add_new_msg(self, user, mentions):
        try:
            self.msgcount[user] += 1
        except KeyError:
            self.msgcount[user] = 1
        if mentions is not None:
            for m in mentions:
                if user != m:
                    self.mentions.append((user, m))

    def total(self):
        return sum([v for k, v in self.msgcount.items()])

    def __str__(self):
        return '{0}\n{1}'.format(self.msgcount, self.mentions)


class Channel(Conversation):

    def __init__(self, type=None):
        super().__init__()
        self.type = type
        self.replies = list()

    def add_new_msg(self, user, mentions, parent):
        super().add_new_msg(user, mentions)
        if parent is not None and user != parent:
            self.replies.append((user, parent))