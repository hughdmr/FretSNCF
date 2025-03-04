# **Fret SNCF** Indian Pacific project

## **Introduction**

This repository hosts the Fret SNCF project, developed by the Indian Pacific team.

In this project, we aim to model the management of a freight classification yard. We utilize data from Woippy, the largest freight yard in France. However, the same principles apply to any classification yard.

## **Contributors**

- Angus Chisholm
- Thomas Desforges
- Marin d'Hébrail
- Tanguy Garnier
- Hugues d'Hardemare

## **Repository structure**

- The folder `data/`contains the instances (already uploaded in the folder)
- The folder `outputs/`contains some of the outputs of the python scripts (models and tables)
- The folder `src/`contains the code with:
  - `notebooks/`: some notebooks for test
  - `utils/`: utils functions used in the creation of the models
  - `main.py`and `create_model.py`to create the model (jalon1).
- The poetry files to install a python virtual environment (cf Prerequisites)
- `.gitignore`and `README.md`

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
