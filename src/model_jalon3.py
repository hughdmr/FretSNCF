from gurobipy import Model, GRB, quicksum
import pandas as pd
import numpy as np
from utils.utils_data import (
    format_trains, add_time_reference, unavailable_machines, correspondance_for_depart, unavailable_chantiers, find_max_voies, format_taches_humaines
)
from utils.utils_date import minute_to_date2
from pathlib import Path
from dotenv import load_dotenv
import os
import time as tme

class ModelJalon3:
    def __init__(self):
        """Initialize the optimization model."""
        self.start_program_time = tme.time()
        load_dotenv(override=True)
        self.model_name = os.getenv('MODEL_JALON1_NAME')
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
            self.sillons_depart_df, self.correspondances_df, self.taches_humaines_df, self.roulements_agents_df,
            self.j1, self.jours, self.first_day
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
        self.arr_taches, self.dep_taches, self.envelopes_agents, self.nombre_agents, self.max_agents = format_taches_humaines(self.taches_humaines_df, self.roulements_agents_df, self.jours, self.first_day, self.minute_slots)
        self.arr_orders = np.array(self.arr_taches[:,0]).astype(int)
        self.dep_orders = np.array(self.dep_taches[:,0]).astype(int)
        self.arr_durees = np.array(self.arr_taches[:,1]).astype(int)
        self.dep_durees = np.array(self.dep_taches[:,1]).astype(int)
        self.orders = np.concatenate((self.arr_orders, self.dep_orders))
        print('Data loaded')

    def _define_variables(self):
        """Define model variables."""
        
        def define_decision_variables(self):
            """Define decision variables for the optimization model."""
            self.a = self.model.addVars(self.trains_arr, lb=0, ub=max(self.minutes), vtype=GRB.INTEGER, name="a")
            self.b = self.model.addVars(self.trains_dep, lb=0, ub=max(self.minutes), vtype=GRB.INTEGER, name="b")
            self.c = self.model.addVars(self.trains_dep, lb=0, ub=max(self.minutes), vtype=GRB.INTEGER, name="c")

            self.th_arr = self.model.addVars(self.trains_arr, self.arr_orders, lb=0, ub=max(self.minutes), vtype=GRB.INTEGER, name="th_arr")
            self.th_dep = self.model.addVars(self.trains_dep, self.dep_orders, lb=0, ub=max(self.minutes), vtype=GRB.INTEGER, name="th_dep")

            # 1 if task assigned to envelope, 0 if not; access using the nb of the envelope as defined in envelopes_agents
            self.envelope_taches_REC = self.model.addVars(len(self.envelopes_agents['roulement_reception']),self.trains_arr,self.arr_orders, vtype=GRB.BINARY, name="envelope_taches_REC")
            self.envelope_taches_FOR = self.model.addVars(len(self.envelopes_agents['roulement_formation']),self.trains_dep,self.dep_orders, vtype=GRB.BINARY, name="envelope_taches_FOR")
            self.envelope_taches_DEP = self.model.addVars(len(self.envelopes_agents['roulement_depart']),self.trains_dep,self.dep_orders, vtype=GRB.BINARY, name="envelope_taches_DEP")
            self.envelope_taches_REC_DEP = self.model.addVars(len(self.envelopes_agents['roulement_reception_depart']),self.trains,self.dep_orders, vtype=GRB.BINARY, name="envelope_taches_REC_DEP")
            self.envelope_taches_FOR_DEP = self.model.addVars(len(self.envelopes_agents['roulement_formation_depart']),self.trains,self.dep_orders, vtype=GRB.BINARY, name="envelope_taches_FOR_DEP")

            # 1 if envelope used, 0 if not
            self.envelope_used_REC = self.model.addVars(len(self.envelopes_agents['roulement_reception']), vtype=GRB.BINARY, name="envelope_used_REC")
            self.envelope_used_FOR = self.model.addVars(len(self.envelopes_agents['roulement_formation']), vtype=GRB.BINARY, name="envelope_used_FOR")
            self.envelope_used_DEP = self.model.addVars(len(self.envelopes_agents['roulement_depart']), vtype=GRB.BINARY, name="envelope_used_DEP")
            self.envelope_used_REC_DEP = self.model.addVars(len(self.envelopes_agents['roulement_reception_depart']), vtype=GRB.BINARY, name="envelope_used_REC_DEP")
            self.envelope_used_FOR_DEP = self.model.addVars(len(self.envelopes_agents['roulement_formation_depart']), vtype=GRB.BINARY, name="envelope_used_FOR_DEP")
            self.envelope_used_total = self.model.addVar(vtype=GRB.INTEGER, name="envelope_used_total")
        
        def define_auxiliary_variables(self):
            """Define auxiliary variables for the optimization model. To ensure that tasks are only every 15 minutes."""
            self.th_arr_int = self.model.addVars(self.trains_arr,self.arr_orders, vtype=GRB.INTEGER, name="aint")
            self.th_dep_int = self.model.addVars(self.trains_dep,self.dep_orders, vtype=GRB.INTEGER, name="bint")
            # self.cint = self.model.addVars(self.trains_dep, vtype=GRB.INTEGER, name="cint")

            #auxiliary varaibles for max voies occupied at any time
            self.rec_max = self.model.addVar(vtype=GRB.INTEGER, name="REC_Max_voies")
            self.for_max = self.model.addVar(vtype=GRB.INTEGER, name="FOR_Max_voies")
            self.dep_max = self.model.addVar(vtype=GRB.INTEGER, name="DEP_Max_voies")

            # check if task is in progress for every minute
            self.task_in_progress_arr = self.model.addVars(self.trains_arr, self.arr_orders, self.minute_slots, vtype=GRB.BINARY, name="task_in_progress_arr")
            self.task_in_progress_dep = self.model.addVars(self.trains_dep, self.dep_orders, self.minute_slots, vtype=GRB.BINARY, name="task_in_progress_dep")

            # simulaneous tasks for every minute
            self.simulaneous_tasks_arr = self.model.addVars(self.minute_slots, vtype=GRB.BINARY, name="simulaneous_tasks_arr")
            self.simulaneous_tasks_dep = self.model.addVars(self.minute_slots, vtype=GRB.BINARY, name="simulaneous_tasks_dep")

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

            self.th_arr_unavail = self.model.addVars(self.trains_arr, self.arr_orders, self.start_times_chantiers, 2, vtype=GRB.BINARY, name="th_arr_unavail")
            self.th_dep_unavail = self.model.addVars(self.trains_dep, self.dep_orders, self.start_times_chantiers, 2, vtype=GRB.BINARY, name="th_dep_unavail")

            self.envelope_taches_REC_x = self.model.addVars(len(self.envelopes_agents['roulement_reception']),self.trains_arr,self.arr_orders, vtype=GRB.BINARY, name="envelope_taches_REC")
            self.envelope_taches_REC_y = self.model.addVars(len(self.envelopes_agents['roulement_reception']),self.trains_arr,self.arr_orders, vtype=GRB.BINARY, name="envelope_taches_REC")
            self.envelope_taches_FOR_x = self.model.addVars(len(self.envelopes_agents['roulement_formation']),self.trains_dep,self.dep_orders, vtype=GRB.BINARY, name="envelope_taches_FOR")
            self.envelope_taches_FOR_y = self.model.addVars(len(self.envelopes_agents['roulement_formation']),self.trains_dep,self.dep_orders, vtype=GRB.BINARY, name="envelope_taches_FOR")
            self.envelope_taches_DEP_x = self.model.addVars(len(self.envelopes_agents['roulement_depart']),self.trains_dep,self.dep_orders, vtype=GRB.BINARY, name="envelope_taches_DEP")
            self.envelope_taches_DEP_y = self.model.addVars(len(self.envelopes_agents['roulement_depart']),self.trains_dep,self.dep_orders, vtype=GRB.BINARY, name="envelope_taches_DEP")
            self.envelope_taches_REC_DEP_x = self.model.addVars(len(self.envelopes_agents['roulement_reception_depart']),self.trains,self.dep_orders, vtype=GRB.BINARY, name="envelope_taches_REC_DEP")
            self.envelope_taches_REC_DEP_y = self.model.addVars(len(self.envelopes_agents['roulement_reception_depart']),self.trains,self.dep_orders, vtype=GRB.BINARY, name="envelope_taches_REC_DEP")
            self.envelope_taches_FOR_DEP_x = self.model.addVars(len(self.envelopes_agents['roulement_formation_depart']),self.trains,self.dep_orders, vtype=GRB.BINARY, name="envelope_taches_FOR_DEP")
            self.envelope_taches_FOR_DEP_y = self.model.addVars(len(self.envelopes_agents['roulement_formation_depart']),self.trains,self.dep_orders, vtype=GRB.BINARY, name="envelope_taches_FOR_DEP")

            

            self.task_in_progress_arr_x = self.model.addVars(self.trains_arr, self.arr_orders, self.minute_slots, vtype=GRB.BINARY, name="task_in_progress_arr_x")
            self.task_in_progress_arr_y = self.model.addVars(self.trains_arr, self.arr_orders, self.minute_slots, vtype=GRB.BINARY, name="task_in_progress_arr_y")
            self.task_in_progress_dep_x = self.model.addVars(self.trains_dep, self.dep_orders, self.minute_slots, vtype=GRB.BINARY, name="task_in_progress_dep_x")
            self.task_in_progress_dep_y = self.model.addVars(self.trains_dep, self.dep_orders, self.minute_slots, vtype=GRB.BINARY, name="task_in_progress_dep_y")

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
                            for task in self.arr_taches:
                                self.model.addConstr(self.th_arr[t[0],t[1],t[2],task[0]] + task[1] <= start_time[0] - self.epsilon + self.M * (1 - self.th_arr_unavail[t[0],t[1],t[2],task[0],start_time[0],chantier,0]))
                                self.model.addConstr(self.th_arr[t[0],t[1],t[2],task[0]] >= end_time[0] + self.epsilon - self.M * self.th_arr_unavail[t[0],t[1],t[2],task[0],start_time[0],chantier,0])
                            if start_time[1] != 0:
                                self.model.addConstr(self.a[t[0], t[1], t[2]] <= start_time[1] - self.epsilon + self.M * (1 - self.chant_d[t[0], t[1], t[2], 1, start_time[1], chantier]))
                                self.model.addConstr(self.a[t[0], t[1], t[2]] >= end_time[1] + self.epsilon - self.M * self.chant_d[t[0], t[1], t[2], 1, start_time[1], chantier])
                                for task in self.arr_taches:
                                    self.model.addConstr(self.th_arr[t[0],t[1],t[2],task[0]] + task[1] <= start_time[0] - self.epsilon + self.M * (1 - self.th_arr_unavail[t[0],t[1],t[2],task[0],start_time[0],chantier,1]))
                                    self.model.addConstr(self.th_arr[t[0],t[1],t[2],task[0]] >= end_time[0] + self.epsilon - self.M * self.th_arr_unavail[t[0],t[1],t[2],task[0],start_time[0],chantier,1])
                        
                        elif t[0] == 'DEP' and chantier == 'WPY_FOR':
                            # Machine FOR
                            self.model.addConstr(self.b[t[0], t[1], t[2]] <= start_time[0] - self.epsilon + self.M * (1 - self.chant_e[t[0], t[1], t[2], 0, start_time[0], chantier]))
                            self.model.addConstr(self.b[t[0], t[1], t[2]] >= end_time[0] + self.epsilon - self.M * self.chant_e[t[0], t[1], t[2], 0, start_time[0], chantier])
                            for task in self.dep_taches[:-1]:
                                self.model.addConstr(self.th_dep[t[0],t[1],t[2],int(task[0])] + int(task[1]) <= start_time[0] - self.epsilon + self.M * (1 - self.th_dep_unavail[t[0],t[1],t[2],int(task[0]),start_time[0],chantier,0]))
                                self.model.addConstr(self.th_dep[t[0],t[1],t[2],int(task[0])] >= end_time[0] + self.epsilon - self.M * self.th_dep_unavail[t[0],t[1],t[2],int(task[0]),start_time[0],chantier,0])
                            if start_time[1] != 0:
                                self.model.addConstr(self.b[t[0], t[1], t[2]] <= start_time[1] - self.epsilon + self.M * (1 - self.chant_e[t[0], t[1], t[2], 1, start_time[1], chantier]))
                                self.model.addConstr(self.b[t[0], t[1], t[2]] >= end_time[1] + self.epsilon - self.M * self.chant_e[t[0], t[1], t[2], 1, start_time[1], chantier])
                                for task in self.dep_taches[:-1]:
                                    self.model.addConstr(self.th_dep[t[0],t[1],t[2],int(task[0])] + int(task[1]) <= start_time[0] - self.epsilon + self.M * (1 - self.th_dep_unavail[t[0],t[1],t[2],int(task[0]),start_time[0],chantier,1]))
                                    self.model.addConstr(self.th_dep[t[0],t[1],t[2],int(task[0])] >= end_time[0] + self.epsilon - self.M * self.th_dep_unavail[t[0],t[1],t[2],int(task[0]),start_time[0],chantier,1])
                            
                            # Machine DEG
                            self.model.addConstr(self.c[t[0], t[1], t[2]] <= start_time[0] - self.epsilon + self.M * (1 - self.chant_f[t[0], t[1], t[2], 0, start_time[0], chantier]))
                            self.model.addConstr(self.c[t[0], t[1], t[2]] >= end_time[0] + self.epsilon - self.M * self.chant_f[t[0], t[1], t[2], 0, start_time[0], chantier])
                            task = self.dep_taches[-1]
                            self.model.addConstr(self.th_dep[t[0],t[1],t[2],int(task[0])] + int(task[1]) <= start_time[0] - self.epsilon + self.M * (1 - self.th_dep_unavail[t[0],t[1],t[2],int(task[0]),start_time[0],chantier,0]))
                            self.model.addConstr(self.th_dep[t[0],t[1],t[2],int(task[0])] >= end_time[0] + self.epsilon - self.M * self.th_dep_unavail[t[0],t[1],t[2],int(task[0]),start_time[0],chantier,0])

                            if start_time[1] != 0:
                                self.model.addConstr(self.c[t[0], t[1], t[2]] <= start_time[1] - self.epsilon + self.M * (1 - self.chant_f[t[0], t[1], t[2], 1, start_time[1], chantier]))
                                self.model.addConstr(self.c[t[0], t[1], t[2]] >= end_time[1] + self.epsilon - self.M * self.chant_f[t[0], t[1], t[2], 1, start_time[1], chantier])
                                task = self.dep_taches[-1]
                                self.model.addConstr(self.th_dep[t[0],t[1],t[2],int(task[0])] + int(task[1]) <= start_time[0] - self.epsilon + self.M * (1 - self.th_dep_unavail[t[0],t[1],t[2],int(task[0]),start_time[0],chantier,1]))
                                self.model.addConstr(self.th_dep[t[0],t[1],t[2],int(task[0])] >= end_time[0] + self.epsilon - self.M * self.th_dep_unavail[t[0],t[1],t[2],int(task[0]),start_time[0],chantier,1])

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


        # def define_deb_usage_delay_constraint():
        #     """Constraint 3: Ensure 'DEB' is not used within 60 minutes after train arrival."""
        #     for train in self.trains:
        #         if train[0] == 'ARR':
        #             arrival_minute = train[2]
        #             self.model.addConstr(self.a[train[0],train[1],train[2]] >= arrival_minute + 60, name=f"constraint_DEB_{train[1]}")
        #     print('3: DEB usage delay constraint defined')

        # def define_deg_time_limit_constraint():
        #     """Constraint 4: Ensure 'DEG' is used at most 35 minutes before train departure."""
        #     for train in self.trains:
        #         if train[0] == 'DEP':
        #             departure_minute = train[2]        
        #             self.model.addConstr(self.c[train[0],train[1],train[2]] <= departure_minute - 35, name=f"constraint_DEG_{train[1]}")
        #     print('4: DEG time limit constraint defined')

        def define_for_after_deb_constraint():
            """Constraint 5: Ensure 'FOR' starts only after all required 'DEB' processes finish."""
            for dep_train, arr_trains in self.trains_requis_dict.items():
                for arr_train in arr_trains:
                    self.model.addConstr(self.b[dep_train[0], dep_train[1], dep_train[2]] >= self.a[arr_train[0], arr_train[1], arr_train[2]] + 15, name=f"constraint_FOR_DEB_{dep_train[1]}_{arr_train[1]}")
            print('5: FOR after DEB constraint defined')

        # def define_for_before_deg_constraint():
        #     """Constraint 6: Ensure 'FOR' is used at least 165 minutes before 'DEG'."""
        #     for train in self.trains_dep:
        #         self.model.addConstr(self.c[train[0],train[1],train[2]] >= self.b[train[0],train[1],train[2]] + 165, name=f"constraint_DEG_FOR_{train[1]}")
        #     print('6: FOR before DEG constraint defined')
        
        def define_task_time_slots_constraint():
            """Constraint 7: Tasks can only begin every 15 mins (h:00, h:15, h:30, h:45)."""
            for train in self.trains_arr:
                for task in self.arr_taches:
                    self.model.addConstr(
                        self.th_arr[train[0], train[1], train[2], int(task[0])] == 15 * self.th_arr_int[train[0], train[1], train[2], int(task[0])],
                        name=f'constraint_creneaux_{train}'
                    )
                # self.model.addConstr(
                #     self.th_arr[train[0], train[1], train[2],] == 15 * self.aint[train[0], train[1], train[2]],
                #     name=f'constraint_creneaux_{train}'
                # )
            for train in self.trains_dep:
                for task in self.dep_taches:
                    self.model.addConstr(
                        self.th_dep[train[0], train[1], train[2], int(task[0])] == 15 * self.th_dep_int[train[0], train[1], train[2], int(task[0])],
                        name=f'constraint_creneaux_{train}'
                    )
                # self.model.addConstr(
                #     self.b[train[0], train[1], train[2]] == 15 * self.bint[train[0], train[1], train[2]],
                #     name=f'constraint_creneaux_{train}'
                # )
                # self.model.addConstr(
                #     self.c[train[0], train[1], train[2]] == 15 * self.cint[train[0], train[1], train[2]],
                #     name=f'constraint_creneaux_{train}'
                # )
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
        
        def max_voies_constraint(self):
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

        def calculate_max_voies_used(self):
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
        

        def define_arr_tri_constraint():
            """Constraint 11: Ensure 'prép tri' starts more than 15 minutes after reception"""
            for train in self.trains_arr:
                self.model.addConstr(self.th_arr[train[0],train[1],train[2],2] >= self.th_arr[train[0], train[1], train[2],1] + self.arr_durees[0], name=f"constraint_arr_tri_{train}")
            print('11: Reception before Prep tri constraint defined')

        def define_tri_deb_constraint():
            """Constraint 12: Ensure DEB starts at least 45 minutes after tri."""
            for train in self.trains_arr:
                self.model.addConstr(self.th_arr[train[0],train[1],train[2],3] >= self.th_arr[train[0], train[1], train[2],2] + self.arr_durees[1], name=f"constraint_tri_deb_{train}")
            print('12: Tri before DEB constraint defined')
        
        def define_DEB_parallel_constraint():
            """Constraint 13: Ensure DEB human and machine parellelisation."""
            for train in self.trains_arr:
                self.model.addConstr(self.th_arr[train[0],train[1],train[2],3] == self.a[train[0], train[1], train[2]], name=f"constraint_deb_parallel_{train}")
            print('13: DEB parallel constraint defined')

        def define_FOR_parallel_constraint():
            """Constraint 14: Ensure FOR human and machine parellelisation."""
            for train in self.trains_dep:
                self.model.addConstr(self.th_dep[train[0],train[1],train[2],1] == self.b[train[0], train[1], train[2]], name=f"constraint_for_parallel_{train}")
            print('14: FOR parallel constraint defined')

        def define_attelage_FOR_constraint():
            """Constraint 15: Ensure attelage véhicules takes place at least 15 minutes after FOR."""
            for train in self.trains_dep:
                self.model.addConstr(self.th_dep[train[0],train[1],train[2],2] >= self.th_dep[train[0], train[1], train[2],1] + self.dep_durees[0], name=f"constraint_attelage_FOR_{train}")
            print('15: Attelage FOR constraint defined')
        
        def define_DEG_attelage_constraint():
            """Constraint 16: Ensure DEG takes place at least 150 minutes after attelage véhicules."""
            for train in self.trains_dep:
                self.model.addConstr(self.th_dep[train[0],train[1],train[2],3] >= self.th_dep[train[0], train[1], train[2],2] + self.dep_durees[1], name=f"constraint_DEG_attelage_{train}")
            print('16: DEG attelage constraint defined')
        
        def define_DEG_parallel_constraint():
            """Constraint 17: Ensure DEG human and machine parellelisation."""
            for train in self.trains_dep:
                self.model.addConstr(self.th_dep[train[0],train[1],train[2],3] == self.c[train[0], train[1], train[2]], name=f"constraint_deg_parallel_{train}")
            print('17: DEG parallel constraint defined')
        
        def define_frein_DEG_constraint():
            """Constraint 18: Ensure essai frein takes place at least 15 minutes after DEG."""
            for train in self.trains_dep:
                self.model.addConstr(self.th_dep[train[0],train[1],train[2],4] >= self.th_dep[train[0], train[1], train[2],3] + self.dep_durees[2], name=f"constraint_frein_DEG_{train}")
            print('18: Frein DEG constraint defined')

        def define_arr_start_constraint():
            """Constraint 19: Ensure arrivée réception starts after train arrival."""
            for train in self.trains_arr:
                self.model.addConstr(self.th_arr[train[0],train[1],train[2],1] >= train[2], name=f"constraint_arr_start_{train}")
            print('19: Reception after arrival constraint defined')
        
        def define_dep_final_constraint():
            """Constraint 20: Ensure essai frein finishes before train departure."""
            for train in self.trains_dep:
                self.model.addConstr(self.th_dep[train[0],train[1],train[2],4] + self.dep_durees[3] <= train[2], name=f"constraint_dep_finish_{train}")
            print('19: Frein before departure constraint defined')


        #self.envelope_taches_REC = self.model.addVars(len(self.envelopes_agents['roulement_reception']), vtype=GRB.BINARY, name="envelope_taches_REC")
        def define_envelope_taches_REC_relation_constraints(self):
            """Constraint 21.1: Assign tasks to shifts for roulement_reception. If (start of envelope) <= t (start of task) <= (end of envelope), then envelope_tache = 1."""
            for i, (start_time,end_time) in enumerate(self.envelopes_agents['roulement_reception']):
                for train in self.trains_arr:
                    for order in self.arr_orders:
                        order = int(order)
                        # Chantier REC
                        # start_time*envelope_tache <= task
                        self.model.addConstr(
                            start_time*self.envelope_taches_REC[i,train[0],train[1],train[2],order] <= self.th_arr[train[0],train[1],train[2],order],
                            name=f"roul_rec_task_after_{start_time}_{train}_{order}"
                        )
                        # task <= end_time*envelope_tache + M(1-envelope_tache)
                        self.model.addConstr(
                            self.th_arr[train[0],train[1],train[2],order] <= (end_time)*self.envelope_taches_REC[i,train[0],train[1],train[2],order] + self.M*(1-self.envelope_taches_REC[i,train[0],train[1],train[2],order]),
                            name=f"roul_rec_task_before_{end_time}_{train}_{order}"
                        )
                        # task-start_time <= M*x
                        self.model.addConstr(
                            (self.th_arr[train[0],train[1],train[2],order] - start_time) <= self.M*self.envelope_taches_REC_x[i,train[0],train[1],train[2],order],
                            name=f"roul_rec_x_{train}_{order}"
                        )
                        # end_time-task <= M*y
                        self.model.addConstr(
                            end_time - self.th_arr[train[0],train[1],train[2],order] <= self.M*self.envelope_taches_REC_y[i,train[0],train[1],train[2],order],
                            name=f"roul_rec_y_{train}_{order}"
                        )
                        # envelope_tache >= x+y-1
                        self.model.addConstr(
                            self.envelope_taches_REC[i,train[0],train[1],train[2],order] >= self.envelope_taches_REC_x[i,train[0],train[1],train[2],order] + self.envelope_taches_REC_y[i,train[0],train[1],train[2],order] - 1,
                            name=f"roul_rec_envelope_{start_time}_{train}_{order}"
                        )
            print("21.1: Envelope taches roulement_reception relation constraints defined.")

        def define_envelope_taches_FOR_relation_constraints(self):
            """Constraint 21.2: Assign tasks to shifts for roulement_formation. If (start of envelope) <= t (start of task) <= (end of envelope), then envelope_tache = 1."""
            for i, (start_time,end_time) in enumerate(self.envelopes_agents['roulement_formation']):
                for train in self.trains_dep:
                    for order in self.dep_orders[:-1]:
                        order = int(order)
                        # Chantier REC
                        # start_time*envelope_tache <= task
                        self.model.addConstr(
                            start_time*self.envelope_taches_FOR[i,train[0],train[1],train[2],order] <= self.th_dep[train[0],train[1],train[2],order],
                            name=f"roul_for_task_after_{start_time}_{train}_{order}"
                        )
                        # task <= end_time*envelope_tache + M(1-envelope_tache)
                        self.model.addConstr(
                            self.th_dep[train[0],train[1],train[2],order] <= (end_time)*self.envelope_taches_FOR[i,train[0],train[1],train[2],order] + self.M*(1-self.envelope_taches_FOR[i,train[0],train[1],train[2],order]),
                            name=f"roul_for_task_before_{end_time}_{train}_{order}"
                        )
                        # task-start_time <= M*x
                        self.model.addConstr(
                            (self.th_dep[train[0],train[1],train[2],order] - start_time) <= self.M*self.envelope_taches_FOR_x[i,train[0],train[1],train[2],order],
                            name=f"roul_for_x_{train}_{order}"
                        )
                        # end_time-task <= M*y
                        self.model.addConstr(
                            end_time - self.th_dep[train[0],train[1],train[2],order] <= self.M*self.envelope_taches_FOR_y[i,train[0],train[1],train[2],order],
                            name=f"roul_for_y_{train}_{order}"
                        )
                        # envelope_tache >= x+y-1
                        self.model.addConstr(
                            self.envelope_taches_FOR[i,train[0],train[1],train[2],order] >= self.envelope_taches_FOR_x[i,train[0],train[1],train[2],order] + self.envelope_taches_FOR_y[i,train[0],train[1],train[2],order] - 1,
                            name=f"roul_for_envelope_{start_time}_{train}_{order}"
                        )
            print("21.2: Envelope taches roulement_formation relation constraints defined.")
        
        def define_envelope_taches_DEP_relation_constraints(self):
            """Constraint 21.3: Assign tasks to shifts for roulement_depart. If (start of envelope) <= t (start of task) <= (end of envelope), then envelope_tache = 1."""
            for i, (start_time,end_time) in enumerate(self.envelopes_agents['roulement_depart']):
                for train in self.trains_dep:
                    order = 4
                    # Chantier REC
                    # start_time*envelope_tache <= task
                    self.model.addConstr(
                        start_time*self.envelope_taches_DEP[i,train[0],train[1],train[2],order] <= self.th_dep[train[0],train[1],train[2],order],
                        name=f"roul_dep_task_after_{start_time}_{train}_{order}"
                    )
                    # task <= end_time*envelope_tache + M(1-envelope_tache)
                    self.model.addConstr(
                        self.th_dep[train[0],train[1],train[2],order] <= (end_time)*self.envelope_taches_DEP[i,train[0],train[1],train[2],order] + self.M*(1-self.envelope_taches_DEP[i,train[0],train[1],train[2],order]),
                        name=f"roul_dep_task_before_{end_time}_{train}_{order}"
                    )
                    # task-start_time <= M*x
                    self.model.addConstr(
                        (self.th_dep[train[0],train[1],train[2],order] - start_time) <= self.M*self.envelope_taches_DEP_x[i,train[0],train[1],train[2],order],
                        name=f"roul_dep_x_{train}_{order}"
                    )
                    # end_time-task <= M*y
                    self.model.addConstr(
                        end_time - self.th_dep[train[0],train[1],train[2],order] <= self.M*self.envelope_taches_DEP_y[i,train[0],train[1],train[2],order],
                        name=f"roul_dep_y_{train}_{order}"
                    )
                    # envelope_tache >= x+y-1
                    self.model.addConstr(
                        self.envelope_taches_DEP[i,train[0],train[1],train[2],order] >= self.envelope_taches_DEP_x[i,train[0],train[1],train[2],order] + self.envelope_taches_DEP_y[i,train[0],train[1],train[2],order] - 1,
                        name=f"roul_dep_envelope_{start_time}_{train}_{order}"
                    )
            print("21.3: Envelope taches roulement_depart relation constraints defined.")
        
        def define_envelope_taches_REC_DEP_relation_constraints(self):
            """Constraint 21.4: Assign tasks to shifts for roulement_reception_depart. If (start of envelope) <= t (start of task) <= (end of envelope), then envelope_tache = 1."""
            for i, (start_time,end_time) in enumerate(self.envelopes_agents['roulement_reception_depart']):
                for train in self.trains:
                    for order in self.dep_orders:
                        order = int(order)
                        if train[0] == 'ARR' and order == 4:
                            continue
                        elif train[0] == 'DEP' and (order == 1 or order == 2 or order == 3):
                            continue
                        if train[0] == 'ARR':
                            task = self.th_arr[train[0],train[1],train[2],order]
                        elif train[0] == 'DEP':
                            task = self.th_dep[train[0],train[1],train[2],order]
                        envelope_tache = self.envelope_taches_REC_DEP[i,train[0],train[1],train[2],order]
                        # Chantier REC
                        # start_time*envelope_tache <= task
                        self.model.addConstr(
                            start_time*envelope_tache <= task,
                            name=f"roul_rec_dep_task_after_{start_time}_{train}_{order}"
                        )
                        # task <= end_time*envelope_tache + M(1-envelope_tache)
                        self.model.addConstr(
                            task <= (end_time)*envelope_tache + self.M*(1-envelope_tache),
                            name=f"roul_rec_dep_task_before_{end_time}_{train}_{order}"
                        )
                        # task-start_time <= M*x
                        self.model.addConstr(
                            (task - start_time) <= self.M*self.envelope_taches_REC_DEP_x[i,train[0],train[1],train[2],order],
                            name=f"roul_rec_dep_x_{train}_{order}"
                        )
                        # end_time-task <= M*y
                        self.model.addConstr(
                            end_time - task <= self.M*self.envelope_taches_REC_DEP_y[i,train[0],train[1],train[2],order],
                            name=f"roul_rec_dep_y_{train}_{order}"
                        )
                        # envelope_tache >= x+y-1
                        self.model.addConstr(
                            envelope_tache >= self.envelope_taches_REC_DEP_x[i,train[0],train[1],train[2],order] + self.envelope_taches_REC_DEP_y[i,train[0],train[1],train[2],order] - 1,
                            name=f"roul_rec_dep_envelope_{start_time}_{train}_{order}"
                        )
            print("21.4: Envelope taches roulement_reception_depart relation constraints defined.")

        def define_envelope_taches_FOR_DEP_relation_constraints(self):
            """Constraint 21.5: Assign tasks to shifts for roulement_formation_depart. If (start of envelope) <= t (start of task) <= (end of envelope), then envelope_tache = 1."""
            for i, (start_time,end_time) in enumerate(self.envelopes_agents['roulement_formation_depart']):
                for train in self.trains_dep:
                    for order in self.dep_orders:
                        order = int(order)
                        task = self.th_dep[train[0],train[1],train[2],order]
                        envelope_tache = self.envelope_taches_FOR_DEP[i,train[0],train[1],train[2],order]
                        # Chantier REC
                        # start_time*envelope_tache <= task
                        self.model.addConstr(
                            start_time*envelope_tache <= task,
                            name=f"roul_for_dep_task_after_{start_time}_{train}_{order}"
                        )
                        # task <= end_time*envelope_tache + M(1-envelope_tache)
                        self.model.addConstr(
                            task <= (end_time)*envelope_tache + self.M*(1-envelope_tache),
                            name=f"roul_for_dep_task_before_{end_time}_{train}_{order}"
                        )
                        # task-start_time <= M*x
                        self.model.addConstr(
                            (task - start_time) <= self.M*self.envelope_taches_FOR_DEP_x[i,train[0],train[1],train[2],order],
                            name=f"roul_for_dep_x_{train}_{order}"
                        )
                        # end_time-task <= M*y
                        self.model.addConstr(
                            end_time - task <= self.M*self.envelope_taches_FOR_DEP_y[i,train[0],train[1],train[2],order],
                            name=f"roul_for_dep_y_{train}_{order}"
                        )
                        # envelope_tache >= x+y-1
                        self.model.addConstr(
                            envelope_tache >= self.envelope_taches_FOR_DEP_x[i,train[0],train[1],train[2],order] + self.envelope_taches_FOR_DEP_y[i,train[0],train[1],train[2],order] - 1,
                            name=f"roul_for_dep_envelope_{start_time}_{train}_{order}"
                        )
            print("21.5: Envelope taches roulement_formation_depart relation constraints defined.")
        
        def define_task_in_progress_rec_relation_constraint(self):
            """22.1: REC For every minute and task, set task_in_progress to 1 if task is in progress at that minute."""  
            for minute in self.minute_slots:
                for train in self.trains_arr:
                    for order in self.arr_orders:
                        # Chantier REC
                        start_time = self.th_arr[train[0],train[1],train[2],order]
                        end_time = self.th_arr[train[0],train[1],train[2],order] + self.arr_durees[order-1]
                        task_in_progress = self.task_in_progress_arr[train[0],train[1],train[2],order,minute]
                        # th*in_progress <= minute
                        self.model.addConstr(
                            start_time*task_in_progress <= minute,
                            name=f"task_in_prog_rec_1_{minute}_{train}_{order}"
                        )
                        # minute <= th+duree*in_progress + M(1-in_progress)
                        self.model.addConstr(
                            minute <= (end_time)*task_in_progress + self.M*(1-task_in_progress),
                            name=f"task_in_prog_rec_2_{minute}_{train}_{order}"
                        )
                        # minute-th <= M*x
                        self.model.addConstr(
                            (minute - end_time) <= self.M*self.task_in_progress_arr_x[train[0],train[1],train[2],order,minute],
                            name=f"task_in_prog_rec_3_{minute}_{train}_{order}"
                        )
                        # end_time-task <= M*y
                        self.model.addConstr(
                            end_time - minute <= self.M*self.task_in_progress_arr_y[train[0],train[1],train[2],order,minute],
                            name=f"task_in_prog_rec_4_{minute}_{train}_{order}"
                        )
                        # in_progress >= x+y-1
                        self.model.addConstr(
                            task_in_progress >= self.task_in_progress_arr_x[train[0],train[1],train[2],order,minute] + self.task_in_progress_arr_y[train[0],train[1],train[2],order,minute] - 1,
                            name=f"task_in_prog_rec_5_{minute}_{train}_{order}"
                        )
            print("23.1: Task in progress relation REC constraint defined.")

        def define_task_in_progress_for_relation_constraint(self):
            """22.2: FOR For every minute and task, set task_in_progress to 1 if task is in progress at that minute."""  
            for minute in self.minute_slots:
                for train in self.trains_dep:
                    for order in self.dep_orders[:-1]:
                        # Chantier FOR
                        start_time = self.th_dep[train[0],train[1],train[2],order]
                        end_time = self.th_dep[train[0],train[1],train[2],order] + self.dep_durees[order-1]
                        task_in_progress = self.task_in_progress_dep[train[0],train[1],train[2],order,minute]
                        # th*in_progress <= minute
                        self.model.addConstr(
                            start_time*task_in_progress <= minute,
                            name=f"task_in_prog_for_1_{minute}_{train}_{order}"
                        )
                        # minute <= th+duree*in_progress + M(1-in_progress)
                        self.model.addConstr(
                            minute <= (end_time)*task_in_progress + self.M*(1-task_in_progress),
                            name=f"task_in_prog_for_2_{minute}_{train}_{order}"
                        )
                        # minute-th <= M*x
                        self.model.addConstr(
                            (minute - end_time) <= self.M*self.task_in_progress_dep_x[train[0],train[1],train[2],order,minute],
                            name=f"task_in_prog_for_3_{minute}_{train}_{order}"
                        )
                        # end_time-task <= M*y
                        self.model.addConstr(
                            end_time - minute <= self.M*self.task_in_progress_dep_y[train[0],train[1],train[2],order,minute],
                            name=f"task_in_prog_for_4_{minute}_{train}_{order}"
                        )
                        # in_progress >= x+y-1
                        self.model.addConstr(
                            task_in_progress >= self.task_in_progress_dep_x[train[0],train[1],train[2],order,minute] + self.task_in_progress_dep_y[train[0],train[1],train[2],order,minute] - 1,
                            name=f"task_in_prog_for_5_{minute}_{train}_{order}"
                        )
            print("23.2: Task in progress relation FOR constraint defined.")

        def define_task_in_progress_dep_relation_constraint(self):
            """22.3: DEP For every minute and task, set task_in_progress to 1 if task is in progress at that minute."""  
            for minute in self.minute_slots:
                for train in self.trains_dep:
                    order = 4
                    # Chantier DEP
                    start_time = self.th_dep[train[0],train[1],train[2],order]
                    end_time = self.th_dep[train[0],train[1],train[2],order] + self.dep_durees[order-1]
                    task_in_progress = self.task_in_progress_dep[train[0],train[1],train[2],order,minute]
                    # th*in_progress <= minute
                    self.model.addConstr(
                        start_time*task_in_progress <= minute,
                        name=f"task_in_prog_dep_1_{minute}_{train}_{order}"
                    )
                    # minute <= th+duree*in_progress + M(1-in_progress)
                    self.model.addConstr(
                        minute <= (end_time)*task_in_progress + self.M*(1-task_in_progress),
                        name=f"task_in_prog_dep_2_{minute}_{train}_{order}"
                    )
                    # minute-th <= M*x
                    self.model.addConstr(
                        (minute - end_time) <= self.M*self.task_in_progress_dep_x[train[0],train[1],train[2],order,minute],
                        name=f"task_in_prog_dep_3_{minute}_{train}_{order}"
                    )
                    # end_time-task <= M*y
                    self.model.addConstr(
                        end_time - minute <= self.M*self.task_in_progress_dep_y[train[0],train[1],train[2],order,minute],
                        name=f"task_in_prog_dep_4_{minute}_{train}_{order}"
                    )
                    # in_progress >= x+y-1
                    self.model.addConstr(
                        task_in_progress >= self.task_in_progress_dep_x[train[0],train[1],train[2],order,minute] + self.task_in_progress_dep_y[train[0],train[1],train[2],order,minute] - 1,
                        name=f"task_in_prog_dep_5_{minute}_{train}_{order}"
                    )
            print("23.3: Task in progress relation DEP constraint defined.")


        def define_max_agent_constraint(self):
            """Constraint 24: Ensure that the maximum number of agents is not exceeded at any time."""
            for minute in self.minute_slots:
                self.model.addConstr(
                    quicksum(self.task_in_progress_arr[train[0], train[1], train[2], order, minute] for train in self.trains_arr for order in self.arr_orders) <= self.max_agents['reception',minute],
                    name=f"max_agents_constraint_rec_{minute}"
                )
                self.model.addConstr(
                    quicksum(self.task_in_progress_dep[train[0], train[1], train[2], order, minute] for train in self.trains_dep for order in self.dep_orders[:-1]) <= self.max_agents['formation',minute],
                    name=f"max_agents_constraint_for_{minute}"
                )
                self.model.addConstr(
                    quicksum(self.task_in_progress_dep[train[0], train[1], train[2], 4, minute] for train in self.trains_dep) <= self.max_agents['depart',minute],
                    name=f"max_agents_constraint_dep_{minute}"
                )
            print("24: Maximum agents constraint defined.")

        def define_usage_relation_constraint(self):
            """Constraint 25: Convert envelope_taches into envelope_used."""
            M = 100
            # REC
            for i, (start_time,end_time) in enumerate(self.envelopes_agents['roulement_reception']):
                self.model.addConstr(
                    quicksum(self.envelope_taches_REC[i,train[0],train[1],train[2],order] for train in self.trains_arr for order in self.arr_orders) >= self.envelope_used_REC[i],
                    name=f'envelope_used_rec_1_{i}'
                )
                self.model.addConstr(
                    quicksum(self.envelope_taches_REC[i,train[0],train[1],train[2],order] for train in self.trains_arr for order in self.arr_orders) <= M*self.envelope_used_REC[i],
                    name=f'envelope_used_rec_2_{i}'
                )
            # FOR
            for i, (start_time,end_time) in enumerate(self.envelopes_agents['roulement_formation']):
                self.model.addConstr(
                    quicksum(self.envelope_taches_FOR[i,train[0],train[1],train[2],order] for train in self.trains_dep for order in self.dep_orders[:-1]) >= self.envelope_used_FOR[i],
                    name=f'envelope_used_for_1_{i}'
                )
                self.model.addConstr(
                    quicksum(self.envelope_taches_FOR[i,train[0],train[1],train[2],order] for train in self.trains_dep for order in self.dep_orders[:-1]) <= M*self.envelope_used_FOR[i],
                    name=f'envelope_used_for_2_{i}'
                )
            # DEP
            for i, (start_time,end_time) in enumerate(self.envelopes_agents['roulement_depart']):
                self.model.addConstr(
                    quicksum(self.envelope_taches_DEP[i,train[0],train[1],train[2],4] for train in self.trains_dep) >= self.envelope_used_DEP[i],
                    name=f'envelope_used_dep_1_{i}'
                )
                self.model.addConstr(
                    quicksum(self.envelope_taches_DEP[i,train[0],train[1],train[2],4] for train in self.trains_dep) <= M*self.envelope_used_DEP[i],
                    name=f'envelope_used_dep_2_{i}'
                )
            # REC_DEP
            for i, (start_time,end_time) in enumerate(self.envelopes_agents['roulement_reception_depart']):
                self.model.addConstr(
                    quicksum(
                        self.envelope_taches_REC_DEP[i, train[0], train[1], train[2], order]
                        for train in self.trains
                        for order in self.dep_orders
                        if not (train[0] == 'ARR' and order == 4) and not (train[0] == 'DEP' and (order == 1 or order == 2 or order == 3))
                    ) >= self.envelope_used_REC_DEP[i],
                    name=f'envelope_used_rec_dep_1_{i}'
                )
                self.model.addConstr(
                    quicksum(self.envelope_taches_REC_DEP[i,train[0],train[1],train[2],order]
                            for train in self.trains
                            for order in self.dep_orders
                            if not (train[0] == 'ARR' and order == 4) and not (train[0] == 'DEP' and (order == 1 or order == 2 or order == 3))) 
                            <= M*self.envelope_used_REC_DEP[i],
                    name=f'envelope_used_rec_dep_2_{i}'
                )
            # FOR_DEP
            for i, (start_time,end_time) in enumerate(self.envelopes_agents['roulement_formation_depart']):
                self.model.addConstr(
                    quicksum(
                        self.envelope_taches_FOR_DEP[i, train[0], train[1], train[2], order]
                        for train in self.trains_dep
                        for order in self.dep_orders
                    ) >= self.envelope_used_FOR_DEP[i],
                    name=f'envelope_used_for_dep_1_{i}'
                )
                self.model.addConstr(
                    quicksum(self.envelope_taches_FOR_DEP[i,train[0],train[1],train[2],order]
                            for train in self.trains_dep
                            for order in self.dep_orders)
                            <= M*self.envelope_used_FOR_DEP[i],
                    name=f'envelope_used_for_dep_2_{i}'
                )
            print("25: Usage relation constraint defined.")
        
        def define_total_usage(self):
            """Constraint 26: Calculate total usage of envelopes."""
            self.model.addConstr(
                quicksum(
                    self.envelope_used_REC[i] for i in range(len(self.envelopes_agents['roulement_reception']))
                )+
                quicksum(
                    self.envelope_used_FOR[i] for i in range(len(self.envelopes_agents['roulement_formation']))
                )+
                quicksum(
                    self.envelope_used_DEP[i] for i in range(len(self.envelopes_agents['roulement_depart']))
                )+
                quicksum(
                    self.envelope_used_REC_DEP[i] for i in range(len(self.envelopes_agents['roulement_reception_depart']))
                )+
                quicksum(
                    self.envelope_used_FOR_DEP[i] for i in range(len(self.envelopes_agents['roulement_formation_depart']))
                ) <= self.envelope_used_total,
            )
            print("26: Total usage constraint defined.")


        define_unavailability_machines_constraints()
        define_usage_relation_constraint(self)
        define_total_usage(self)
        define_max_agent_constraint(self)
        define_task_in_progress_rec_relation_constraint(self)
        define_task_in_progress_for_relation_constraint(self)
        define_task_in_progress_dep_relation_constraint(self)
        define_envelope_taches_REC_relation_constraints(self)
        define_envelope_taches_FOR_relation_constraints(self)
        define_envelope_taches_DEP_relation_constraints(self)
        define_envelope_taches_REC_DEP_relation_constraints(self)
        define_envelope_taches_FOR_DEP_relation_constraints(self)
        define_unavailability_chantier_constraints()
        define_single_train_per_machine_constraints()
        # define_deb_usage_delay_constraint()
        # define_deg_time_limit_constraint()
        # define_for_before_deg_constraint()
        define_for_after_deb_constraint()        
        define_task_time_slots_constraint()
        define_arr_tri_constraint()
        define_tri_deb_constraint()
        define_DEB_parallel_constraint()
        define_FOR_parallel_constraint()
        define_attelage_FOR_constraint()
        define_DEG_attelage_constraint()
        define_DEG_parallel_constraint()
        define_frein_DEG_constraint()
        define_arr_start_constraint()
        define_dep_final_constraint()
        max_voies_constraint(self)
        calculate_max_voies_used(self)
        define_REC_occupation_relation_constraints(self)
        define_FOR_occupation_relation_constraints(self)
        define_DEP_occupation_relation_constraints(self)
        

        
        
        

        print('Constraints defined')
    
    def _define_objective_function(self):
        self.model.setObjective(self.envelope_used_total, GRB.MINIMIZE)  # Minimise total envelope usage
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

            results_taches_humaines = []
            for train in self.trains:
                if train[0] == 'ARR':
                    for task in self.arr_taches:
                        jour, horaire = minute_to_date2(self.model.getVarByName(f'th_arr[{train[0]},{train[1]},{train[2]},{task[0]}]').X, self.j1)
                        results_taches_humaines.append({
                            'Id tâche': f'{self.machines[0]}_{train[1]}_{jour}',
                            'Type de tâche': task,
                            'Jour': jour,
                            'Heure début': horaire,
                            'Durée': task[1],
                            'Sillon': train[1]
                        })
                elif train[0] == 'DEP':
                    for task in self.dep_taches:
                        jour, horaire = minute_to_date2(self.model.getVarByName(f'th_dep[{train[0]},{train[1]},{train[2]},{task[0]}]').X, self.j1)
                        results_taches_humaines.append({
                            'Id tâche': f'{self.machines[1]}_{train[1]}_{jour}',
                            'Type de tâche': task,
                            'Jour': jour,
                            'Heure début': horaire,
                            'Durée': task[1],
                            'Sillon': train[1]
                        })

            results_roulements = []
            for train in self.trains:
                if train[0] == 'ARR':
                    for order in self.arr_orders:
                        nb_roulement = self.
                        jour, horaire = minute_to_date2(self.model.getVarByName(f'th_arr[{train[0]},{train[1]},{train[2]},{order}]').X, self.j1)
                        results_roulements.append({
                            'Id tâche': f'{self.machines[0]}_{train[1]}_{jour}',
                            'Type de tâche': self.machines[0],
                            'Jour': jour,
                            'Heure début': horaire,
                            'Durée': self.arr_durees[order-1],
                            'Sillon': train[1]
                        })
            
                elif train[0] == 'DEP':



            # Create a DataFrame from the results
            df_results = pd.DataFrame(results)
            df_voies = pd.DataFrame(voies,index =self.chantiers)
            df_results_th = pd.DataFrame(results_taches_humaines)
            sheet_names = ["Taches machine","Voies utilisation","Taches humaines"]
            file_name = Path(self.fichier).stem

            # Save DataFrames to different sheets in the same Excel file
            with pd.ExcelWriter(f'{self.results_folder_save_path}/results_{file_name}.xlsx') as writer:
                df_results.to_excel(writer, sheet_name=sheet_names[0], index=False)
                df_voies.to_excel(writer, sheet_name=sheet_names[1], index=True)
                df_results_th.to_excel(writer, sheet_name=sheet_names[2], index=False)
            print(f'Results saved to {self.results_folder_save_path}/results_{file_name}.xlsx')
            print(f'Optimal solution found with objective value: {self.model.objVal}, total no of envelopes: {len(self.envelopes_agents["roulement_reception"])+len(self.envelopes_agents["roulement_formation"])+len(self.envelopes_agents["roulement_depart"])+len(self.envelopes_agents["roulement_reception_depart"])+len(self.envelopes_agents["roulement_formation_depart"])}')

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
