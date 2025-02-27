from gurobipy import Model, GRB
import pandas as pd
from datetime import datetime

# Fonction pour convertir une heure au format "HH:MM" en minutes depuis minuit
def time_to_minutes(time_str):
    time_part = time_str.split(',')[1] if ',' in time_str else time_str
    time_part = time_part.strip('()')  # Enlever les parenthèses
    time_obj = datetime.strptime(time_part, "%H:%M")
    return time_obj.hour * 60 + time_obj.minute

# Charger les données
fichier = 'instance_WPY_realiste_jalon1.xlsx'
chantiers_df = pd.read_excel(fichier, sheet_name='Chantiers')
machines_df = pd.read_excel(fichier, sheet_name='Machines')
sillons_arrivee_df = pd.read_excel(fichier, sheet_name='Sillons arrivee')

# Définir un modèle Gurobi
model = Model("planification_taches_machines")

# Variables de décision : x_m,h,w = 1 si la machine m travaille sur le wagon w à l'heure h, 0 sinon
# Listes des machines, heures et wagons
machines = machines_df['Machine'].tolist()
wagons = sillons_arrivee_df['n°TRAIN'].tolist()
hours = range(24 * 60 * 7)  # De 0 à  minutes (pour chaque minute de la semaine)

