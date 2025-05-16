# main.py (snippet aggiornato per passare n_complex)
import argparse
from utils.evaluator import Evaluator
from utils.few_shot_generator import generate_few_shot
from config import DATASETS, MODEL_OPTIONS
import config

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Text-to-SQL evaluation")
    parser.add_argument("--dataset", type=str, choices=DATASETS.keys(), default="oncomx",
                        help="Dataset to use: oncomx, cordis, or sdss")
    parser.add_argument("--model", type=str, choices=MODEL_OPTIONS, default="llama3",
                        help="LLM model to use")
    parser.add_argument("--fewshot", type=int, default=30,
                        help="Number of few-shot examples to include (default=30)")
    parser.add_argument("--n_complex", type=int, default=15,
                        help="Number of few-shot examples that must be complex (default=15)")
    parser.add_argument("--n", type=int, default=10,
                        help="Number of queries to run (default=10)")

    args = parser.parse_args()

    # Set selected model globally
    config.MODEL_NAME = args.model

    # Paths
    dataset_paths = DATASETS[args.dataset]
    dev_path = dataset_paths["dev"]
    schema_path = dataset_paths["tables"]
    db_name = dataset_paths["db"]
    few_shot_path = f"prompts/{args.dataset}_few_shot.txt"

    # Genera dinamicamente i few-shot
    generate_few_shot(
        dev_path=dev_path,
        out_path=few_shot_path,
        n_total=args.fewshot,
        n_complex=args.n_complex
    )

    # Run evaluation
    evaluator = Evaluator(dev_path)
    evaluator.run(
        schema_path=schema_path,
        db_name=db_name,
        few_shot_path=few_shot_path,
        limit=args.n
    )
