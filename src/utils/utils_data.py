import pandas as pd
import numpy as np
from datetime import datetime
from utils.utils_date import time_to_minutes_2, time_to_minutes, minute_to_date, minute_to_date2, time_to_minutes_3

def load_data(fichier):
    """Load the data from the Excel file"""

    chantiers_df = pd.read_excel(fichier, sheet_name='Chantiers')
    machines_df = pd.read_excel(fichier, sheet_name='Machines')
    sillons_arrivee_df = pd.read_excel(fichier, sheet_name='Sillons arrivee')
    sillons_depart_df = pd.read_excel(fichier, sheet_name='Sillons depart')
    correspondances_df = pd.read_excel(fichier, sheet_name='Correspondances')
    taches_humaines_df = pd.read_excel(fichier, sheet_name='Taches humaines')
    roulements_agents_df = pd.read_excel(fichier, sheet_name='Roulements agents')
    return chantiers_df, machines_df, sillons_arrivee_df, sillons_depart_df, correspondances_df, taches_humaines_df,roulements_agents_df

def calculate_delta_days(sillons_depart_df,sillons_arrivee_df):
    """Calculate the number of days between the first and last event"""
    max_jour = sillons_depart_df['JDEP'].agg(['max'])['max']
    min_jour = sillons_arrivee_df['JARR'].agg(['min'])['min']

    if type(max_jour) == str:
        jfin = datetime.strptime(max_jour.strip(), "%d/%m/%Y")
    elif type(max_jour) == pd._libs.tslibs.timestamps.Timestamp:
        jfin = max_jour
    if type(min_jour) == str:
        j1 = datetime.strptime(min_jour.strip(), "%d/%m/%Y")
    elif type(min_jour) == pd._libs.tslibs.timestamps.Timestamp:
        j1 = min_jour

    diff = jfin - j1
    jours = diff.days
    first_day = j1.weekday()
    return j1, jours, first_day

def add_time_reference(fichier):
    """Add the time reference to the data"""
    chantiers_df, machines_df, sillons_arrivee_df, sillons_depart_df, correspondances_df,taches_humaines_df,roulements_agents_df = load_data(fichier)
    j1, jours,first_day = calculate_delta_days(sillons_depart_df,sillons_arrivee_df)
    return chantiers_df, machines_df, sillons_arrivee_df, sillons_depart_df, correspondances_df, taches_humaines_df,roulements_agents_df, j1, jours,first_day

def format_trains(machines_df, sillons_arrivee_df, sillons_depart_df, chantiers_df, j1, jours,day_1):
    """Process the trains data and create the list of trains with their arrival and departure times"""
    machines = ['DEB', 'FOR', 'DEG']
    chantiers = chantiers_df['Chantier'].to_list()
    machines_durees = machines_df['Duree '].to_list()
    trains_arr = []
    trains_dep = []
    for x, train in sillons_arrivee_df.iterrows():
        y = ('ARR', train['n°TRAIN'], time_to_minutes_2(train['JARR'], train['HARR'], j1,day_1))
        trains_arr.append(y)
    for x, train in sillons_depart_df.iterrows():
        trains_dep.append(('DEP', train['n°TRAIN'], time_to_minutes_2(train['JDEP'], train['HDEP'], j1,day_1)))

    trains = trains_arr + trains_dep
    minutes = list(range(0, 24 * 60 * (jours+1)))
    minute_slots = list(range(0,24*4*(jours+1)))
    return trains, trains_arr, trains_dep, minutes, machines, machines_durees, minute_slots, chantiers

def format_taches_humaines(taches_humaines_df, roulements_agents_df, jours,day_1, minute_slots):
    """Process the human tasks data and creates a list of the order of the task and the duration"""
    arr_taches = []
    dep_taches = []
    for x, tache in taches_humaines_df.iterrows():
        if tache['Type de train'] == 'ARR':
            arr_taches.append([tache['Ordre'], tache['Durée'], tache['Chantier']])
        elif tache['Type de train'] == 'DEP':
            dep_taches.append([tache['Ordre'], tache['Durée'], tache['Chantier']])
    arr_taches = np.array(arr_taches)
    dep_taches = np.array(dep_taches)

    envelopes_agents = {}
    nombre_agents = []
    for x, roulement in roulements_agents_df.iterrows():
        nombre_agents.append(roulement['Nombre agents'])
        jours_semaine = roulement['Jours de la semaine'].split(';')
        jours_semaine = [int(jour) for jour in jours_semaine] + [(int(jour) + 7) for jour in jours_semaine]
        cycle_horaires = roulement['Cycles horaires'].split(';')
        cycles = []
        for cycle in cycle_horaires:
            cycles.append((cycle.split('-')[0], cycle.split('-')[1]))
        roulement_name = roulement['Roulement']
        envelopes_agents[roulement_name] = []
        possible_days = list(range(day_1, jours+day_1))
        for i in possible_days:
            for j in jours_semaine:
                if i == (j-1):
                    for (start_time,end_time) in cycles:
                        day_of_period = i - day_1
                        start = time_to_minutes_3(day_of_period, start_time,day_1)
                        end = time_to_minutes_3(day_of_period, end_time,day_1)
                        if end < start:
                            end = time_to_minutes_3(day_of_period+1, end_time,day_1)
                        envelopes_agents[roulement_name].append((start, end))

    nombre_agents = np.array(nombre_agents)

    max_agents = {
        'reception': [0] * len(minute_slots),
        'reception_depart': [0] * len(minute_slots),
        'formation': [0] * len(minute_slots),
        'formation_depart': [0] * len(minute_slots),
        'depart': [0] * len(minute_slots)
    }

    for i, minute in enumerate(minute_slots):
        minute = minute*15
        for (start, end) in envelopes_agents['roulement_reception']:
            if start <= minute < end:
                max_agents['reception'][i] += nombre_agents[0]
        for (start, end) in envelopes_agents['roulement_formation']:
            if start <= minute < end:
                max_agents['formation'][i] += nombre_agents[1]
        for (start, end) in envelopes_agents['roulement_depart']:
            if start <= minute < end:
                max_agents['depart'][i] += nombre_agents[2]
        for (start, end) in envelopes_agents['roulement_reception_depart']:
            if start <= minute < end:
                max_agents['depart'][i] += nombre_agents[3]
        for (start3, end3) in envelopes_agents['roulement_formation_depart']:
            if start <= minute < end:
                max_agents['depart'][i] += nombre_agents[4]

        
    arr_taches_dict = {}
    dep_taches_dict = {}
    for x, tache in taches_humaines_df.iterrows():
        if tache['Type de train'] == 'ARR':
            if tache['Ordre'] not in arr_taches_dict:
                arr_taches_dict[tache['Ordre']] = []
            arr_taches_dict[tache['Ordre']].append([tache['Durée'], tache['Chantier'], tache['Type de tache humaine']])
        elif tache['Type de train'] == 'DEP':
            if tache['Ordre'] not in dep_taches_dict:
                dep_taches_dict[tache['Ordre']] = []
            dep_taches_dict[tache['Ordre']].append([tache['Durée'], tache['Chantier'], tache['Type de tache humaine']])


    return arr_taches, dep_taches, envelopes_agents, nombre_agents, max_agents, arr_taches_dict, dep_taches_dict

def unavailable_machines(machines_df, jours,day_1):
    """Process the unavailable periods for each machine"""
    unavailable_periods = {}
    for _, row in machines_df.iterrows():
        machine = row['Machine']
        unavailable_times = row['Indisponibilites']
        
        if unavailable_times != 0:
            periods = unavailable_times.split(';')
            unavailable_periods[machine] = []
            for period in periods:
                period = period.strip('()')
                day_of_week, time_str = period.split(',')
                start_time = time_to_minutes(day_of_week, time_str.split('-')[0], jours,day_1)
                end_time = time_to_minutes(day_of_week, time_str.split('-')[1], jours,day_1)
                unavailable_periods[machine].append((start_time, end_time))


    start_times =[]
    for machine, periods in unavailable_periods.items():
        for (start_time, end_time) in periods:
            start_times.append((start_time[0],machine))
            if start_time[1] != 0:
                start_times.append((start_time[1],machine))

    return unavailable_periods, start_times

def unavailable_chantiers(chantiers_df, jours,day_1):
    """Process the unavailable periods for each machine"""
    unavailable_periods_chantiers = {}
    for _, row in chantiers_df.iterrows():
        chantier = row['Chantier']
        unavailable_times = row['Indisponibilites']
        
        if unavailable_times != 0:
            periods = unavailable_times.split(';')
            unavailable_periods_chantiers[chantier] = []
            for period in periods:
                period = period.strip('()')
                day_of_week, time_str = period.split(',')
                start_time = time_to_minutes(day_of_week, time_str.split('-')[0], jours,day_1)
                end_time = time_to_minutes(day_of_week, time_str.split('-')[1], jours,day_1)
                unavailable_periods_chantiers[chantier].append((start_time, end_time))


    start_times =[]
    for chantier, periods in unavailable_periods_chantiers.items():
        for (start_time, end_time) in periods:
            start_times.append((start_time[0],chantier))
            if start_time[1] != 0:
                start_times.append((start_time[1],chantier))

    return unavailable_periods_chantiers, start_times

def correspondance_for_depart(trains_dep, trains_arr, correspondances_df, j1):
    """Find the required arrived trains for each departed train"""
    trains_requis_dict = {}
    for train in trains_dep:
        tous_trains = []
        for _, row in correspondances_df.iterrows():
            if row['n°Train depart'] == train[1] and row['Jour depart'] == minute_to_date(train[2], j1):
                for train_arr in trains_arr:
                    if row['n°Train arrivee'] == train_arr[1] and row['Jour arrivee'] == minute_to_date(train_arr[2], j1):
                        if train_arr not in tous_trains:
                            tous_trains.append(train_arr)
        trains_requis_dict[train] = tous_trains
    return trains_requis_dict

def find_max_voies(chantiers_df):
    """Find the maximum number of voies used in the data"""
    max_voies = chantiers_df['Nombre de voies'].to_numpy()
    return max_voies
