from llm.client import LLMClient
import re
import json
import argparse
from glob import glob
from db.postgres import PostgresConnector
from config import DATASETS

class EC:
   

   
    def is_system_error(sql, db_name):
        try:
            db = PostgresConnector(db_name)
            db.run_query(f"SET search_path TO {db_name};")
            sql_result = db.run_query(sql)
            db.close()
            if isinstance(sql_result, str):
                return {"error": True, "extra_info" : sql_result}
            return {"error": False, "extra_info" : None}
        except Exception as e:
            return {"error": True, "extra_info" : e}
            
            
    

    def extract_filter_values_from_sql(sql):
        patterns = [
        r"=\s*['\"]([^'\"]+)['\"]",
        r"ILIKE\s+['\"]%?([^%'\"]+)%?['\"]",
        r"LIKE\s+['\"]%?([^%'\"]+)%?['\"]",
        r"\bIN\s*\(\s*(['\"][^'\"]+['\"](?:\s*,\s*['\"][^'\"]+['\"])*)\s*\)",
        r"=\s*(TRUE|FALSE)",
        r"\bIS\s+(TRUE|FALSE)"
     ]
    
        all_values = []
        for pattern in patterns:
            matches = re.findall(pattern, sql, flags=re.IGNORECASE)
            for match in matches:
                if isinstance(match, str):
                    all_values.append(match.strip())
                elif isinstance(match, tuple):
                    all_values.extend([v.strip().strip("'\"") for v in match])
    
        return sorted(set(all_values))
        

    def collect_filter_values(data_paths):
        filter_values = set()
        for path in data_paths:
            with open(path, "r") as f:
                dataset = json.load(f)
                for entry in dataset:
                    values = entry.get("values", [])
                    filter_values.update(values)
        return filter_values
    
    

    def is_value_error(predicted_sql, allowed_values):
        filter_values = EC.extract_filter_values_from_sql(predicted_sql)
        invalid_values = [v for v in filter_values if v not in allowed_values]
    
        if invalid_values:
            print(f"[is_value_error] Invalid values found: {invalid_values}")
            return {"error": True, "invalid_values": invalid_values}
        else:
            return {"error": False}



    def generate_correction_prompt(original_prompt, error_type, predicted_sqls, extra_info=None):
        previous_attempts = "\n\n".join(
            f"[Attempt {i+1}]\n{sql}" for i, sql in enumerate(predicted_sqls)
        )
        if error_type == "system":
            return (
                f"Correct this non-executable SQL, based on this error information: {extra_info} \n\n"
                f"Previous attempts:\n{previous_attempts}\n\n"
                f"Original task:\n{original_prompt}\n\n"
                f"Wrap the corrected SQL query into ```sql ```."
            )
        if error_type == "value":
           return(
               f"Correct the erroneous SQL, based on the absence of the following filter value(s) in the database {extra_info}. \n\n"
               f"It might simply be a case-sensitivity issue. \n\n"
               f"Previous attempts:\n{previous_attempts}\n\n"
                f"Original task:\n{original_prompt}\n\n"
                f"Wrap the corrected SQL query into ```sql ```."
            )
        
 

    def correct_error(predicted_sqls, prompt, error_type, extra_info=None):
        llm = LLMClient()
        print(f"\n🔁 Retrying due to {error_type} error with {extra_info}")
        correction_prompt = EC.generate_correction_prompt(original_prompt=prompt, error_type=error_type, predicted_sqls=predicted_sqls, extra_info=extra_info)
    
        try:
            corrected_output = llm.infer(correction_prompt)
            match = re.search(r"```sql(.*?)```", corrected_output, re.DOTALL)
            if match:
                corrected_sql = match.group(1).strip().rstrip(";")
            else:
                corrected_sql = corrected_output.strip().rstrip(";")
            print(f"[CORRECTED SQL]: {corrected_sql}") 
            return corrected_sql
        except Exception as e:
            print(f"Error during self-correction: {e}")  
            return predicted_sqls[-1]
     

    def MGEI(predicted_sql, prompt, n = 1, db_name = "oncomx_v1_0_25"):
        sql_attempts = [predicted_sql]

        # ------ Phase 1: System Error Check ------ #
        for attempt in range(n):
            current_sql = sql_attempts[-1]
            
            print(f"\n🔁 [System error correction round {attempt + 1}/{n}]")
            
            system_check = EC.is_system_error(current_sql, db_name)
            if not system_check["error"]:
                print("✅ No system errors detected.")
                break

            error_type = "system"
            extra_info = system_check["extra_info"]
            
            corrected_sql = EC.correct_error(
                predicted_sqls=sql_attempts,
                prompt=prompt,
                error_type=error_type,
                extra_info=extra_info
            )

            if corrected_sql.strip() == current_sql.strip():
                print("⚠️ Correction did not change the SQL. Stopping system error correction.")
                break

            sql_attempts.append(corrected_sql)

        #------ Phase 2: Value Error Check ------ #
        for attempt in range(n):
            current_sql = sql_attempts[-1]
            print(f"\n🔁 [Value Error Correction Round {attempt + 1}/{n}]")
            
            def get_dataset_paths():
                parser = argparse.ArgumentParser()
                parser.add_argument("--dataset", choices=DATASETS.keys(), default="oncomx")
                args, _ = parser.parse_known_args()  # avoids crashing on unknown args
                return DATASETS[args.dataset]
    
            dataset_paths = get_dataset_paths()
            #print(f"Dataset paths: {dataset_paths}")
            dataset_paths = [dataset_paths["dev"], dataset_paths["tables"]]
            all_filter_values = EC.collect_filter_values(dataset_paths) 
            
            value_check = EC.is_value_error(predicted_sql=current_sql, allowed_values=all_filter_values)
           
            if not value_check["error"]:
                print("✅ No value errors detected.")
                break
            
            error_type = "value"
            extra_info = value_check["invalid_values"]
            
            print(f"\n🔁 Retrying due to {error_type} error...")
            corrected_sql = EC.correct_error(
                predicted_sqls=sql_attempts,
                prompt=prompt,
                error_type=error_type,
                extra_info=extra_info
            )
           
            if corrected_sql.strip() == current_sql.strip():
                print("⚠️ Correction did not change the SQL. Stopping value error correction.")
                break

            sql_attempts.append(corrected_sql)
        return sql_attempts[-1]
    
    # EM
    def normalize_sql(sql):
            return re.sub(r"\s+", " ", sql.strip().lower())
        
    #EX  
    def check_execution_match(pred_sql, gold_sql, db_name):
            try:
                db = PostgresConnector(db_name)
                gold_res = db.run_query(gold_sql)
                pred_res = db.run_query(pred_sql)
                db.close()
                if isinstance(pred_res, str):
                    return False
                return sorted(gold_res) == sorted(pred_res)
            except Exception:
                return False


