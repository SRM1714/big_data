import json
import random
from pathlib import Path

def generate_few_shot(dev_path: str, out_path: str, n_total: int = 30, n_complex: int = 15):
    COMPLEX_KW = ('JOIN','GROUP','DISTINCT','COUNT','EXISTS','IN (')

    dev_file = Path(dev_path)
    out_file = Path(out_path)

    with dev_file.open(encoding='utf-8') as f:
        data = json.load(f)

    all_ex = []
    for ex in data:
        q = ex.get('question', '').strip().replace('\n', ' ')
        sql = ex.get('query', ex.get('sql', '')).strip().rstrip(';')
        if q and sql:
            all_ex.append((q, sql))

    complex_ex = [e for e in all_ex if any(kw in e[1].upper() for kw in COMPLEX_KW)]
    simple_ex  = [e for e in all_ex if e not in complex_ex]

    random.seed(42)

    available_complex = min(n_complex, len(complex_ex))
    chosen = random.sample(complex_ex, available_complex)

    remain = n_total - len(chosen)
    available_simple = min(remain, len(simple_ex))

    chosen += random.sample(simple_ex, available_simple)

    total_final = len(chosen)
    if total_final < n_total:
        print(f"[FewShot] ⚠️ Solo se generaron {total_final} ejemplos (faltaban suficientes complejos/simples)")


    out_file.parent.mkdir(parents=True, exist_ok=True)
    with out_file.open('w', encoding='utf-8') as f:
        for q, sql in chosen:
            f.write(f"-- Question: {q}\n-- SQL: {sql}\n\n")

    print(f"[FewShot] ✅ Written {len(chosen)} examples to {out_file}")
