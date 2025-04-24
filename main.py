from utils.evaluator import Evaluator
from config import DEV_PATH, SCHEMA_PATH

if __name__ == "__main__":
    evaluator = Evaluator(DEV_PATH)
    evaluator.run(SCHEMA_PATH)
