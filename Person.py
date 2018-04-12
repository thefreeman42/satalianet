from collections import defaultdict

class Person(object):

    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.project_list = defaultdict(dict)
        self.convo_list = list()

    def __str__(self):
        return "ID: {0}\nName: {1}\nProjects: {2}".format(self.id, self.name, self.project_list.keys())

    def __getitem__(self, item):
        return self.project_list[item]

    def add_new_standup(self, project, interest, h):
        try:
            self.project_list[project][interest] += h
        except:
            self.project_list[project][interest] = h

    def get_convos(self):
        pass