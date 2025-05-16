import json
import random
from pathlib import Path

def generate_few_shot(dev_path: str,
                      out_path: str,
                      n_total: int = 30,
                      n_complex: int = 15):
    """
    Estrae n_total esempi few-shot dal dev-set:
      - fino a n_complex esempi ‘complessi’ (contengono JOIN/GROUP/DISTINCT/COUNT/EXISTS/IN)
      - il resto da quelli ‘semplici’
    """
    COMPLEX_KW = ('JOIN','GROUP','DISTINCT','COUNT','EXISTS','IN (')

    data = json.load(Path(dev_path).open(encoding='utf-8'))
    all_ex = []
    for ex in data:
        q   = ex.get('question','').strip().replace('\n',' ')
        sql = ex.get('query', ex.get('sql','')).strip().rstrip(';')
        if q and sql:
            all_ex.append((q, sql))

    complex_ex = [e for e in all_ex if any(kw in e[1].upper() for kw in COMPLEX_KW)]
    simple_ex  = [e for e in all_ex if e not in complex_ex]

    random.seed(42)
    chosen = random.sample(complex_ex, min(n_complex, len(complex_ex)))
    remain = n_total - len(chosen)
    chosen += random.sample(simple_ex, min(remain, len(simple_ex)))

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open('w', encoding='utf-8') as f:
        for q, sql in chosen:
            f.write(f"-- Question: {q}\n-- SQL: {sql}\n\n")

    print(f"[FewShot] ✅ Written {len(chosen)} examples to {out}")
