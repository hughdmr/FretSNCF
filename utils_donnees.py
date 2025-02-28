import pandas as pd
from datetime import datetime
from utils_horaires import time_to_minutes_2, time_to_minutes, minute_to_jour, minute_to_jour2



def charger_donnees(fichier):
    chantiers_df = pd.read_excel(fichier, sheet_name='Chantiers')
    machines_df = pd.read_excel(fichier, sheet_name='Machines')
    sillons_arrivee_df = pd.read_excel(fichier, sheet_name='Sillons arrivee')
    sillons_depart_df = pd.read_excel(fichier, sheet_name='Sillons depart')
    correspondances_df = pd.read_excel(fichier, sheet_name='Correspondances')
    return chantiers_df, machines_df, sillons_arrivee_df, sillons_depart_df, correspondances_df

def trouver_jours(sillons_depart_df,sillons_arrivee_df):
    max_jour = sillons_depart_df['JDEP'].agg(['max'])
    min_jour = sillons_arrivee_df['JARR'].agg(['min'])
    j1 = datetime.strptime(min_jour['min'].strip(), "%d/%m/%Y")
    jfin = datetime.strptime(max_jour['max'].strip(), "%d/%m/%Y")
    diff = jfin - j1
    jours = diff.days
    return j1, jours

def charger_valeurs(fichier):
    chantiers_df, machines_df, sillons_arrivee_df, sillons_depart_df, correspondances_df = charger_donnees(fichier)
    j1, jours = trouver_jours(sillons_depart_df,sillons_arrivee_df)
    return chantiers_df, machines_df, sillons_arrivee_df, sillons_depart_df, correspondances_df, j1, jours


def process_trains(sillons_arrivee_df, sillons_depart_df, j1, jours):
    machines = ['DEB', 'FOR', 'DEG']
    trains_arr = []
    trains_dep = []
    for x, train in sillons_arrivee_df.iterrows():
        y = ('ARR', train['n°TRAIN'], time_to_minutes_2(train['JARR'], train['HARR'], j1))
        trains_arr.append(y)
    for x, train in sillons_depart_df.iterrows():
        trains_dep.append(('DEP', train['n°TRAIN'], time_to_minutes_2(train['JDEP'], train['HDEP'], j1)))

    trains = trains_arr + trains_dep
    minutes = list(range(0, 24 * 60 * jours))
    return trains, trains_arr, trains_dep, minutes, machines

def temps_indispo(machines_df, jours):
    # Precompute unavailable time periods
    unavailable_periods = {}  # Dict to store unavailable periods for each machine
    for _, row in machines_df.iterrows():
        machine = row['Machine']
        unavailable_times = row['Indisponibilites']
        
        if unavailable_times != 0:
            periods = unavailable_times.split(';')
            unavailable_periods[machine] = []
            for period in periods:
                period = period.strip('()')
                day_of_week, time_str = period.split(',')
                start_time = time_to_minutes(day_of_week, time_str.split('-')[0], jours)
                end_time = time_to_minutes(day_of_week, time_str.split('-')[1], jours)
                unavailable_periods[machine].append((start_time, end_time))

    return unavailable_periods

def trains_requis(trains_dep, trains_arr, correspondances_df, j1):
    # Create the dictionary
    trains_requis_dict = {}
    for train in trains_dep:
        tous_trains = []
        for _, row in correspondances_df.iterrows():
            if row['n°Train depart'] == train[1] and row['Jour depart'] == minute_to_jour(train[2], j1):
                for train_arr in trains_arr:
                    if row['n°Train arrivee'] == train_arr[1] and row['Jour arrivee'] == minute_to_jour(train_arr[2], j1):
                        if train_arr not in tous_trains:
                            tous_trains.append(train_arr)
        trains_requis_dict[train] = tous_trains
    return trains_requis_dict


def minute_to_datetime_df(df_results_test,j1):
    # Convert minutes to date and time for each task
    df_results_test[['Start Date DEB', 'Start Time DEB']] = df_results_test['Start Time DEB'].apply(lambda x: pd.Series(minute_to_jour2(x, j1) if pd.notnull(x) else (None, None)))
    df_results_test[['Start Date FOR', 'Start Time FOR']] = df_results_test['Start Time FOR'].apply(lambda x: pd.Series(minute_to_jour2(x, j1) if pd.notnull(x) else (None, None)))
    df_results_test[['Start Date DEG', 'Start Time DEG']] = df_results_test['Start Time DEG'].apply(lambda x: pd.Series(minute_to_jour2(x, j1) if pd.notnull(x) else (None, None)))

    df_reordered = df_results_test.iloc[:, [0, 1, 4, 2, 5, 3, 6]]

    return df_reordered