from gurobipy import Model, GRB
import pandas as pd
from utils.utils_data import format_trains, add_time_reference, unavailable_machines, correspondance_for_depart, unavailable_chantiers
from utils.utils_date import minute_to_date2
from pathlib import Path
from dotenv import load_dotenv
import os
import time as tme

def create_model(fichier):
    """Create the optimization model"""
    start_program_time = tme.time()
    load_dotenv(override=True)
    MODEL_JALON1_NAME = os.getenv('MODEL_JALON1_NAME')
    MODEL_SAVE_PATH = os.getenv('MODEL_SAVE_PATH')
    RESULTS_FOLDER_SAVE_PATH = os.getenv('RESULTS_FOLDER_SAVE_PATH')

    # Charger les données
    chantiers_df, machines_df, sillons_arrivee_df, sillons_depart_df, correspondances_df, j1, jours,first_day = add_time_reference(fichier)
    trains, trains_arr, trains_dep, minutes, machines, machines_durees = format_trains(machines_df, sillons_arrivee_df, sillons_depart_df, j1, jours,first_day)
    unavailable_periods, start_times = unavailable_machines(machines_df, jours,first_day)
    unavailable_periods_chantiers, start_times_chantiers = unavailable_chantiers(chantiers_df, jours,first_day)
    trains_requis_dict = correspondance_for_depart(trains_dep, trains_arr, correspondances_df, j1)


    print('Donnees chargees')
    data_loaded_time = tme.time()


    # Cree un modele
    model = Model(MODEL_JALON1_NAME)

    print(f'{MODEL_JALON1_NAME} cree')

    # Definir les variables de decision
    a = model.addVars(trains_arr, lb=0, ub=max(minutes), vtype=GRB.INTEGER, name="a")
    b = model.addVars(trains_dep, lb=0, ub=max(minutes), vtype=GRB.INTEGER, name="b")
    c = model.addVars(trains_dep, lb=0, ub=max(minutes), vtype=GRB.INTEGER, name="c")

    # Definir les variables auxiliares
    aint = model.addVars(trains_arr, vtype=GRB.INTEGER, name="aint") #pour assurer que a,b,c sont tous les 15 minutes
    bint = model.addVars(trains_dep, vtype=GRB.INTEGER, name="bint")
    cint = model.addVars(trains_dep, vtype=GRB.INTEGER, name="cint")

    # Definir les variables binaires
    d = model.addVars(trains_arr, 2, start_times, vtype=GRB.BINARY, name="d")
    e = model.addVars(trains_dep, 2, start_times, vtype=GRB.BINARY, name="e")
    f = model.addVars(trains_dep, 2, start_times, vtype=GRB.BINARY, name="f")

    g_before = model.addVars(trains_arr, trains_arr, range(15), vtype=GRB.BINARY, name="g_before")
    g_after = model.addVars(trains_arr, trains_arr, range(15), vtype=GRB.BINARY, name="g_after")

    k_before = model.addVars(trains_dep, trains_dep, range(15), vtype=GRB.BINARY, name="k_before")
    k_after = model.addVars(trains_dep, trains_dep, range(15), vtype=GRB.BINARY, name="k_after")

    l_before = model.addVars(trains_dep, trains_dep, range(15), vtype=GRB.BINARY, name="l_before")
    l_after = model.addVars(trains_dep, trains_dep, range(15), vtype=GRB.BINARY, name="l_after")

    chant_d = model.addVars(trains_arr, 2, start_times_chantiers, vtype=GRB.BINARY, name="chant_d")
    chant_e = model.addVars(trains_dep, 2, start_times_chantiers, vtype=GRB.BINARY, name="chant_e")
    chant_f = model.addVars(trains_dep, 2, start_times_chantiers, vtype=GRB.BINARY, name="chant_f")

    print('Variables definies')
    
    # Contrainte 1.1: Periodes d'indisponibilite machine
    M = max(minutes)+1
    epsilon = 0.5

    for machine, periods in unavailable_periods.items():
        for (start_time, end_time) in periods:        
            # Loop through trains only once per unavailable period
            for t in trains: 
                if t[0] == 'ARR' and machine == 'DEB':
                    model.addConstr(a[t[0], t[1], t[2]] <= start_time[0] - epsilon + M * (1 - d[t[0], t[1], t[2], 0, start_time[0],machine]))
                    model.addConstr(a[t[0], t[1], t[2]] >= end_time[0] + epsilon - M * d[t[0], t[1], t[2], 0, start_time[0],machine])
                    if start_time[1] != 0:
                        model.addConstr(a[t[0], t[1], t[2]] <= start_time[1] - epsilon + M * (1 - d[t[0], t[1], t[2], 1,start_time[1],machine]))
                        model.addConstr(a[t[0], t[1], t[2]] >= end_time[1] + epsilon - M * d[t[0], t[1], t[2], 1,start_time[1],machine])
                elif t[0] == 'DEP' and machine == 'FOR':
                    model.addConstr(b[t[0], t[1], t[2]] <= start_time[0] - epsilon + M * (1 - e[t[0], t[1], t[2], 0, start_time[0],machine]))
                    model.addConstr(b[t[0], t[1], t[2]] >= end_time[0] + epsilon - M * e[t[0], t[1], t[2], 0, start_time[0],machine])
                    if start_time[1] != 0:
                        model.addConstr(b[t[0], t[1], t[2]] <= start_time[1] - epsilon + M * (1 - e[t[0], t[1], t[2], 1,start_time[1],machine]))
                        model.addConstr(b[t[0], t[1], t[2]] >= end_time[1] + epsilon - M * e[t[0], t[1], t[2], 1,start_time[1],machine])
                elif t[0] == 'DEP' and machine == 'DEG':
                    model.addConstr(c[t[0], t[1], t[2]] <= start_time[0] - epsilon + M * (1 - f[t[0], t[1], t[2], 0, start_time[0],machine]))
                    model.addConstr(c[t[0], t[1], t[2]] >= end_time[0] + epsilon - M * f[t[0], t[1], t[2], 0, start_time[0],machine])
                    if start_time[1] != 0:
                        model.addConstr(c[t[0], t[1], t[2]] <= start_time[1] - epsilon + M * (1 - f[t[0], t[1], t[2], 1,start_time[1],machine]))
                        model.addConstr(c[t[0], t[1], t[2]] >= end_time[1] + epsilon - M * f[t[0], t[1], t[2], 1,start_time[1],machine])

    print('Contrainte 1.1 definie')

    # Contrainte 1.2: Periodes d'indisponibilite chantier

    for chantier, periods in unavailable_periods_chantiers.items():
        for (start_time, end_time) in periods:        
            # Loop through trains only once per unavailable period
            for t in trains: 
                if t[0] == 'ARR' and chantier == 'WPY_REC':
                    # machine DEB
                    model.addConstr(a[t[0], t[1], t[2]] <= start_time[0] - epsilon + M * (1 - chant_d[t[0], t[1], t[2], 0, start_time[0],chantier]))
                    model.addConstr(a[t[0], t[1], t[2]] >= end_time[0] + epsilon - M * chant_d[t[0], t[1], t[2], 0, start_time[0],chantier])
                    if start_time[1] != 0:
                        model.addConstr(a[t[0], t[1], t[2]] <= start_time[1] - epsilon + M * (1 - chant_d[t[0], t[1], t[2], 1,start_time[1],chantier]))
                        model.addConstr(a[t[0], t[1], t[2]] >= end_time[1] + epsilon - M * chant_d[t[0], t[1], t[2], 1,start_time[1],chantier])
                elif t[0] == 'DEP' and chantier == 'WPY_FOR':
                    # machine FOR
                    model.addConstr(b[t[0], t[1], t[2]] <= start_time[0] - epsilon + M * (1 - chant_e[t[0], t[1], t[2], 0, start_time[0],chantier]))
                    model.addConstr(b[t[0], t[1], t[2]] >= end_time[0] + epsilon - M * chant_e[t[0], t[1], t[2], 0, start_time[0],chantier])
                    if start_time[1] != 0:
                        model.addConstr(b[t[0], t[1], t[2]] <= start_time[1] - epsilon + M * (1 - chant_e[t[0], t[1], t[2], 1,start_time[1],chantier]))
                        model.addConstr(b[t[0], t[1], t[2]] >= end_time[1] + epsilon - M * chant_e[t[0], t[1], t[2], 1,start_time[1],chantier])
                    # machine DEG    
                    model.addConstr(c[t[0], t[1], t[2]] <= start_time[0] - epsilon + M * (1 - chant_f[t[0], t[1], t[2], 0, start_time[0],chantier]))
                    model.addConstr(c[t[0], t[1], t[2]] >= end_time[0] + epsilon - M * chant_f[t[0], t[1], t[2], 0, start_time[0],chantier])
                    if start_time[1] != 0:
                        model.addConstr(c[t[0], t[1], t[2]] <= start_time[1] - epsilon + M * (1 - chant_f[t[0], t[1], t[2], 1,start_time[1],chantier]))
                        model.addConstr(c[t[0], t[1], t[2]] >= end_time[1] + epsilon - M * chant_f[t[0], t[1], t[2], 1,start_time[1],chantier])

    print('Contrainte 1.2 definie')

    # Contrainte 2: Chaque machine ne peut traiter qu'un train a la fois
    for machine in machines:
        for i in range(len(trains)):
            for j in range(i + 1, len(trains)):
                train = trains[i]
                train2 = trains[j]
                for time in [0,14]:  
                    if train[0] == 'ARR' and train2[0] == 'ARR' and machine == 'DEB':
                        # Train1 before Train2
                        model.addConstr(a[train[0], train[1], train[2]] <= a[train2[0], train2[1], train2[2]] - time - epsilon + M * (1 - g_before[train[0], train[1], train[2], train2[0], train2[1], train2[2], time])) 
                        # Train1 after Train2
                        model.addConstr(a[train[0], train[1], train[2]] >= a[train2[0], train2[1], train2[2]] + time + epsilon - M * (1 - g_after[train[0], train[1], train[2], train2[0], train2[1], train2[2], time]))
                        # Ensure either before or after
                        model.addConstr(g_before[train[0], train[1], train[2], train2[0], train2[1], train2[2], time] + g_after[train[0], train[1], train[2], train2[0], train2[1], train2[2], time] == 1)

                    elif train[0] == 'DEP' and train2[0] == 'DEP' and machine == 'FOR':
                        # Train1 before Train2
                        model.addConstr(b[train[0], train[1], train[2]] <= b[train2[0], train2[1], train2[2]] - time - epsilon + M * (1 - k_before[train[0], train[1], train[2], train2[0], train2[1], train2[2], time])) 
                        # Train1 after Train2
                        model.addConstr(b[train[0], train[1], train[2]] >= b[train2[0], train2[1], train2[2]] + time + epsilon - M * (1 - k_after[train[0], train[1], train[2], train2[0], train2[1], train2[2], time]))
                        # Ensure either before or after
                        model.addConstr(k_before[train[0], train[1], train[2], train2[0], train2[1], train2[2], time] + k_after[train[0], train[1], train[2], train2[0], train2[1], train2[2], time] == 1)

                    elif train[0] == 'DEP' and train2[0] == 'DEP' and machine == 'DEG':
                        # Train1 before Train2
                        model.addConstr(c[train[0], train[1], train[2]] <= c[train2[0], train2[1], train2[2]] - time - epsilon + M * (1 - l_before[train[0], train[1], train[2], train2[0], train2[1], train2[2], time])) 
                        # Train1 after Train2
                        model.addConstr(c[train[0], train[1], train[2]] >= c[train2[0], train2[1], train2[2]] + time + epsilon - M * (1 - l_after[train[0], train[1], train[2], train2[0], train2[1], train2[2], time]))
                        # Ensure either before or after
                        model.addConstr(l_before[train[0], train[1], train[2], train2[0], train2[1], train2[2], time] + l_after[train[0], train[1], train[2], train2[0], train2[1], train2[2], time] == 1)
        
    print('Contrainte 2 definie')

    # Contrainte 3: la machine 'DEB' ne peut pas être utilisée dans les 60 minutes suivant l'heure d'arrivée du train
    for train in trains:
        if train[0] == 'ARR': 
            arrival_minute = train[2]
            model.addConstr(a[train[0],train[1],train[2]] >= arrival_minute + 60, name=f"constraint_DEB_{train[1]}")
    
    print('Contrainte 3 definie')

    # Contrainte 4: la machine 'DEG' doit être utilisée avant 35 minutes avant le départ du train de type 'DEP'
    for train in trains:
        if train[0] == 'DEP':
            departure_minute = train[2]        
            model.addConstr(c[train[0],train[1],train[2]] <= departure_minute - 35, name=f"constraint_DEG_{train[1]}")
    
    print('Contrainte 4 definie')

    # Contrainte 5: Machine 'FOR' ne peut pas commencer avant tous les trains necessaire sont finis avec 'DEB'
    for dep_train, arr_trains in trains_requis_dict.items():
        for arr_train in arr_trains:
            model.addConstr(b[dep_train[0], dep_train[1], dep_train[2]] >= a[arr_train[0], arr_train[1], arr_train[2]] + 15, name=f"constraint_FOR_DEB_{dep_train[1]}_{arr_train[1]}")

    print('Contrainte 5 definie')

    # Contrainte 6: la machine 'FOR' doit être utilisée avant 165 minutes avant machine 'DEG'
    for train in trains_dep:
        model.addConstr(c[train[0],train[1],train[2]] >= b[train[0],train[1],train[2]] + 165, name=f"constraint_DEG_FOR_{train[1]}")

    print('Contrainte 6 definie, optimisation en cours...')


    # Constraint 7: Tasks can only begin every 15 mins (h:00,h:15,h:30,h:45)
    for train in trains_arr:
        model.addConstr(a[train[0],train[1],train[2]]==15*aint[train[0],train[1],train[2]],name=f'constraint_creneaux_{train}')
    for train in trains_dep:
        model.addConstr(b[train[0],train[1],train[2]]==15*bint[train[0],train[1],train[2]],name=f'constraint_creneaux_{train}')
        model.addConstr(c[train[0],train[1],train[2]]==15*cint[train[0],train[1],train[2]],name=f'constraint_creneaux_{train}')

    # # Contrainte 7: definir voie occupation comme 1 si train est dans le chantier
    # for minute in minutes:
    #     for train in trains_arr:
    #         model.addConstr(minute <= train[2] - M * REC_voie_occupation[minute,train[0],train[1],train[2]], name = "Force_0_lower_REC")
    #         model.addConstr(a[train[0],train[1],train[2]] + 14 >= minute + M * (1 - REC_voie_occupation[minute,train[0],train[1],train[2]]), name = "Force_1_REC")
    #         model.addConstr(minute >= a[train[0],train[1],train[2]] + 15 - M * REC_voie_occupation[minute,train[0],train[1],train[2]], name = "Force_0_upper_REC")
    #     for train in trains_dep:            
    #         model.addConstr(b[train[0],train[1],train[2]] <= minute + M * (1 - FOR_voie_occupation[minute,train[0],train[1],train[2]]), name = "Force_1_lower_FOR")
    #         model.addConstr(minute <= c[train[0],train[1],train[2]] + 15 - M * FOR_voie_occupation[minute,train[0],train[1],train[2]], name = "Force_1_upper_FOR")
    #         model.addConstr(minute <= b[train[0],train[1],train[2]] - 1 - M * FOR_voie_occupation[minute,train[0],train[1],train[2]], name = "Force_0_lower_FOR")
    #         model.addConstr(minute >= c[train[0],train[1],train[2]] + 15 + 1 - M * FOR_voie_occupation[minute,train[0],train[1],train[2]], name = "Force_0_upper_FOR")

    #         model.addConstr(minute >= a[train[0],train[1],train[2]] + 15 - M * DEP_voie_occupation[minute,train[0],train[1],train[2]], name = "Force_0_lower_DEP")
    #         model.addConstr(a[train[0],train[1],train[2]] + 14 >= minute + M * (1 - DEP_voie_occupation[minute,train[0],train[1],train[2]]), name = "Force_1_DEP")
    #         model.addConstr(minute >= train[2] - M * DEP_voie_occupation[minute,train[0],train[1],train[2]], name = "Force_0_upper_DEP")

    constraint_variable_time = tme.time()
    # Optimisation
    model.setObjective(0, GRB.MINIMIZE)  # Pas d'optimisation spécifique ici pour ce jalon

    # Résolution du problème
    model.optimize()
    
    optimisation_time = tme.time()
    # Sauvegarder le modèle
    model.write(MODEL_SAVE_PATH)

    # Afficher les résultats
    if model.status == GRB.OPTIMAL:
        print('Solution optimale trouvée')
        results = []
        for train in trains:
            if train[0] == 'ARR':
                jour, horaire = minute_to_date2(a[train[0],train[1],train[2]].X,j1)
                results.append({
                    'Id tâche': f'{machines[0]}_{train[1]}_{jour}',
                    'Type de tâche': machines[0],
                    'Jour': jour,
                    'Heure début': horaire,
                    'Durée': machines_durees[0],
                    'Sillon': train[1]
                })
            elif train[0] == 'DEP':
                jour, horaire = minute_to_date2(b[train[0],train[1],train[2]].X,j1)
                results.append({
                    'Id tâche': f'{machines[1]}_{train[1]}_{jour}',
                    'Type de tâche': machines[1],
                    'Jour': jour,
                    'Heure début': horaire,
                    'Durée': machines_durees[1],
                    'Sillon': train[1]
                })
                jour, horaire = minute_to_date2(c[train[0],train[1],train[2]].X,j1)
                results.append({
                    'Id tâche': f'{machines[2]}_{train[1]}_{jour}',
                    'Type de tâche': machines[2],
                    'Jour': jour,
                    'Heure début': horaire,
                    'Durée': machines_durees[2],
                    'Sillon': train[1]
                })
        
        # Create a DataFrame from the results
        df_results = pd.DataFrame(results)
        FILE_NAME = Path(fichier).stem
        df_results.to_excel(f'{RESULTS_FOLDER_SAVE_PATH}/results_{FILE_NAME}.xlsx', index=False, sheet_name="Taches machine")


    else:
        print("Aucune solution optimale trouvée.")
        model.computeIIS()
        model.write('infeasible.ilp')
        FILE_NAME = Path(fichier).stem

    print(f'Modele resolu, resultats disponible à {RESULTS_FOLDER_SAVE_PATH}/results_{FILE_NAME}.xlsx')
    print(f'Time taken for: Data Loading = {data_loaded_time-start_program_time}s, Variables and Constraints = {constraint_variable_time-data_loaded_time}s, Optimisation = {optimisation_time-constraint_variable_time}s')

    return df_results
