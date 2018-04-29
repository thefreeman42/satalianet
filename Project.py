from collections import defaultdict

class Project(object):

    def __init__(self, name=''):
        self.name = name
        self.data_by_group = defaultdict(dict)
        self.data_by_person = dict()
        self.metrics = {'evc': 0, 'gdc': 0, 'gcc': 0}

    def idlist(self):
        return list(self.data_by_person)

    def __getitem__(self, item):
        if type(item) is int:
            return self.data_by_person[item]
        else:
            return self.data_by_group[item]

    def add_standup(self, user, ig, h):
        try:
            self.data_by_group[int(ig)][int(user)] += int(h)
        except KeyError:
            self.data_by_group[int(ig)][int(user)] = int(h)
        try:
            self.data_by_person[int(user)] += int(h)
        except KeyError:
            self.data_by_person[int(user)] = int(h)

    def to_dict(self):
        return {'internal': self.metrics['evc'],
                'ext_degree': self.metrics['gdc'],
                'ext_closeness': self.metrics['gcc'],
                'n_people': len(self.idlist()),
                'total_worktime': sum(self.data_by_person.values())}
