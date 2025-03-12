from model_jalon1 import ModelJalon1
import sys

if __name__ == '__main__':
    try:
        ModelJalon1().run_optimization()
        print(f"Model created successfully for instance.")
    except Exception as e:
        print(f"An error occurred while creating the model: {e}")
        sys.exit(1)
