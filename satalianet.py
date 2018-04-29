import networkx as nx
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from itertools import permutations
from collections import defaultdict
from Person import Person
from Project import Project
from Conversation import Conversation, Channel
from datetime import datetime, timedelta


def build(interval=28, until=None):

    def hubble(interval, until):

        df_hubble = pd.read_csv('data_hubble.csv').iloc[:, 1:]
        df_hubble['date'] = pd.to_datetime(df_hubble['date'], format='%Y-%m-%d')
        df_hubble = df_hubble[(until - timedelta(interval) <= df_hubble['date']) &
                                      (df_hubble['date'] <= until)]
        # print(df_hubble.head())

        projects = dict()

        print('Building projects dict...')
        for ix, row in df_hubble.iterrows():
            pid = int(row['project'])
            try:
                projects[pid].add_standup(row['id'], row['interest'], row['time'])
            except KeyError:
                projects[pid] = Project()
                projects[pid].add_standup(row['id'], row['interest'], row['time'])

        return projects

    def slackPriv(ids, userids, interval, until):

        df_slack_priv = pd.read_csv('data_slack_priv.csv').iloc[:, 1:]
        df_slack_priv["date"] = pd.to_datetime(df_slack_priv["date"], format='%Y-%m-%d')
        df_slack_priv = df_slack_priv[(until - timedelta(interval) <= df_slack_priv["date"]) &
                                      (df_slack_priv["date"] <= until)]
        # print(df_slack_priv.head())

        convos = dict()

        print('Building convos dict...')
        for ix, row in df_slack_priv.iterrows():
            if not pd.isnull(row['timestamp']) and not pd.isnull(row['members']):
                if until - timedelta(interval) <= row["date"].to_pydatetime().date() <= until:
                    members = row['members'][2:-2].split("', '")
                    if len(members) > 1:
                        try:
                            convid = hash(tuple(sorted([ids[x] for x in members])))
                            if not pd.isnull(row['mentions']):
                                mentions = [userids[x] for x in row['mentions'].split(', ')]
                            else:
                                mentions = None
                        except KeyError:
                            continue
                        try:
                            convos[convid].add_new_msg(int(row['hubble_id']), mentions)
                        except KeyError:
                            convos[convid] = Conversation()
                            convos[convid].add_new_msg(int(row['hubble_id']), mentions)


        return convos

    def slackPub(ids, userids, interval, until):

        df_slack_pub = pd.read_csv('data_slack_pub.csv').iloc[:, 1:]
        df_slack_pub["date"] = pd.to_datetime(df_slack_pub["date"], format='%Y-%m-%d')
        df_slack_pub = df_slack_pub[(until - timedelta(interval) <= df_slack_pub["date"]) &
                                      (df_slack_pub["date"] <= until)]
        # print(df_slack_pub.head())

        channels = dict()

        print('Building channels dict...')
        for ix, row in df_slack_pub.iterrows():
            if until - timedelta(interval) <= row["date"].to_pydatetime().date() <= until:
                try:
                    if not pd.isnull(row['mentions']):
                        mentions = [userids[x] for x in row['mentions'].split(', ')]
                    else:
                        mentions = None
                except KeyError:
                    mentions = None
                try:
                    if not pd.isnull(row['parent_user_id']):
                        parent = int(ids[row['parent_user_id']])
                    else:
                        parent = None
                except KeyError:
                    parent = None
                try:
                    channels[row['channel']].add_new_msg(int(row['hubble_id']), mentions, parent)
                except KeyError:
                    channels[row['channel']] = Channel()
                    channels[row['channel']].add_new_msg(int(row['hubble_id']), mentions, parent)

        return channels

    def merge_by_people(meta, projects, convos, channels):

        people = dict()

        print("Merging into people dict...")
        for ix, row in meta.iterrows():
            people[row['hubble_id']] = Person(row['name'], row['relationship'], row['sat_score'])

        for pid, project in projects.items():
            for id, h in project.data_by_person.items():
                people[id].add_project(pid, h)
            for id1, id2 in permutations(project.data_by_person, 2):
                people[id1].incr_hubble(id2, pid)

        for cid, convo in convos.items():
            for (id1, m1), (id2, m2) in permutations(convo.msgcount.items(), 2):
                people[id1].incr_slack(id2, m1)
        for chid, channel in channels.items():
            for id1, id2 in channel.mentions:
                people[id1].incr_slack(id2)
            for id1, id2 in channel.replies:
                people[id1].incr_slack(id2)

        for id, person in people.items():
            people[id].calc_weights()

        return dict((id, p) for id, p in people.items() if len(p.connections.values()) > 0)

    ## Generate ID dictionaries
    metadata = pd.read_csv('metadata.csv').iloc[:,1:]
    # print(metadata.head())

    # Hubble IDs are unique -- SHOULD MERGE IDS IN R INSTEAD OF HERE
    slackids = dict(zip(metadata['slack_id'], metadata['hubble_id']))
    slackusers = dict(zip(metadata['slack_user'], metadata['hubble_id']))

    if until is None: enddate = datetime.now().date()
    else:
        try:
            enddate = datetime.strptime(until, '%Y-%m-%d').date()
        except:
            raise ValueError("Interval end date must be in format YYYY-MM-DD")

    projects = hubble(interval, enddate)
    # print('Number of projects: {0}'.format(len(projects)))
    convos = slackPriv(slackids, slackusers, interval, enddate)
    # print('Number of private convos: {0}'.format(len(convos)))
    channels = slackPub(slackids, slackusers, interval, enddate)
    # print('Number of public channels: {0}'.format(len(channels)))

    people = merge_by_people(metadata, projects, convos, channels)

    return projects, people


def generate(people, threshold=0.5, show=False):

    X = nx.DiGraph()

    print("Generating network...")
    for id, person in people.items():
        for id2, w in person.connections.items():
            X.add_edge(id, id2, weight=w)
    rel_attributes = dict((id, p.relation) for id, p in people.items())
    sat_attributes = dict((id, p.satisfaction) for id, p in people.items())
    nx.set_node_attributes(X, rel_attributes, name='rel')
    nx.set_node_attributes(X, sat_attributes, name='sat')

    filtered_edges = [(n1, n2) for n1, n2, d in X.edges(data=True) if d['weight'] >= threshold]
    node_attr_dict_rel = nx.get_node_attributes(X, 'rel')
    node_attr_dict_sat = nx.get_node_attributes(X, 'sat')
    edge_attr_dict = nx.get_edge_attributes(X, 'weight')
    finalGraph = nx.DiGraph(filtered_edges)
    nx.set_node_attributes(finalGraph, node_attr_dict_rel, name='rel')
    nx.set_node_attributes(finalGraph, node_attr_dict_sat, name='sat')
    nx.set_edge_attributes(finalGraph, edge_attr_dict, name='weight')

    if show:
        pos = nx.spring_layout(finalGraph)
        # nx.draw_networkx_nodes(finalGraph, pos, node_size=100, cmap=plt.get_cmap('plasma'),
        #                        node_color=[d['sat'] for n, d in finalGraph.nodes(data=True)])
        nx.draw_networkx_nodes(finalGraph, pos, node_size=100, node_color='orange')
        nx.draw_networkx_edges(finalGraph, pos, alpha=0.5,
                               edge_color=[d['weight'] for n1, n2, d in finalGraph.edges(data=True)])
        nx.draw_networkx_labels(finalGraph, pos, font_size=10)
        plt.show()

    print("All good!")

    return finalGraph


def analyse(G, projects, people, show=None):

    output = projects

    G_undir = G.to_undirected()
    for n1, n2 in G_undir.edges():
        G_undir[n1][n2]['weight'] = 0.5 * (G[n1][n2]['weight'] + G[n2][n1]['weight'])

    dc = nx.degree_centrality(G_undir)
    nx.set_node_attributes(G, dc, name='degree')
    cc = nx.closeness_centrality(G_undir)
    nx.set_node_attributes(G, cc, name='closeness')
    bc1 = nx.betweenness_centrality(G_undir)
    nx.set_node_attributes(G, bc1, name='betweenness')
    bc2 = nx.current_flow_betweenness_centrality(G_undir)
    nx.set_node_attributes(G, bc2, name='flow_betweenness')

    for id in G.nodes():
        people[id].centrality.update({'degree': dc[id], 'closeness': cc[id], 'betweenness': bc1[id],
                                      'flow_betweenness': bc2[id]})

    if show == 'bc':
        fig = plt.figure(figsize=(20,15))
        pos = nx.spring_layout(G)
        nx.draw_networkx_nodes(G, pos, node_size=200, cmap=plt.get_cmap('autumn'),
                               node_color=[d['flow_betweenness'] for n, d in G.nodes(data=True)])
        nx.draw_networkx_edges(G, pos, alpha=0.5, cmap=plt.get_cmap('inferno'),
                               edge_color=[d['weight'] for n1, n2, d in G.edges(data=True)])
        nx.draw_networkx_labels(G, pos, font_size=14)
        plt.show()

    for pid, project in projects.items():

        G_project = G.subgraph(project.idlist())
        if len(G_project.nodes()) == 0:
            output[pid].metrics['evc'] = np.NaN
        else:
            evc = nx.eigenvector_centrality(G_project, max_iter=2000, weight='weight')
            output[pid].metrics['evc'] = np.mean([v for k, v in evc.items()])

            pnodes = G_project.nodes()
            other_nodes = [n for n in G.nodes() if n not in pnodes]

            neighbors = list()
            for n in pnodes:
                for m in nx.neighbors(G, n):
                    if m not in pnodes and m not in neighbors:
                        neighbors.append(m)
            output[pid].metrics['gdc'] = len(neighbors) / len(other_nodes)

            shortest_paths = list()
            for n in other_nodes:
                local_paths = list()
                for m in pnodes:
                    local_paths.append(nx.shortest_path_length(G, n, m))
                shortest_paths.append(max(local_paths))
            output[pid].metrics['gcc'] = len(other_nodes) / sum(shortest_paths)

    people_dict = dict()
    for id, person in people.items():
        people_dict.update({id: person.to_dict()})
    people_data = pd.DataFrame(people_dict).T

    project_dict = dict()
    for id, project in projects.items():
        project_dict.update({id: project.to_dict()})
    project_data = pd.DataFrame(project_dict).T

    return project_data, people_data


if __name__ == '__main__':
    projects, people = build(28, '2018-04-04')
    finalGraph = generate(people, threshold=0, show=False)
    df_project, df_people = analyse(finalGraph, projects, people, show='bc')
    df_people.to_csv('output_people.csv')
    df_project.to_csv('output_projects.csv')