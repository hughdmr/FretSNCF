import os

import plotly.graph_objects as go
import pandas as pd
from dotenv import load_dotenv

ORDERED_MACHINES = ["Debranchement", "Formation", "Degarage"]
CORRESPONDANCES_SHEET = "Correspondances"


class CorrespondanceColumnNames:
    WAGON_ID = "Id wagon"
    ARRIVAL_DATE = "Jour arrivee"
    ARRIVAL_TRAIN_NUMBER = "n°Train arrivee"
    ARRIVAL_TRAIN_ID = "ID Train arrivee"
    DEPARTURE_DATE = "Jour depart"
    DEPARTURE_TRAIN_NUMBER = "n°Train depart"
    DEPARTURE_TRAIN_ID = "ID Train depart"


def get_link_id(arrival_train_id, departure_train_id):
    return f"{arrival_train_id} {departure_train_id}"


if __name__ == "__main__":
    load_dotenv()
    FILE_INSTANCE = os.getenv("FILE_INSTANCE")
    input_file_path = FILE_INSTANCE
    input_directory_path = r"..\données_MAJ"

    filter_on_departure_date = True
    departure_date_filter = "13/08/2022"

    input_df = pd.read_excel(
        input_file_path,
        sheet_name=CORRESPONDANCES_SHEET,
        converters={
            CorrespondanceColumnNames.WAGON_ID: str,
            CorrespondanceColumnNames.ARRIVAL_DATE: str,
            CorrespondanceColumnNames.ARRIVAL_TRAIN_NUMBER: str,
            CorrespondanceColumnNames.DEPARTURE_DATE: str,
            CorrespondanceColumnNames.DEPARTURE_TRAIN_NUMBER: str,
        }
    )

    if filter_on_departure_date:
        input_df = input_df[input_df[CorrespondanceColumnNames.DEPARTURE_DATE] == departure_date_filter]

    input_df[CorrespondanceColumnNames.ARRIVAL_TRAIN_ID] = (
        input_df[CorrespondanceColumnNames.ARRIVAL_TRAIN_NUMBER]
        + " "
        + input_df[CorrespondanceColumnNames.ARRIVAL_DATE]
    )
    arrival_train_ids = input_df[CorrespondanceColumnNames.ARRIVAL_TRAIN_ID].drop_duplicates().values.tolist()
    arrival_train_idx_per_id = {
        train_id: train_idx
        for train_idx, train_id in enumerate(arrival_train_ids)
    }
    arrival_trains_amount = len(arrival_train_idx_per_id)

    input_df[CorrespondanceColumnNames.DEPARTURE_TRAIN_ID] = (
            input_df[CorrespondanceColumnNames.DEPARTURE_TRAIN_NUMBER]
            + " "
            + input_df[CorrespondanceColumnNames.DEPARTURE_DATE]
    )
    departure_train_ids = input_df[CorrespondanceColumnNames.DEPARTURE_TRAIN_ID].drop_duplicates().values.tolist()
    departure_train_idx_per_id = {
        train_id: train_idx
        for train_idx, train_id in enumerate(departure_train_ids)
    }

    link_sources = []
    link_targets = []
    link_values = []
    idx_offset = arrival_trains_amount
    link_idx = 0
    link_idx_per_id = {}
    for wagon_id, arrival_train_id, departure_train_id in zip(
        input_df[CorrespondanceColumnNames.WAGON_ID],
        input_df[CorrespondanceColumnNames.ARRIVAL_TRAIN_ID],
        input_df[CorrespondanceColumnNames.DEPARTURE_TRAIN_ID],
    ):
        link_id = get_link_id(arrival_train_id, departure_train_id)
        if link_id not in link_idx_per_id:
            link_sources.append(arrival_train_idx_per_id[arrival_train_id])
            link_targets.append(departure_train_idx_per_id[departure_train_id] + idx_offset)
            link_values.append(1)
            link_idx_per_id[link_id] = link_idx
            link_idx += 1
        else:
            link_values[link_idx_per_id[link_id]] += 1

    fig = go.Figure(go.Sankey(
        arrangement='snap',
        node=dict(
            label=arrival_train_ids+departure_train_ids,
            pad=10,
            thickness=20,
        ),
        link=dict(
            arrowlen=15,
            source=link_sources,
            target=link_targets,
            value=link_values,
            hovertemplate='%{value} wagons<br />'
                          'du sillon "%{source.label}"<br />'
                          'au sillon "%{target.label}"<br /><extra></extra>',
        )
    ))

    fig.show()
