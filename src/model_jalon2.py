# COPY OF model_jalon1.py, WILL BE UPDATED FOR JALON2.

from gurobipy import Model, GRB, quicksum
import pandas as pd
from utils.utils_data import (
    format_trains, add_time_reference, unavailable_machines, correspondance_for_depart, unavailable_chantiers, find_max_voies
)
from utils.utils_date import minute_to_date2
from pathlib import Path
from dotenv import load_dotenv
import os
import time as tme

class ModelJalon2:
    """Optimization model for Jalon 2."""
    def __init__(self):
        """Initialize the optimization model."""
        self.start_program_time = tme.time()
        load_dotenv(override=True)
        self.model_name = os.getenv('MODEL_NAME')
        self.model_save_path = os.getenv('MODEL_SAVE_PATH')
        self.results_folder_save_path = os.getenv('RESULTS_FOLDER_SAVE_PATH')
        self.fichier = os.getenv('FILE_INSTANCE')

        self.model = Model(self.model_name)
        self._load_data()
        self.data_loaded_time = tme.time()
        self._define_variables()
        self._define_constraints()
        self.constraint_variable_time = tme.time()
        self._define_objective_function()
    
    def _load_data(self):
        """Load and process input data."""
        (
            self.chantiers_df, self.machines_df, self.sillons_arrivee_df,
            self.sillons_depart_df, self.correspondances_df, self.j1, self.jours, self.first_day
        ) = add_time_reference(self.fichier)
        
        (
            self.trains, self.trains_arr, self.trains_dep, self.minutes,
            self.machines, self.machines_durees, self.minute_slots, self.chantiers
        ) = format_trains(
            self.machines_df, self.sillons_arrivee_df, self.sillons_depart_df, self.chantiers_df,
            self.j1, self.jours, self.first_day
        )
        
        self.unavailable_periods, self.start_times = unavailable_machines(self.machines_df, self.jours, self.first_day)
        self.unavailable_periods_chantiers, self.start_times_chantiers = unavailable_chantiers(self.chantiers_df, self.jours, self.first_day)
        self.trains_requis_dict = correspondance_for_depart(self.trains_dep, self.trains_arr, self.correspondances_df, self.j1)
        self.max_voies = find_max_voies(self.chantiers_df)
        print('Data loaded')

    def _define_variables(self):
        """Define model variables."""
        
        def define_decision_variables(self):
            """Define decision variables for the optimization model."""
            self.a = self.model.addVars(self.trains_arr, lb=0, ub=max(self.minutes), vtype=GRB.INTEGER, name="a")
            self.b = self.model.addVars(self.trains_dep, lb=0, ub=max(self.minutes), vtype=GRB.INTEGER, name="b")
            self.c = self.model.addVars(self.trains_dep, lb=0, ub=max(self.minutes), vtype=GRB.INTEGER, name="c")
        
        def define_auxiliary_variables(self):
            """Define auxiliary variables for the optimization model. To ensure that a,b,c are all 15 minutes."""
            self.aint = self.model.addVars(self.trains_arr, vtype=GRB.INTEGER, name="aint")
            self.bint = self.model.addVars(self.trains_dep, vtype=GRB.INTEGER, name="bint")
            self.cint = self.model.addVars(self.trains_dep, vtype=GRB.INTEGER, name="cint")

            #auxiliary varaibles for max voies occupied at any time
            self.rec_max = self.model.addVar(vtype=GRB.INTEGER, name="REC_Max_voies")
            self.for_max = self.model.addVar(vtype=GRB.INTEGER, name="FOR_Max_voies")
            self.dep_max = self.model.addVar(vtype=GRB.INTEGER, name="DEP_Max_voies")

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
            
            self.chant_d = self.model.addVars(self.trains_arr, 2, self.start_times_chantiers, vtype=GRB.BINARY, name="chant_d")
            self.chant_e = self.model.addVars(self.trains_dep, 2, self.start_times_chantiers, vtype=GRB.BINARY, name="chant_e")
            self.chant_f = self.model.addVars(self.trains_dep, 2, self.start_times_chantiers, vtype=GRB.BINARY, name="chant_f")
            
            self.rec_occup = self.model.addVars(self.trains_arr, self.minute_slots, vtype=GRB.BINARY, name="rec_occup")
            self.for_occup = self.model.addVars(self.trains, self.minute_slots, vtype=GRB.BINARY, name="for_occup")
            self.dep_occup = self.model.addVars(self.trains_dep, self.minute_slots, vtype=GRB.BINARY, name="dep_occup")

            self.rec_x = self.model.addVars(self.trains_arr, self.minute_slots, vtype=GRB.BINARY, name="rec_x")
            self.rec_y = self.model.addVars(self.trains_arr, self.minute_slots, vtype=GRB.BINARY, name="rec_y")
            self.for_x = self.model.addVars(self.trains, self.minute_slots, vtype=GRB.BINARY, name="for_x")
            self.for_y = self.model.addVars(self.trains, self.minute_slots, vtype=GRB.BINARY, name="for_y")
            self.dep_x = self.model.addVars(self.trains_dep, self.minute_slots, vtype=GRB.BINARY, name="dep_x")
            self.dep_y = self.model.addVars(self.trains_dep, self.minute_slots, vtype=GRB.BINARY, name="dep_y")

        define_decision_variables(self)
        define_auxiliary_variables(self)
        define_binary_variables(self)
        print('Variables defined')

    def _define_constraints(self):
        """Define constraints for the optimization model."""
        self.M = max(self.minutes)+1
        self.epsilon = 1
    
        def define_unavailability_machines_constraints():
            """Constraint 1.1: Ensure machines respect unavailable periods."""
            for machine, periods in self.unavailable_periods.items():
                for (start_time, end_time) in periods:        
                    # Loop through trains only once per unavailable period
                    for t in self.trains: 
                        if t[0] == 'ARR' and machine == 'DEB':
                            self.model.addConstr(self.a[t[0], t[1], t[2]] <= start_time[0] - self.epsilon + self.M * (1 - self.d[t[0], t[1], t[2], 0, start_time[0], machine]))
                            self.model.addConstr(self.a[t[0], t[1], t[2]] >= end_time[0] + self.epsilon - self.M * self.d[t[0], t[1], t[2], 0, start_time[0], machine])
                            if start_time[1] != 0:
                                self.model.addConstr(self.a[t[0], t[1], t[2]] <= start_time[1] - self.epsilon + self.M * (1 - self.d[t[0], t[1], t[2], 1,start_time[1], machine]))
                                self.model.addConstr(self.a[t[0], t[1], t[2]] >= end_time[1] + self.epsilon - self.M * self.d[t[0], t[1], t[2], 1,start_time[1], machine])
                        elif t[0] == 'DEP' and machine == 'FOR':
                            self.model.addConstr(self.b[t[0], t[1], t[2]] <= start_time[0] - self.epsilon + self.M * (1 - self.e[t[0], t[1], t[2], 0, start_time[0], machine]))
                            self.model.addConstr(self.b[t[0], t[1], t[2]] >= end_time[0] + self.epsilon - self.M * self.e[t[0], t[1], t[2], 0, start_time[0], machine])
                            if start_time[1] != 0:
                                self.model.addConstr(self.b[t[0], t[1], t[2]] <= start_time[1] - self.epsilon + self.M * (1 - self.e[t[0], t[1], t[2], 1,start_time[1], machine]))
                                self.model.addConstr(self.b[t[0], t[1], t[2]] >= end_time[1] + self.epsilon - self.M * self.e[t[0], t[1], t[2], 1,start_time[1], machine])
                        elif t[0] == 'DEP' and machine == 'DEG':
                            self.model.addConstr(self.c[t[0], t[1], t[2]] <= start_time[0] - self.epsilon + self.M * (1 - self.f[t[0], t[1], t[2], 0, start_time[0], machine]))
                            self.model.addConstr(self.c[t[0], t[1], t[2]] >= end_time[0] + self.epsilon - self.M * self.f[t[0], t[1], t[2], 0, start_time[0], machine])
                            if start_time[1] != 0:
                                self.model.addConstr(self.c[t[0], t[1], t[2]] <= start_time[1] - self.epsilon + self.M * (1 - self.f[t[0], t[1], t[2], 1,start_time[1], machine]))
                                self.model.addConstr(self.c[t[0], t[1], t[2]] >= end_time[1] + self.epsilon - self.M * self.f[t[0], t[1], t[2], 1,start_time[1], machine])

            print('1.1: Unavailability machine constraint defined')

        def define_unavailability_chantier_constraints():
            """Constraint 1.2: Ensure chantier respect unavailable periods."""
            for chantier, periods in self.unavailable_periods_chantiers.items():
                for (start_time, end_time) in periods:        
                    # Loop through trains only once per unavailable period
                    for t in self.trains: 
                        if t[0] == 'ARR' and chantier == 'WPY_REC':
                            # Machine DEB
                            self.model.addConstr(self.a[t[0], t[1], t[2]] <= start_time[0] - self.epsilon + self.M * (1 - self.chant_d[t[0], t[1], t[2], 0, start_time[0], chantier]))
                            self.model.addConstr(self.a[t[0], t[1], t[2]] >= end_time[0] + self.epsilon - self.M * self.chant_d[t[0], t[1], t[2], 0, start_time[0], chantier])
                            if start_time[1] != 0:
                                self.model.addConstr(self.a[t[0], t[1], t[2]] <= start_time[1] - self.epsilon + self.M * (1 - self.chant_d[t[0], t[1], t[2], 1, start_time[1], chantier]))
                                self.model.addConstr(self.a[t[0], t[1], t[2]] >= end_time[1] + self.epsilon - self.M * self.chant_d[t[0], t[1], t[2], 1, start_time[1], chantier])
                        
                        elif t[0] == 'DEP' and chantier == 'WPY_FOR':
                            # Machine FOR
                            self.model.addConstr(self.b[t[0], t[1], t[2]] <= start_time[0] - self.epsilon + self.M * (1 - self.chant_e[t[0], t[1], t[2], 0, start_time[0], chantier]))
                            self.model.addConstr(self.b[t[0], t[1], t[2]] >= end_time[0] + self.epsilon - self.M * self.chant_e[t[0], t[1], t[2], 0, start_time[0], chantier])
                            if start_time[1] != 0:
                                self.model.addConstr(self.b[t[0], t[1], t[2]] <= start_time[1] - self.epsilon + self.M * (1 - self.chant_e[t[0], t[1], t[2], 1, start_time[1], chantier]))
                                self.model.addConstr(self.b[t[0], t[1], t[2]] >= end_time[1] + self.epsilon - self.M * self.chant_e[t[0], t[1], t[2], 1, start_time[1], chantier])
                            
                            # Machine DEG
                            self.model.addConstr(self.c[t[0], t[1], t[2]] <= start_time[0] - self.epsilon + self.M * (1 - self.chant_f[t[0], t[1], t[2], 0, start_time[0], chantier]))
                            self.model.addConstr(self.c[t[0], t[1], t[2]] >= end_time[0] + self.epsilon - self.M * self.chant_f[t[0], t[1], t[2], 0, start_time[0], chantier])
                            if start_time[1] != 0:
                                self.model.addConstr(self.c[t[0], t[1], t[2]] <= start_time[1] - self.epsilon + self.M * (1 - self.chant_f[t[0], t[1], t[2], 1, start_time[1], chantier]))
                                self.model.addConstr(self.c[t[0], t[1], t[2]] >= end_time[1] + self.epsilon - self.M * self.chant_f[t[0], t[1], t[2], 1, start_time[1], chantier])

            print("Constraint 1.2: Unavailability chantier constraints defined")
                    

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
            """Constraint 3: Ensure 'DEB' is not used within 60 minutes after train arrival."""
            for train in self.trains:
                if train[0] == 'ARR':
                    arrival_minute = train[2]
                    self.model.addConstr(self.a[train[0],train[1],train[2]] >= arrival_minute + 60, name=f"constraint_DEB_{train[1]}")
            print('3: DEB usage delay constraint defined')

        def define_deg_time_limit_constraint():
            """Constraint 4: Ensure 'DEG' is used at most 35 minutes before train departure."""
            for train in self.trains:
                if train[0] == 'DEP':
                    departure_minute = train[2]        
                    self.model.addConstr(self.c[train[0],train[1],train[2]] <= departure_minute - 35, name=f"constraint_DEG_{train[1]}")
            print('4: DEG time limit constraint defined')

        def define_for_after_deb_constraint():
            """Constraint 5: Ensure 'FOR' starts only after all required 'DEB' processes finish."""
            for dep_train, arr_trains in self.trains_requis_dict.items():
                for arr_train in arr_trains:
                    self.model.addConstr(self.b[dep_train[0], dep_train[1], dep_train[2]] >= self.a[arr_train[0], arr_train[1], arr_train[2]] + 15, name=f"constraint_FOR_DEB_{dep_train[1]}_{arr_train[1]}")
            print('5: FOR after DEB constraint defined')

        def define_for_before_deg_constraint():
            """Constraint 6: Ensure 'FOR' is used at least 165 minutes before 'DEG'."""
            for train in self.trains_dep:
                self.model.addConstr(self.c[train[0],train[1],train[2]] >= self.b[train[0],train[1],train[2]] + 165, name=f"constraint_DEG_FOR_{train[1]}")
            print('6: FOR before DEG constraint defined')
        
        def define_task_time_slots_constraint():
            """Constraint 7: Tasks can only begin every 15 mins (h:00, h:15, h:30, h:45)."""
            for train in self.trains_arr:
                self.model.addConstr(
                    self.a[train[0], train[1], train[2]] == 15 * self.aint[train[0], train[1], train[2]],
                    name=f'constraint_creneaux_{train}'
                )

            for train in self.trains_dep:
                self.model.addConstr(
                    self.b[train[0], train[1], train[2]] == 15 * self.bint[train[0], train[1], train[2]],
                    name=f'constraint_creneaux_{train}'
                )
                self.model.addConstr(
                    self.c[train[0], train[1], train[2]] == 15 * self.cint[train[0], train[1], train[2]],
                    name=f'constraint_creneaux_{train}'
                )

            print("Constraint 7: Task time slots defined.")

        def define_REC_occupation_relation_constraints(self):
            """Constraint 8.1: Relate binary variables for occupation to the start time of each machine"""
            for minute in self.minute_slots:
                for train in self.trains_arr:
                    # Chantier REC
                    # tarr*occup <= t
                    self.model.addConstr(
                        train[2]/15*self.rec_occup[train[0],train[1],train[2], minute] <= minute,
                        name=f"rec_occup_before_{train}_{minute}"
                    )
                    # t <= (a+15)*occup + M(1-occup)
                    self.model.addConstr(
                        minute <= (self.a[train[0],train[1],train[2]]+15)/15*self.rec_occup[train[0],train[1],train[2], minute] + self.M*(1-self.rec_occup[train[0],train[1],train[2], minute]),
                        name=f"rec_occup_after_{train}_{minute}"
                    )
                    # t-tarr <= M*x
                    self.model.addConstr(
                        (minute - train[2]/15) <= self.M*self.rec_x[train[0],train[1],train[2], minute],
                        name=f"rec_occup_after_harr_{train}_{minute}"
                    )
                    # (a+15)-t <= M*y
                    self.model.addConstr(
                        (self.a[train[0],train[1],train[2]]+15)/15 - minute <= self.M*self.rec_y[train[0],train[1],train[2], minute],
                        name=f"rec_occup_before_harr_{train}_{minute}"
                    )
                    # occup >= x+y-1
                    self.model.addConstr(
                        self.rec_occup[train[0],train[1],train[2], minute] >= self.rec_x[train[0],train[1],train[2], minute] + self.rec_y[train[0],train[1],train[2], minute] - 1,
                    )
            print("8.1: Occupation variables REC related to start time defined.")
        
        def define_FOR_occupation_relation_constraints(self):
            """Constraint 8.2: Relate binary variables for occupation to the start time of each machine"""
            for minute in self.minute_slots:
                for train in self.trains_arr:
                    # Chantier FOR
                    # tarr*occup <= t
                    self.model.addConstr(
                        train[2]/15*self.for_occup[train[0],train[1],train[2], minute] <= minute,
                        name=f"for_occup_before_{train}_{minute}"
                    )
                    # t <= (a+15)*occup + M(1-occup)
                    self.model.addConstr(
                        minute <= (self.a[train[0],train[1],train[2]]+15)/15*self.for_occup[train[0],train[1],train[2], minute] + self.M*(1-self.for_occup[train[0],train[1],train[2], minute]),
                        name=f"for_occup_after_{train}_{minute}"
                    )
                    # t-tarr <= M*x
                    self.model.addConstr(
                        (minute - train[2]/15) <= self.M*self.for_x[train[0],train[1],train[2], minute],
                        name=f"for_occup_after_harr_{train}_{minute}"
                    )
                    # (a+15)-t <= M*y
                    self.model.addConstr(
                        (self.a[train[0],train[1],train[2]]+15)/15 - minute <= self.M*self.for_y[train[0],train[1],train[2], minute],
                        name=f"for_occup_before_harr_{train}_{minute}"
                    )
                    # occup >= x+y-1
                    self.model.addConstr(
                        self.for_occup[train[0],train[1],train[2], minute] >= self.for_x[train[0],train[1],train[2], minute] + self.for_y[train[0],train[1],train[2], minute] - 1,
                    )
                for train in self.trains_dep:
                    # Chantier FOR
                    # b*occup <= t
                    self.model.addConstr(
                        self.b[train[0],train[1],train[2]]/15*self.for_occup[train[0],train[1],train[2], minute] <= minute,
                        name=f"for_occup_before_{train}_{minute}"
                    )
                    # t <= (c+15)*occup + M(1-occup)
                    self.model.addConstr(
                        minute <= (self.c[train[0],train[1],train[2]]+15)/15*self.for_occup[train[0],train[1],train[2], minute] + self.M*(1-self.for_occup[train[0],train[1],train[2], minute]),
                        name=f"for_occup_after_{train}_{minute}"
                    )
                    # t-b <= M*x
                    self.model.addConstr(
                        (minute - self.b[train[0],train[1],train[2]]/15) <= self.M*self.for_x[train[0],train[1],train[2], minute],
                        name=f"for_occup_after_harr_{train}_{minute}"
                    )
                    # (c+15)-t <= M*y
                    self.model.addConstr(
                        (self.c[train[0],train[1],train[2]]+15)/15 - minute <= self.M*self.for_y[train[0],train[1],train[2], minute],
                        name=f"for_occup_before_harr_{train}_{minute}"
                    )
                    # occup >= x+y-1
                    self.model.addConstr(
                        self.for_occup[train[0],train[1],train[2], minute] >= self.for_x[train[0],train[1],train[2], minute] + self.for_y[train[0],train[1],train[2], minute] - 1,
                    )
            print("8.2: Occupation variables FOR related to start time defined.")

        def define_DEP_occupation_relation_constraints(self):
            """Constraint 8.3: Relate binary variables for occupation to the start time of each machine"""
            for minute in self.minute_slots:
                for train in self.trains_dep:
                    # Chantier DEP
                    # c*occup <= t
                    self.model.addConstr(
                        self.c[train[0],train[1],train[2]]/15*self.dep_occup[train[0],train[1],train[2], minute] <= minute,
                        name=f"dep_occup_before_{train}_{minute}"
                    )
                    # t <= tdep*occup + M(1-occup)
                    self.model.addConstr(
                        minute <= train[2]/15*self.dep_occup[train[0],train[1],train[2], minute] + self.M*(1-self.dep_occup[train[0],train[1],train[2], minute]),
                        name=f"dep_occup_after_{train}_{minute}"
                    )
                    # t-c <= M*x
                    self.model.addConstr(
                        (minute - self.c[train[0],train[1],train[2]]/15) <= self.M*self.dep_x[train[0],train[1],train[2], minute],
                        name=f"dep_occup_after_harr_{train}_{minute}"
                    )
                    # tdep-t <= M*y
                    self.model.addConstr(
                        train[2]/15 - minute <= self.M*self.dep_y[train[0],train[1],train[2], minute],
                        name=f"dep_occup_before_harr_{train}_{minute}"
                    )
                    # occup >= x+y-1
                    self.model.addConstr(
                        self.dep_occup[train[0],train[1],train[2], minute] >= self.dep_x[train[0],train[1],train[2], minute] + self.dep_y[train[0],train[1],train[2], minute] - 1,
                    )
            print("8.3: Occupation variables DEP related to start time defined.")
        
        def define_max_voies_constraint():
            """Constraint 9: Ensure that no more than max_voies are used at any time."""
            for minute in self.minute_slots:
                self.model.addConstr(
                    quicksum(self.rec_occup[train[0], train[1], train[2], minute] for train in self.trains_arr) <= self.max_voies[0],
                    name=f"max_voies_constraint_{minute}"
                )
                self.model.addConstr(
                    quicksum(self.for_occup[train[0], train[1], train[2], minute] for train in self.trains_dep) <= self.max_voies[1],
                    name=f"max_voies_constraint_{minute}"
                )
                self.model.addConstr(
                    quicksum(self.dep_occup[train[0], train[1], train[2], minute] for train in self.trains_dep) <= self.max_voies[2],
                    name=f"max_voies_constraint_{minute}"
                )
            print("9: Maximum voies constraint defined.")

        def calculate_max_voies_used():
            """Constraint 10: Calculate the maximum number of voies used."""
            for minute in self.minute_slots:
                self.model.addConstr(
                    self.rec_max >= quicksum(self.rec_occup[train[0], train[1], train[2], minute] for train in self.trains_arr),
                    name=f"rec_max_constraint_{minute}"
                )
                self.model.addConstr(
                    self.for_max >= quicksum(self.for_occup[train[0], train[1], train[2], minute] for train in self.trains),
                    name=f"for_max_constraint_{minute}"
                )
                self.model.addConstr(
                    self.dep_max >= quicksum(self.dep_occup[train[0], train[1], train[2], minute] for train in self.trains_dep),
                    name=f"dep_max_constraint_{minute}"
                )
            print("10: Maximum voies used calculated.")
                
  
        define_unavailability_machines_constraints()
        max_voies_constraint()
        calculate_max_voies_used()
        define_REC_occupation_relation_constraints(self)
        define_FOR_occupation_relation_constraints(self)
        define_DEP_occupation_relation_constraints(self)
        define_unavailability_chantier_constraints()
        define_single_train_per_machine_constraints()
        define_deb_usage_delay_constraint()
        define_deg_time_limit_constraint()
        define_for_after_deb_constraint()
        define_for_before_deg_constraint()
        define_task_time_slots_constraint()
        
        
        

        print('Constraints defined')
    
    def _define_objective_function(self):
        self.model.setObjective(self.for_max, GRB.MINIMIZE)  # Minimise taux d'occupation des voies de chantier FOR
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
            voies =[{
                'Taux max voies (%)': 100*self.rec_max.x/self.max_voies[0],
                'Nombre max voies occupées': self.rec_max.x,
                'Nombre total voies dispo': self.max_voies[0],
            },
            {
                'Taux max voies (%)': 100*self.for_max.x/self.max_voies[1],
                'Nombre max voies occupées': self.for_max.x,
                'Nombre total voies dispo': self.max_voies[1],  
            },
            {
                'Taux max voies (%)': 100*self.dep_max.x/self.max_voies[2],
                'Nombre max voies occupées': self.dep_max.x,
                'Nombre total voies dispo': self.max_voies[2],  
            }
            ]


            # Create a DataFrame from the results
            df_results = pd.DataFrame(results)
            df_voies = pd.DataFrame(voies,index =self.chantiers)
            sheet_names = ["Taches machine","Voies utilisation"]
            file_name = Path(self.fichier).stem
            #writer = pd.ExcelWriter(f'{self.results_folder_save_path}/results_{file_name}.xlsx')
            df_results.to_excel(f'{self.results_folder_save_path}/results_{file_name}.xlsx',sheet_name=sheet_names[0], index=False)
            df_voies.to_excel(f'{self.results_folder_save_path}/results_{file_name}_voies.xlsx',sheet_name=sheet_names[1], index=True)
            #df_voies.to_excel(writer, sheet_name=sheet_names[1], index=False)
            print(f'Results saved to {self.results_folder_save_path}/results_{file_name}.xlsx')

            return df_results
        else:
            print("No optimal solution found")
            self.model.computeIIS()
            self.model.write('outputs/models/infeasible.ilp')
            return None
        
    def run_optimization(self):
        """Run the full optimization process."""
        self.optimize()
        self.optimisation_time = tme.time()
        self.save_model()
        df_results = self.get_results()
        print(f'Time taken for: Data Loading = {self.data_loaded_time-self.start_program_time}s, Variables and Constraints = {self.constraint_variable_time-self.data_loaded_time}s, Optimisation = {self.optimisation_time-self.constraint_variable_time}s')
        return df_results
