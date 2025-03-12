from gurobipy import Model, GRB
import pandas as pd
from utils.utils_data import (
    format_trains, add_time_reference, unavailable_machines, correspondance_for_depart
)
from utils.utils_date import minute_to_date2
from pathlib import Path
from dotenv import load_dotenv
import os

class ModelJalon1:
    def __init__(self):
        """Initialize the optimization model."""
        load_dotenv(override=True)
        self.model_name = os.getenv('MODEL_JALON1_NAME')
        self.model_save_path = os.getenv('MODEL_SAVE_PATH')
        self.results_folder_save_path = os.getenv('RESULTS_FOLDER_SAVE_PATH')
        self.fichier = os.getenv('FILE_INSTANCE')

        self.model = Model(self.model_name)
        self._load_data()
        self._define_variables()
        self._define_constraints()
        self._define_objective_function()
    
    def _load_data(self):
        """Load and process input data."""
        (
            self.chantiers_df, self.machines_df, self.sillons_arrivee_df,
            self.sillons_depart_df, self.correspondances_df, self.j1, self.jours
        ) = add_time_reference(self.fichier)
        
        (
            self.trains, self.trains_arr, self.trains_dep, self.minutes,
            self.machines, self.machines_durees
        ) = format_trains(
            self.machines_df, self.sillons_arrivee_df, self.sillons_depart_df,
            self.j1, self.jours
        )
        
        self.unavailable_periods, self.start_times = unavailable_machines(self.machines_df, self.jours)
        self.trains_requis_dict = correspondance_for_depart(self.trains_dep, self.trains_arr, self.correspondances_df, self.j1)
        print('Data loaded')

    def _define_variables(self):
        """Define model variables."""
        
        def define_decision_variables(self):
            """Define decision variables for the optimization model."""
            self.a = self.model.addVars(self.trains_arr, lb=0, ub=max(self.minutes), vtype=GRB.INTEGER, name="a")
            self.b = self.model.addVars(self.trains_dep, lb=0, ub=max(self.minutes), vtype=GRB.INTEGER, name="b")
            self.c = self.model.addVars(self.trains_dep, lb=0, ub=max(self.minutes), vtype=GRB.INTEGER, name="c")
            
        def define_binary_variables(self):
            """Define binary variables for the optimization model."""
            self.d = self.model.addVars(self.trains_arr, 2, self.start_times, vtype=GRB.BINARY, name="d")
            self.e = self.model.addVars(self.trains_dep, 2, self.start_times, vtype=GRB.BINARY, name="e")
            self.f = self.model.addVars(self.trains_dep, 2, self.start_times, vtype=GRB.BINARY, name="f")

            self.g_before = self.model.addVars(self.trains_arr, self.trains_arr, range(15), vtype=GRB.BINARY, name="g_before")
            self.g_after = self.model.addVars(self.trains_arr, self.trains_arr, range(15), vtype=GRB.BINARY, name="g_after")

            self.k_before = self.model.addVars(self.trains_dep, self.trains_dep, range(15), vtype=GRB.BINARY, name="k_before")
            self.k_after = self.model.addVars(self.trains_dep, self.trains_dep, range(15), vtype=GRB.BINARY, name="k_after")

            self.l_before = self.model.addVars(self.trains_dep, self.trains_dep, range(15), vtype=GRB.BINARY, name="l_before")
            self.l_after = self.model.addVars(self.trains_dep, self.trains_dep, range(15), vtype=GRB.BINARY, name="l_after")

        define_decision_variables(self)
        define_binary_variables(self)
        print('Variables defined')

    def _define_constraints(self):
        """Define constraints for the optimization model."""
        self.M = 10000
        self.epsilon = 0.5
    
        def define_unavailability_constraints():
            """Constraint 1: Ensure machines respect unavailable periods."""
            for machine, periods in self.unavailable_periods.items():
                for (start_time, end_time) in periods:        
                    # Loop through trains only once per unavailable period
                    for t in self.trains: 
                        if t[0] == 'ARR' and machine == 'DEB':
                            self.model.addConstr(self.a[t[0], t[1], t[2]] <= start_time[0] - self.epsilon + self.M * (1 - self.d[t[0], t[1], t[2], 0, start_time[0]]))
                            self.model.addConstr(self.a[t[0], t[1], t[2]] >= end_time[0] + self.epsilon - self.M * self.d[t[0], t[1], t[2], 0, start_time[0]])
                            if start_time[1] != 0:
                                self.model.addConstr(self.a[t[0], t[1], t[2]] <= start_time[1] - self.epsilon + self.M * (1 - self.d[t[0], t[1], t[2], 1,start_time[1]]))
                                self.model.addConstr(self.a[t[0], t[1], t[2]] >= end_time[1] + self.epsilon - self.M * self.d[t[0], t[1], t[2], 1,start_time[1]])
                        elif t[0] == 'DEP' and machine == 'FOR':
                            self.model.addConstr(self.b[t[0], t[1], t[2]] <= start_time[0] - self.epsilon + self.M * (1 - self.e[t[0], t[1], t[2], 0, start_time[0]]))
                            self.model.addConstr(self.b[t[0], t[1], t[2]] >= end_time[0] + self.epsilon - self.M * self.e[t[0], t[1], t[2], 0, start_time[0]])
                            if start_time[1] != 0:
                                self.model.addConstr(self.b[t[0], t[1], t[2]] <= start_time[1] - self.epsilon + self.M * (1 - self.e[t[0], t[1], t[2], 1,start_time[1]]))
                                self.model.addConstr(self.b[t[0], t[1], t[2]] >= end_time[1] + self.epsilon - self.M * self.e[t[0], t[1], t[2], 1,start_time[1]])
                        elif t[0] == 'DEP' and machine == 'DEG':
                            self.model.addConstr(self.c[t[0], t[1], t[2]] <= start_time[0] - self.epsilon + self.M * (1 - self.f[t[0], t[1], t[2], 0, start_time[0]]))
                            self.model.addConstr(self.c[t[0], t[1], t[2]] >= end_time[0] + self.epsilon - self.M * self.f[t[0], t[1], t[2], 0, start_time[0]])
                            if start_time[1] != 0:
                                self.model.addConstr(self.c[t[0], t[1], t[2]] <= start_time[1] - self.epsilon + self.M * (1 - self.f[t[0], t[1], t[2], 1,start_time[1]]))
                                self.model.addConstr(self.c[t[0], t[1], t[2]] >= end_time[1] + self.epsilon - self.M * self.f[t[0], t[1], t[2], 1,start_time[1]])

            print('1: Unavailability machine constraint defined')

        def define_single_train_per_machine_constraints():
            """Constraint 2: Ensure each machine processes one train at a time."""
            for machine in self.machines:
                for i in range(len(self.trains)):
                    for j in range(i + 1, len(self.trains)):
                        train1 = self.trains[i]
                        train2 = self.trains[j]
                        for time in [0, 14]:
                            if train1[0] == 'ARR' and train2[0] == 'ARR' and machine == 'DEB':
                                # Train1 before Train2
                                self.model.addConstr(self.a[train1[0], train1[1], train1[2]] <= self.a[train2[0], train2[1], train2[2]] - time - self.epsilon + self.M * (1 - self.g_before[train1[0], train1[1], train1[2], train2[0], train2[1], train2[2], time])) 
                                # Train1 after Train2
                                self.model.addConstr(self.a[train1[0], train1[1], train1[2]] >= self.a[train2[0], train2[1], train2[2]] + time + self.epsilon - self.M * (1 - self.g_after[train1[0], train1[1], train1[2], train2[0], train2[1], train2[2], time]))
                                # Ensure either before or after
                                self.model.addConstr(self.g_before[train1[0], train1[1], train1[2], train2[0], train2[1], train2[2], time] + self.g_after[train1[0], train1[1], train1[2], train2[0], train2[1], train2[2], time] == 1)

                            elif train1[0] == 'DEP' and train2[0] == 'DEP' and machine == 'FOR':
                                self.model.addConstr(self.b[train1[0], train1[1], train1[2]] <= self.b[train2[0], train2[1], train2[2]] - time - self.epsilon + self.M * (1 - self.k_before[train1[0], train1[1], train1[2], train2[0], train2[1], train2[2], time])) 
                                self.model.addConstr(self.b[train1[0], train1[1], train1[2]] >= self.b[train2[0], train2[1], train2[2]] + time + self.epsilon - self.M * (1 - self.k_after[train1[0], train1[1], train1[2], train2[0], train2[1], train2[2], time]))
                                self.model.addConstr(self.k_before[train1[0], train1[1], train1[2], train2[0], train2[1], train2[2], time] + self.k_after[train1[0], train1[1], train1[2], train2[0], train2[1], train2[2], time] == 1)

                            elif train1[0] == 'DEP' and train2[0] == 'DEP' and machine == 'DEG':
                                self.model.addConstr(self.c[train1[0], train1[1], train1[2]] <= self.c[train2[0], train2[1], train2[2]] - time - self.epsilon + self.M * (1 - self.l_before[train1[0], train1[1], train1[2], train2[0], train2[1], train2[2], time])) 
                                self.model.addConstr(self.c[train1[0], train1[1], train1[2]] >= self.c[train2[0], train2[1], train2[2]] + time + self.epsilon - self.M * (1 - self.l_after[train1[0], train1[1], train1[2], train2[0], train2[1], train2[2], time]))
                                self.model.addConstr(self.l_before[train1[0], train1[1], train1[2], train2[0], train2[1], train2[2], time] + self.l_after[train1[0], train1[1], train1[2], train2[0], train2[1], train2[2], time] == 1)

            print('2: One train processed by a machine constraint defined')


        def define_deb_usage_delay_constraint():
            """Ensure 'DEB' is not used within 60 minutes after train arrival."""
            for train in self.trains:
                if train[0] == 'ARR':
                    arrival_minute = train[2]
                    self.model.addConstr(self.a[train[0],train[1],train[2]] >= arrival_minute + 60, name=f"constraint_DEB_{train[1]}")
            print('3: DEB usage delay constraint defined')

        def define_deg_time_limit_constraint():
            """Ensure 'DEG' is used at most 35 minutes before train departure."""
            for train in self.trains:
                if train[0] == 'DEP':
                    departure_minute = train[2]        
                    self.model.addConstr(self.c[train[0],train[1],train[2]] <= departure_minute - 35, name=f"constraint_DEG_{train[1]}")
            print('4: DEG time limit constraint defined')

        def define_for_after_deb_constraint():
            """Ensure 'FOR' starts only after all required 'DEB' processes finish."""
            for dep_train, arr_trains in self.trains_requis_dict.items():
                for arr_train in arr_trains:
                    self.model.addConstr(self.b[dep_train[0], dep_train[1], dep_train[2]] >= self.a[arr_train[0], arr_train[1], arr_train[2]] + 15, name=f"constraint_FOR_DEB_{dep_train[1]}_{arr_train[1]}")
            print('5: FOR after DEB constraint defined')

        def define_for_before_deg_constraint():
            """Ensure 'FOR' is used at least 165 minutes before 'DEG'."""
            for train in self.trains_dep:
                self.model.addConstr(self.c[train[0],train[1],train[2]] >= self.b[train[0],train[1],train[2]] + 165, name=f"constraint_DEG_FOR_{train[1]}")
            print('6: FOR before DEG constraint defined')
            
        define_unavailability_constraints()
        define_single_train_per_machine_constraints()
        define_deb_usage_delay_constraint()
        define_deg_time_limit_constraint()
        define_for_after_deb_constraint()
        define_for_before_deg_constraint()

        print('Constraints defined')
    
    def _define_objective_function(self):
        self.model.setObjective(0, GRB.MINIMIZE)  # Pas d'optimisation spécifique ici pour ce jalon
        print('Objective function defined')

    def optimize(self):
        """Optimize the model."""
        self.model.optimize()
        print('Optimization complete')

    def save_model(self):
        """Save the model to a file."""
        self.model.write(self.model_save_path)
        print(f'Model saved to {self.model_save_path}')

    def get_results(self):
        """Extract and return results after optimization."""
        if self.model.status == GRB.OPTIMAL:
            results = []
            for train in self.trains:
                if train[0] == 'ARR':
                    jour, horaire = minute_to_date2(self.model.getVarByName(f'a[{train[0]},{train[1]},{train[2]}]').X, self.j1)
                    results.append({
                        'Id tâche': f'{self.machines[0]}_{train[1]}_{jour}',
                        'Type de tâche': self.machines[0],
                        'Jour': jour,
                        'Heure début': horaire,
                        'Durée': self.machines_durees[0],
                        'Sillon': train[1]
                    })
                elif train[0] == 'DEP':
                    jour, horaire = minute_to_date2(self.model.getVarByName(f'b[{train[0]},{train[1]},{train[2]}]').X, self.j1)
                    results.append({
                        'Id tâche': f'{self.machines[1]}_{train[1]}_{jour}',
                        'Type de tâche': self.machines[1],
                        'Jour': jour,
                        'Heure début': horaire,
                        'Durée': self.machines_durees[1],
                        'Sillon': train[1]
                    })
                    jour, horaire = minute_to_date2(self.model.getVarByName(f'c[{train[0]},{train[1]},{train[2]}]').X, self.j1)
                    results.append({
                        'Id tâche': f'{self.machines[2]}_{train[1]}_{jour}',
                        'Type de tâche': self.machines[2],
                        'Jour': jour,
                        'Heure début': horaire,
                        'Durée': self.machines_durees[2],
                        'Sillon': train[1]
                    })

            # Create a DataFrame from the results
            df_results = pd.DataFrame(results)
            file_name = Path(self.fichier).stem
            df_results.to_excel(f'{self.results_folder_save_path}/results_{file_name}.xlsx', index=False, sheet_name="Taches machine")
            print(f'Results saved to {self.results_folder_save_path}/results_{file_name}.xlsx')

            return df_results
        else:
            print("No optimal solution found")
            return None
        
    def run_optimization(self):
        """Run the full optimization process."""
        self.optimize()
        self.save_model()
        df_results = self.get_results()
        return df_results
