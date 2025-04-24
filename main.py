import argparse
from utils.evaluator import Evaluator
from config import DATASETS, MODEL_OPTIONS
import config

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Text-to-SQL evaluation")
    parser.add_argument("--dataset", type=str, choices=DATASETS.keys(), default="oncomx",
                        help="Dataset to use: oncomx, cordis, or sdss")
    parser.add_argument("--model", type=str, choices=MODEL_OPTIONS, default="llama3",
                        help="LLM model to use")

    args = parser.parse_args()

    # Set selected model globally
    config.MODEL_NAME = args.model

    # Get dataset paths
    dataset_paths = DATASETS[args.dataset]
    dev_path = dataset_paths["dev"]
    schema_path = dataset_paths["tables"]
    db_name = dataset_paths["db"]

    evaluator = Evaluator(dev_path)
    evaluator.run(schema_path=schema_path, db_name=db_name)
