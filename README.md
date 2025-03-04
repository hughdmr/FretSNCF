# **fret-sncf** Project

## **Introduction**

This is the **fret-sncf** project.

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
