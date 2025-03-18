from model_jalon1 import ModelJalon1
from model_jalon2 import ModelJalon2
from model_jalon3 import ModelJalon3

if __name__ == '__main__':
    try:
        ModelJalon3().run_optimization() # Choose the model you want to run
        print(f"Model created successfully for instance.")
    except Exception as e:
        print(f"An error occurred while creating the model: {e}")
