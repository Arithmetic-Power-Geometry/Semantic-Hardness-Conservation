import os,sys,json,subprocess
ROOT=os.path.dirname(__file__)
sys.path.insert(0,os.path.join(ROOT,'src'))
from semantic_hardness.experiments import run_all
summary=run_all(os.path.join(ROOT,'results'))
subprocess.run([sys.executable, os.path.join(ROOT,'export_latex_tables.py')], check=True)
summary['latex_table_fragments']=10
print(json.dumps(summary,indent=2))
