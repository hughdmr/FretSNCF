from gurobipy import Model, GRB
import pandas as pd
from utils_donnees import charger_valeurs, process_trains, temps_indispo, trains_requis, minute_to_datetime_df

def creer_modele():

    # Charger les données
    fichier = 'instance_WPY_realiste_jalon1.xlsx'
    chantiers_df, machines_df, sillons_arrivee_df, sillons_depart_df, correspondances_df, j1, jours = charger_valeurs(fichier)
    trains, trains_arr, trains_dep, minutes, machines = process_trains(sillons_arrivee_df, sillons_depart_df, j1, jours)
    unavailable_periods = temps_indispo(machines_df, jours)
    trains_requis_dict = trains_requis(trains_dep, trains_arr, correspondances_df, j1)


    print('Donnees chargees')


    # Cree un modele
    model = Model('optimisation')

    print('Modele cree')

    # Definir les variables de decision
    a = model.addVars(trains_arr, lb=0, ub=max(minutes), vtype=GRB.INTEGER, name="a")
    b = model.addVars(trains_dep, lb=0, ub=max(minutes), vtype=GRB.INTEGER, name="b")
    c = model.addVars(trains_dep, lb=0, ub=max(minutes), vtype=GRB.INTEGER, name="c")

    # Definir les variables binaires
    d = model.addVars(trains_arr, 2, vtype=GRB.BINARY, name="d")
    e = model.addVars(trains_dep, 2, vtype=GRB.BINARY, name="e")
    f = model.addVars(trains_dep, 2, vtype=GRB.BINARY, name="f")
    g = model.addVars(trains_arr, vtype=GRB.BINARY, name="g")
    k = model.addVars(trains_dep, vtype=GRB.BINARY, name="h")
    l = model.addVars(trains_dep, vtype=GRB.BINARY, name="i")

    print('Variables definies')
    
    # Contrainte 1: Periodes d'indisponibilite
    epsilon = 1
    for machine, periods in unavailable_periods.items():
        for (start_time, end_time) in periods:
            for t in trains:
                # Constraints for start_time[0] to end_time[0]
                for h in range(start_time[0], end_time[0]):
                    if t[0] == 'ARR' and machine == 'DEB':
                        model.addGenConstrIndicator(d[t[0],t[1],t[2],0], 0, a[t[0],t[1],t[2]] <= h - epsilon)
                        model.addGenConstrIndicator(d[t[0],t[1],t[2],0], 0, a[t[0],t[1],t[2]] >= h + epsilon)
                    elif t[0] == 'DEP' and machine == 'FOR':
                        model.addGenConstrIndicator(e[t[0],t[1],t[2],0], 0, b[t[0],t[1],t[2]] <= h - epsilon)
                        model.addGenConstrIndicator(e[t[0],t[1],t[2],0], 0, b[t[0],t[1],t[2]] >= h + epsilon)
                    elif t[0] == 'DEP' and machine == 'DEG':
                        model.addGenConstrIndicator(f[t[0],t[1],t[2],0], 0, c[t[0],t[1],t[2]] <= h - epsilon)
                        model.addGenConstrIndicator(f[t[0],t[1],t[2],0], 0, c[t[0],t[1],t[2]] >= h + epsilon)
                
                # Constraints for start_time[1] to end_time[1]
                for h in range(start_time[1], end_time[1]):
                    if t[0] == 'ARR' and machine == 'DEB':
                        model.addGenConstrIndicator(d[t[0],t[1],t[2],1], 0, a[t[0],t[1],t[2]] <= h - epsilon)
                        model.addGenConstrIndicator(d[t[0],t[1],t[2],1], 0, a[t[0],t[1],t[2]] >= h + epsilon)
                    elif t[0] == 'DEP' and machine == 'FOR':
                        model.addGenConstrIndicator(e[t[0],t[1],t[2],1], 0, b[t[0],t[1],t[2]] <= h - epsilon)
                        model.addGenConstrIndicator(e[t[0],t[1],t[2],1], 0, b[t[0],t[1],t[2]] >= h + epsilon)
                    elif t[0] == 'DEP' and machine == 'DEG':
                        model.addGenConstrIndicator(f[t[0],t[1],t[2],1], 0, c[t[0],t[1],t[2]] <= h - epsilon)
                        model.addGenConstrIndicator(f[t[0],t[1],t[2],1], 0, c[t[0],t[1],t[2]] >= h + epsilon)

    print('Contrainte 1 definie')

    # Contrainte 2: Chaque machine ne peut traiter qu'un train a la fois
    for machine in machines:
        for train in trains:
            for train2 in trains:
                if train != train2:
                    for time in range(15):  # Ensure valid values of t
                        if train[0] == 'ARR' and train2[0] == 'ARR' and machine == 'DEB':
                            model.addGenConstrIndicator(g[train[0],train[1],train[2]], 0, a[train[0],train[1],train[2]] <= a[train2[0],train2[1],train2[2]] - time - epsilon)
                            model.addGenConstrIndicator(g[train[0],train[1],train[2]], 0, a[train[0],train[1],train[2]] >= a[train2[0],train2[1],train2[2]] + time + epsilon)
                        elif train[0] == 'DEP' and train2[0] == 'DEP' and machine == 'FOR':
                            model.addGenConstrIndicator(k[train[0],train[1],train[2]], 0, b[train[0],train[1],train[2]] <= b[train2[0],train2[1],train2[2]] - time - epsilon)
                            model.addGenConstrIndicator(k[train[0],train[1],train[2]], 0, b[train[0],train[1],train[2]] >= b[train2[0],train2[1],train2[2]] + time + epsilon)
                        elif train[0] == 'DEP' and train2[0] == 'DEP' and machine == 'DEG':
                            model.addGenConstrIndicator(l[train[0],train[1],train[2]], 0, c[train[0],train[1],train[2]] <= c[train2[0],train2[1],train2[2]] - time - epsilon)
                            model.addGenConstrIndicator(l[train[0],train[1],train[2]], 0, c[train[0],train[1],train[2]] >= c[train2[0],train2[1],train2[2]] + time + epsilon)
    
    print('Contrainte 2 definie')

    # Contrainte 3: la machine 'DEB' ne peut pas être utilisée dans les 60 minutes suivant l'heure d'arrivée du train
    for train in trains:
        if train[0] == 'ARR':  # Check if the train type is 'ARR'
            arrival_minute = train[2]
            model.addConstr(a[train[0],train[1],train[2]] >= arrival_minute + 60, name=f"constraint_DEB_{t[1]}")
    
    print('Contrainte 3 definie')

    # Contrainte 4: la machine 'DEG' doit être utilisée avant 35 minutes avant le départ du train de type 'DEP'
    for train in trains:
        if train[0] == 'DEP':  # Check if the train type is 'DEP'
            departure_minute = t[2]
            model.addConstr(c[train[0],train[1],train[2]] <= departure_minute - 35, name=f"constraint_DEG_{t[1]}")
    
    print('Contrainte 4 definie')

    # Contrainte 5: Machine 'FOR' ne peut pas commencer avant tous les trains necessaire sont finis avec 'DEB'
    for dep_train, arr_trains in trains_requis_dict.items():
        for arr_train in arr_trains:
            model.addConstr(b[dep_train[0], dep_train[1], dep_train[2]] >= a[arr_train[0], arr_train[1], arr_train[2]] + 15, name=f"constraint_FOR_DEB_{dep_train[1]}_{arr_train[1]}")

    print('Contrainte 5 definie')

    # Contrainte 6: la machine 'FOR' doit être utilisée avant 165 minutes avant machine 'DEG'
    for train in trains_dep:
        model.addConstr(c[train[0],train[1],train[2]] >= b[train[0],train[1],train[2]] + 165, name=f"constraint_DEG_FOR_{t[1]}")

    print('Contrainte 6 definie, optimisation en cours...')


    # Optimisation
    model.setObjective(0, GRB.MINIMIZE)  # Pas d'optimisation spécifique ici pour ce jalon

    # Résolution du problème
    model.optimize()

    # Afficher les résultats
    if model.status == GRB.OPTIMAL:
        print('Solution optimale trouvée')
        results = []
        for train in trains:
            results.append({
                'Train': train,
                'Start Time DEB': a[train[0],train[1],train[2]].X if train in trains_arr else None,
                'Start Time FOR': b[train[0],train[1],train[2]].X if train in trains_dep else None,
                'Start Time DEG': c[train[0],train[1],train[2]].X if train in trains_dep else None
            })
        
        # Create a DataFrame from the results
        df_results = pd.DataFrame(results)

        # Convertir les minutes en date et heure pour chaque tâche
        df_reordered = minute_to_datetime_df(df_results, j1)
        df_reordered.to_excel('resultats.xlsx', index=False)

    else:
        print("Aucune solution optimale trouvée.")

    print('Modele resolu')
