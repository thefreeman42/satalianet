import networkx as nx
import networkx_viewer as nxv
import pandas as pd
import matplotlib.pyplot as plt
from itertools import combinations
from Person import Person
from Conversation import Conversation, Channel, Thread


def build():

    def hubble(ids):

        df_hubble = pd.read_csv('data_hubble.csv').iloc[:, 1:]
        # print(df_hubble.head())

        df_interest_ids = pd.read_csv('interests.csv', header=None, names=["id", "group_name"])
        interest_ids = dict(zip(df_interest_ids["id"], df_interest_ids["group_name"]))
        print(interest_ids)

        people = dict()
        for id, name in ids.items():
            people.update({id: Person(id, name)})

        for ix, row in df_hubble.iterrows():
            if pd.isnull(row["interest_id"]):
                try:
                    interest = int(row["milestone_id"]) + 1000
                except ValueError:
                    interest = 0
            else:
                interest = int(row["interest_id"])
            people[int(row["user_id"])].add_new_standup(row["project"], interest, int(row["calculated_time"]))

        return people

    def slackPriv(ids):

        df_slack_priv = pd.read_csv('data_slack_priv.csv').iloc[:, 1:]
        # print(df_slack_priv.head())

        convos = {}
        for ix, row in df_slack_priv.iterrows():
            if not pd.isnull(row['members']):
                members = row['members'][2:-2].split("', '")
                try:
                    k = tuple([slackids[x] for x in members])
                    try:
                        convos[k] += 1
                    except KeyError:
                        convos[k] = 1
                except KeyError:
                    continue

        print(convos)

    def slackPub(ids):

        pass

    ## Generate ID dictionaries
    df_ids = pd.read_csv('id_list.csv').iloc[:,1:]
    # print(df_ids.head())

    # Hubble IDs are unique
    id2name = dict(zip(df_ids['hubble_id'], df_ids['name']))
    slackids = dict(zip(df_ids['slack_id'], df_ids['hubble_id']))
    slackusers = dict(zip(df_ids['slack_user'], df_ids['hubble_id']))

    people = hubble(id2name)
    convos = slackPriv(slackids)

    def get_graph_from_group(group):

        G = nx.MultiGraph()
        for sgkey, subgroup in group.items():
            sgweights = 0
            sgsize = len(subgroup)
            for k, v in subgroup.items():
                sgweights += v
            for (k1, v1), (k2, v2) in combinations(subgroup.items(), 2):
                if v1 > sgweights/sgsize and v2 > sgweights/sgsize:
                    G.add_edge(k1, k2, weight=(v1+v2)/2, subgroup=sgkey)
        return G

    def subgroup_graph(G, sg):

        S = nx.Graph()
        for n1, n2, d in G.edges(data=True):
            if d['subgroup'] == sg:
                S.add_edge(n1, n2)
        return S


if __name__ == '__main__':
    build()