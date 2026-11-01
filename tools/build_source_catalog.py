"""Refresh the source catalogue and literal API route map."""
import argparse,ast,hashlib,json,os,re
from pathlib import Path
from datetime import datetime,timezone
parser=argparse.ArgumentParser()
parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
ROOT=parser.parse_args().root.resolve();PACK=ROOT/'analysis/soven'
now=datetime.now(timezone.utc).isoformat()
files=[]
for directory,dirs,names in os.walk(ROOT):
    dirs[:]=[d for d in dirs if d not in {'.git','node_modules','.next','.qa','.test-deps','__pycache__','.venv'}]
    for name in names:
        p=Path(directory)/name
        if p.suffix in {'.py','.ts','.tsx','.mjs','.cjs','.css','.yml'}:
            text=p.read_text(encoding='utf-8');symbols=[]
            if p.suffix=='.py':
                tree=ast.parse(text)
                symbols=[{'name':n.name,'line':n.lineno,'kind':type(n).__name__} for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))]
            else:symbols=[{'name':m.group(1),'line':text.count('\n',0,m.start())+1} for m in re.finditer(r'(?:function|class|type|interface)\s+(\w+)',text)]
            files.append({'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest(),'lines':len(text.splitlines()),'symbols':symbols})
(PACK/'SOURCE_CATALOG.json').write_text(json.dumps({'generated_at_utc':now,'scope':'Active source and supported tooling; no runtime/private files','text_hash_format':'UTF-8 with CRLF normalized to LF','files':sorted(files,key=lambda v:v['path'])},indent=2),encoding='utf-8')
# Resolve literal APIRouter prefixes to avoid treating relative paths as full endpoints.
rows=[]
for p in (ROOT/'backend/routers').glob('*.py'):
    tree=ast.parse(p.read_text(encoding='utf-8'));prefixes={}
    for n in tree.body:
        if isinstance(n,ast.Assign) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='APIRouter':
            prefix=next((k.value.value for k in n.value.keywords if k.arg=='prefix' and isinstance(k.value,ast.Constant)),'')
            for t in n.targets:
                if isinstance(t,ast.Name):prefixes[t.id]=prefix
    for n in ast.walk(tree):
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
            for d in n.decorator_list:
                if isinstance(d,ast.Call) and isinstance(d.func,ast.Attribute) and d.func.attr in {'get','post','put','delete','patch','websocket'} and isinstance(d.func.value,ast.Name) and d.args and isinstance(d.args[0],ast.Constant):
                    rows.append((p.relative_to(ROOT).as_posix(),d.func.attr.upper(),prefixes.get(d.func.value.id,'')+d.args[0].value,n.name))
(PACK/'API_MAP.md').write_text('# SOVEN API map\n\nGenerated from literal router prefixes and decorators. Check source models for exact schemas and middleware for access rules.\n\n| Source | Method | Route | Handler |\n|---|---|---|---|\n'+'\n'.join('| '+' | '.join(r)+' |' for r in rows)+'\n',encoding='utf-8')
print(json.dumps({'catalogued_source_files':len(files),'routes':len(rows)}))
