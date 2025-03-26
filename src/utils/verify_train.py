import streamlit as st
import pandas as pd
from utils_date import minute_to_date2
from utils_data import add_time_reference, format_trains, correspondance_for_depart

# Mapping for file selection and their respective output files for DEB/DEG/FOR times
FILE_MAP = {
    "Réaliste jalon2": ('data/instance_WPY_realiste_jalon2.xlsx', 'outputs/results/results_instance_WPY_realiste_jalon2_jalon2.xlsx'),
    "Simple": ("data/instance_WPY_simple.xlsx", "outputs/results/results_instance_WPY_simple.xlsx"),
    "Réaliste jalon1": ('data/instance_WPY_realiste_jalon1.xlsx', 'outputs/results/results_instance_WPY_realiste_jalon1.xlsx')
}

st.title("Train Correspondance Tracker 🚆")

selected_file_key = st.selectbox("Choisissez votre instance:", list(FILE_MAP.keys()))
selected_file, results_file = FILE_MAP[selected_file_key]

# Load data
st.write(f"🔄 Chargement des données pour: **{selected_file_key}**...")
chantiers_df, machines_df, sillons_arrivee_df, sillons_depart_df, correspondances_df, j1, jours, first_day = add_time_reference(selected_file)
trains, trains_arr, trains_dep, *_ = format_trains(machines_df, sillons_arrivee_df, sillons_depart_df, chantiers_df, j1, jours, first_day)
results_df = pd.read_excel(results_file)

# Train number input
train_num = st.number_input("Entrez le numéro du train de départ:", min_value=0, step=1, format="%d")

if train_num:
    train_depart = next((t for t in trains_dep if t[1] == train_num), None)
    
    if train_depart:
        departure_day, departure_time = minute_to_date2(train_depart[2], j1)
        st.write(f"### 🚉 Train {train_num} part à **{departure_day}, {departure_time}**")

        correspondances = correspondance_for_depart([train_depart], trains_arr, correspondances_df, j1)
        
        if correspondances.get(train_depart):
            st.write("### 🛬 Trains d'arrivées correspondants:")
            for train_arr in correspondances[train_depart]:
                arrival_day, arrival_time = minute_to_date2(train_arr[2], j1)
                st.write(f"- **Train {train_arr[1]}** → Arrivée à **{arrival_day}, {arrival_time}**")

                # Fetch DEB time for the arrival train (deb_trainnumber_hour)
                deb_time = results_df[results_df['Id tâche'] == f'DEB_{train_arr[1]}_{arrival_day}']
                deb_time = deb_time[deb_time['Type de tâche'] == 'DEB']

                if not deb_time.empty:
                    deb_time_row = deb_time.iloc[0]
                    deb_hour = deb_time_row['Heure début']
                    st.write(f"    - **Temps DEB**: {deb_time_row['Jour']} à {deb_hour}")
                else:
                    st.write(f"    ⚠️ Temps DEB non trouvé pour le train {train_arr[1]}.")

        else:
            st.write("⚠️ Aucune correspondance trouvée.")

        # Fetch FOR and DEG times for the departure train (for_trainnumber_day, deg_trainnumber_day)
        for_time = results_df[results_df['Id tâche'] == f'FOR_{train_num}_{departure_day}']
        for_time = for_time[for_time['Type de tâche'] == 'FOR']
        
        deg_time = results_df[results_df['Id tâche'] == f'DEG_{train_num}_{departure_day}']
        deg_time = deg_time[deg_time['Type de tâche'] == 'DEG']

        if not for_time.empty:
            for_time_row = for_time.iloc[0]
            st.write(f"### 🚉 Temps FOR pour le train de départ {train_num}: {for_time_row['Jour']} à {for_time_row['Heure début']}")
        else:
            st.write(f"⚠️ Aucune correspondance FOR trouvée pour le train {train_num} le {departure_day}.")

        if not deg_time.empty:
            deg_time_row = deg_time.iloc[0]
            st.write(f"### 🛣️ Temps DEG pour le train de départ {train_num}: {deg_time_row['Jour']} à {deg_time_row['Heure début']}")
        else:
            st.write(f"⚠️ Aucune correspondance DEG trouvée pour le train {train_num} le {departure_day}.")
        
    else:
        st.write("❌ Train de départ non trouvé.")
