# **Fret SNCF** Indian Pacific project

## **Introduction**

This repository hosts the Fret SNCF project, developed by the Indian Pacific team.

In this project, we aim to model the management of a freight classification yard. We utilize data from Woippy, the largest freight yard in France. However, the same principles apply to any classification yard.

## **Contributors**

- Angus Chisholm
- Hugues d'Hardemare

## **Repository structure**

- The folder `data/`contains the instances (already uploaded in the folder)
- The folder `outputs/`contains some of the outputs of the python scripts (models and tables)
  - `results_instanceNAME_jalonN.xlsx`are the excel with the results of an instance M and jalon N, you can use it to display graph with gantt and sankey.
  - `gantt_instanceNAME_jalonN.png`are the gantt graph (same for sankey).
- The folder `src/`contains the code with:
  - `deprecated_versions/`: some old versions of models and notebooks for test
  - `utils/`: utils functions used in the creation of the models and displaying of the results.
    - `display_gantt.py`: displaying function for gantt graph
    - `display_sankey.py`: displaying function for sankey graph
    - `display_track_occupation.py`: displaying function for track occupation using `display_colors.py`
    - `verify_train.py`: streamlit interface to check times when machines are used for a departure train.
  - `model.py`: old version for creation of model
  - `model_jalonN.py`: model for the Nth jalon.
  - `main.py`: choose you model and run it.
- The poetry files to install a python virtual environment (cf Prerequisites)
- `.gitignore`and `README.md`
- `.env`here is not ignored because there is no confidential data but it's used as a config file

## **Prerequisites (virtual environment)**

Before you begin, make sure you have the following installed on your machine to use the poetry env:

- **Poetry**  
  To install Poetry, you can use the following command:

  ```bash
  curl -sSL https://install.python-poetry.org | python3 -
  ```

- **Install**
  Use Poetry to install the project dependencies, including numpy, matplotlib, and gurobipy.
  This will also create a virtual environment automatically.

  Run the following command:

  ```bash
    poetry install
  ```

- **Activate the Poetry Virtual Environment**
  Once the dependencies are installed, you can activate the Poetry virtual environment by running:

  ```bash
  poetry env activate
  ```

- **Run the script in poetry env**
  Once the env is activated, you can use the Poetry virtual environment by running:

  ```bash
  poetry run python <script>.py
  ```

- **Add packages in poetry env**
  If you want to add package in the env, you can run:

  ```bash
  poetry add <package_name>
  poetry install
  ```

## **Config environment**

Update your .env with the global variables you want to use for the execution of the code

## **Create a model**

Run main with the config file updated and the model chose.
