class Conversation(object):

    def __init__(self):
        self.msgcount = dict()
        self.mentions = list()

    def idlist(self):
        return list(self.msgcount)

    def add_new_msg(self):
        pass


class Channel(Conversation):

    def __init__(self, name, type="none"):
        super().__init__()
        self.name = name
        self.type = type
        self.threads = list()

    def add_new_msg(self):
        pass

class Thread(Conversation):

    def __init__(self, p):
        super().__init__()
        self.parent = p
