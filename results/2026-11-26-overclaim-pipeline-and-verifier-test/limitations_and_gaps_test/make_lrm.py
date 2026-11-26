"""Turn the Haiku readers' replies into helper_out/<id>.json, merge them, and check the quotes."""
import json,os,subprocess,sys
E="/tmp/claude-0/-home-user-Skill-Optimizer/32faaa39-f790-5f14-83c0-16c82a453572/scratchpad/exp"
SK="/home/user/Skill-Optimizer/skills/research-matrix/scripts"
T="/home/user/Skill-Optimizer/results/2026-11-26-overclaim-pipeline-and-verifier-test/limitations_and_gaps_test"
W=f"{E}/g/work2"; os.makedirs(f"{W}/helper_out",exist_ok=True)
base={p["id"]:p for p in json.load(open(f"{E}/sonnet_lrm.json"))["papers"]}
def last_obj(txt,key):
    dec=json.JSONDecoder(); i=0; found=None
    while True:
        j=txt.find("{",i)
        if j<0: return found
        try: o,end=dec.raw_decode(txt[j:])
        except Exception: i=j+1; continue
        if isinstance(o,dict) and key in o: found=o
        i=j+end
cost=0
for pid in base:
    d=json.load(open(f"{E}/g/out/s1-{pid}.json")); cost+=d.get("total_cost_usd",0)
    o=last_obj(str(d["result"]),"evidence")
    if not o: print("NO JSON for",pid); continue
    p={k:v for k,v in base[pid].items() if k in ("id","authors","year","title","journal","volume","issue","pages","doi","issn","quartile")}
    p["quartile"]=p.get("quartile") or "Unranked/Unavailable"
    for k in ("type","introduction","methodology","theory","results","discussion","limitations","evidence","abstract_claims","caveats","source_basis"):
        if k in o: p[k]=o[k]
    p["type"]=p.get("type") or base[pid].get("type")
    json.dump(p,open(f"{W}/helper_out/{pid}.json","w"),ensure_ascii=False,indent=1)
    print(pid,"output tokens",d["usage"]["output_tokens"],"cost",round(d.get("total_cost_usd",0),4))
print("stage-1 total cost",round(cost,3))
subprocess.run([sys.executable,"-I",f"{SK}/merge_papers.py",f"{W}/lrm.json","--from",f"{W}/helper_out"])
r=subprocess.run([sys.executable,"-I",f"{SK}/check_evidence.py",f"{W}/lrm.json","--papers",f"{E}/papers"],capture_output=True,text=True)
print(r.stdout[-3000:],r.stderr[-500:])
d=json.load(open(f"{W}/lrm.json"))
for p in d["papers"]:
    print("\n=====",p["id"],"\nLIMITATIONS CELL:",p.get("limitations"))
    for q in (p.get("evidence") or {}).get("limitations",[]): print("   Q:",q["q"][:230] if isinstance(q,dict) else q[:230])
