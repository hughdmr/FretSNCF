import datetime
import itertools
import os

import plotly.express as px
import pandas as pd


# ORDERED_MACHINES = ["Debranchement", "Formation", "Degarage"]
ORDERED_MACHINES = ["DEB", "FOR", "DEG"]
MACHINE_TASKS_SHEET = "Sheet1"


class ResultColumnNames:
    TASK_ID = "Id tâche"
    TASK_TYPE = "Type de tâche"
    TASK_DATE = "Jour"
    TASK_HOUR = "Heure début"
    TASK_DURATION = "Durée"
    TASK_TRAIN = "Sillon"


def get_resource_name(task_type, task_date):
    return f"{task_type} {task_date.isoformat()}"


if __name__ == "__main__":
    # result_directory_path = r"./"
    result_file_path = "outputs/results/resultats_instance_WPY_realiste_jalon1.xlsx"
    # result_file_path = os.path.join(result_directory_path, result_file_name)

    result_df = pd.read_excel(result_file_path, sheet_name=MACHINE_TASKS_SHEET)
    # Ensure that date columns are properly parsed
    result_df[ResultColumnNames.TASK_DATE] = pd.to_datetime(result_df[ResultColumnNames.TASK_DATE],  format="%d/%m/%Y")
    result_df[ResultColumnNames.TASK_HOUR] = pd.to_datetime(result_df[ResultColumnNames.TASK_HOUR], format="%H:%M").dt.time
    dummy_date = datetime.date(2000, 1, 1)
    tasks = []
    resource_per_machine = {}
    for task_id, task_type, task_pd_datetime, task_hour_datetime, task_duration, task_train in zip(
            result_df[ResultColumnNames.TASK_ID],
            result_df[ResultColumnNames.TASK_TYPE],
            result_df[ResultColumnNames.TASK_DATE],
            result_df[ResultColumnNames.TASK_HOUR],
            result_df[ResultColumnNames.TASK_DURATION],
            result_df[ResultColumnNames.TASK_TRAIN],
    ):  
        task_date_datetime = task_pd_datetime.to_pydatetime()
        task_start = datetime.datetime.combine(dummy_date, task_hour_datetime)
        task_resource = get_resource_name(task_type, task_date_datetime.date())
        tasks.append(
            dict(
                Train=task_train,
                Start=task_start,
                Finish=task_start+datetime.timedelta(minutes=task_duration),
                Machine=task_type,
                Resource=task_resource
            )
        )
        resource_per_machine.setdefault(task_type, set()).add(get_resource_name(task_type, task_date_datetime.date()))
    gantt_df = pd.DataFrame(tasks)
    sorted_resources = list(itertools.chain.from_iterable(
        [sorted(resource_per_machine[machine]) for machine in ORDERED_MACHINES]
    ))

    fig = px.timeline(gantt_df, x_start="Start", x_end="Finish", y="Resource", color="Train", color_discrete_sequence=px.colors.qualitative.Set3)
    fig.update_layout(xaxis=dict(title='Timestamp', tickformat='%H:%M:%S'))
    fig.update_yaxes(categoryorder="array", categoryarray=sorted_resources[::-1])
    fig.show()
