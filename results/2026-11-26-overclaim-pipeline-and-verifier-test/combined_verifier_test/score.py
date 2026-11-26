"""Score verifier runs against the planted-error key (same method as verifier_test/)."""
import json,sys
E="/tmp/claude-0/-home-user-Skill-Optimizer/32faaa39-f790-5f14-83c0-16c82a453572/scratchpad/exp"
V="/home/user/Skill-Optimizer/results/2026-11-26-overclaim-pipeline-and-verifier-test/verifier_test"
PIDS=["india2025","piu2026","brink2022","tpack2024"]
key=json.load(open(f"{V}/seedkey.json")); seed={}
for k in key: seed.setdefault(k["id"],set()).update(k["sentence_ids"])
def objs(txt):
    dec=json.JSONDecoder(); out=[]; i=0
    while True:
        j=txt.find("{",i)
        if j<0: return out
        try: o,end=dec.raw_decode(txt[j:]); out.append(o); i=j+end
        except Exception: i=j+1
def load(path):
    d=json.load(open(path)); return d
def verdicts(d):
    for o in reversed(objs(str(d["result"]))):
        if "verdicts" in o: return {v["id"]:v for v in o["verdicts"]}
    return {}
def disputes(d):
    for o in reversed(objs(str(d["result"]))):
        if "disputes" in o: return o["disputes"]
    return []
def score(tag,kind="verdicts"):
    caught=false=miss=0; cost=0; flagged=[]; real=None
    for pid in PIDS:
        d=load(f"{E}/v2/out/{tag}-{pid}.json" if tag.startswith(("combo","opusChallengesOpus")) else f"{E}/v/out/{tag}-{pid}.json")
        cost+=d.get("total_cost_usd",0)
        n=len(json.load(open(f"{V}/vin_{pid}.json"))["sentences"])
        sent=[s["id"] for s in json.load(open(f"{V}/vin_{pid}.json"))["sentences"]]
        if kind=="verdicts":
            vs=verdicts(d); bad={i for i,v in vs.items() if v.get("verdict")!="keep"}
        else:
            first=verdicts(load(f"{E}/v/out/opusV-{pid}.json"))
            bad={i for i,v in first.items() if v.get("verdict")!="keep"}
            for x in disputes(d):
                if x["should_be"]=="keep": bad.discard(x["id"])
                else: bad.add(x["id"])
        for i in sent:
            if i in seed[pid]:
                caught+= i in bad; miss+= i not in bad
            elif i in bad:
                false+=1; flagged.append((pid,i))
        if pid=="india2025" and "results.4" in bad: real=True
    return dict(tag=tag,caught=caught,missed=miss,untouched_flagged=false,real_find_india_results4=bool(real),cost=round(cost,3),per_paper=round(cost/4,3),flagged=flagged)
if __name__=="__main__":
    out=[score("opusV"),score("combo1"),score("combo2"),score("opusChallengesOpus","disputes")]
    for o in out: print({k:v for k,v in o.items() if k!="flagged"})
    json.dump(out,open(sys.argv[1] if len(sys.argv)>1 else "/dev/null","w"),indent=1)
