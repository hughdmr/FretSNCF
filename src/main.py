from model_jalon1 import ModelJalon1
from model_jalon2 import ModelJalon2

if __name__ == '__main__':
    try:
        ModelJalon2().run_optimization() # Choose the model you want to run
        print(f"Model created successfully for instance.")
    except Exception as e:
        print(f"An error occurred while creating the model: {e}")
