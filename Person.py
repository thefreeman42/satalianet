class Person(object):

    def __init__(self, name, rel, sat=0):

        self.name = name
        self.relation = rel
        self.projects = dict()
        self.data = {'hubble': dict(), 'slack': dict()}
        self.connections = dict()
        self.centrality = dict()
        self.satisfaction = sat

    # def __str__(self):
    #     return "ID: {0}\nName: {1}\nProjects: {2}".format(self.id, self.name, self.project_list.keys())

    def add_project(self, p, h):
        self.projects.update({p: h})

    def total_worktime(self):
        return sum(self.projects.values())

    def incr_hubble(self, user, p):

        try:
            self.data['hubble'][user] += self.projects[p]
        except KeyError:
            self.data['hubble'][user] = self.projects[p]

    def incr_slack(self, user, m=1):

        try:
            self.data['slack'][user] += m
        except KeyError:
            self.data['slack'][user] = m

    def calc_weights(self, hubble_weight=0.5):

        h_total = self.total_worktime()
        m_total = sum(self.data['slack'].values())

        for id, h in self.data['hubble'].items():
            self.connections[id] = h / h_total * hubble_weight
        for id, m in self.data['slack'].items():
            try:
                self.connections[id] += m / m_total * (1-hubble_weight)
            except KeyError:
                self.connections[id] = m / m_total * (1-hubble_weight)

    def to_dict(self):
        return {'name': self.name,
                'degree': self.centrality['degree'],
                'closeness': self.centrality['closeness'],
                'betweenness': self.centrality['betweenness'],
                'flow_betweenness': self.centrality['flow_betweenness'],
                'relation': self.relation,
                'n_projects': len(self.projects),
                'total_worktime': self.total_worktime(),
                'satisfaction': self.satisfaction}