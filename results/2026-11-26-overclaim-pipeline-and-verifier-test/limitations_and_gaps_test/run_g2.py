"""Stage: Opus verifies the limitations sentences (combined verifier prompt); Sonnet writes gaps; Opus checks gaps."""
import json,os,re,subprocess,sys,concurrent.futures as cf
sys.path.insert(0,"/home/user/Skill-Optimizer/skills/research-matrix/scripts")
from common import split_sentences
E="/tmp/claude-0/-home-user-Skill-Optimizer/32faaa39-f790-5f14-83c0-16c82a453572/scratchpad/exp"
R="/home/user/Skill-Optimizer/results/2026-11-26-overclaim-pipeline-and-verifier-test"
T=f"{R}/limitations_and_gaps_test"; W=f"{E}/g/work2"
comb=open(f"{R}/combined_verifier_test/combined_prompt.txt").read()
gl=open("/home/user/Skill-Optimizer/skills/research-matrix/references/gap-list.md").read()
blocks=re.findall(r"```\n(.*?)\n```",gl,re.S)
writer=[b for b in blocks if b.startswith("You write the research-gap list")][0]
checker=[b for b in blocks if b.startswith("You check a research-gap list")][0]
data=json.load(open(f"{W}/lrm.json"))["papers"]
os.makedirs(f"{W}/o",exist_ok=True)
def claude(model,prompt,tag):
    out=f"{W}/o/{tag}.json"
    if os.path.exists(out) and os.path.getsize(out)>100: return json.load(open(out))
    w=f"{W}/w/{tag}"; os.makedirs(w,exist_ok=True)
    p=subprocess.run(["claude","-p",prompt,"--model",model,"--output-format","json","--setting-sources","project"],cwd=w,stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=900)
    open(out,"w").write(p.stdout); return json.loads(p.stdout)
def last(txt,key):
    dec=json.JSONDecoder(); i=0; f=None
    while True:
        j=txt.find("{",i)
        if j<0: return f
        try: o,e=dec.raw_decode(txt[j:])
        except Exception: i=j+1; continue
        if isinstance(o,dict) and key in o: f=o
        i=j+e
cost={"verify":0,"write":0,"check":0}
# 1. verify limitations sentences
def ver(p):
    sents=[{"id":f"limitations.{k}","sentence":s} for k,s in enumerate(split_sentences(p.get("limitations") or ""),1)]
    q=[x["q"] if isinstance(x,dict) else x for x in (p.get("evidence") or {}).get("limitations",[])]
    inp=json.dumps({"sentences":sents,"quotes":{"limitations":q}},ensure_ascii=False,indent=1)
    d=claude("claude-opus-5-5",comb+inp,"ver-"+p["id"]); return p["id"],sents,d
with cf.ThreadPoolExecutor(2) as ex: vres=list(ex.map(ver,data))
verified={}
for pid,sents,d in vres:
    cost["verify"]+=d.get("total_cost_usd",0)
    o=last(str(d["result"]),"verdicts"); vs={v["id"]:v for v in (o or {}).get("verdicts",[])}
    keep=[s["sentence"] for s in sents if vs.get(s["id"],{}).get("verdict")=="keep"]
    print(pid,{s["id"]:vs.get(s["id"],{}).get("verdict") for s in sents})
    for s in sents:
        v=vs.get(s["id"],{})
        if v.get("verdict")!="keep": print("   NOT KEPT",s["id"],v.get("verdict"),"|",s["sentence"][:110],"|",v.get("reason","")[:160])
    verified[pid]=" ".join(keep)
json.dump(verified,open(f"{T}/verified_limitations.json","w"),indent=1,ensure_ascii=False)
# 2. Sonnet writes the gap list
inp={"title":"Digital literacy training programmes for adolescents and teachers: effects and teaching approaches",
     "papers":[{"id":p["id"],"year":p.get("year"),"type":p.get("type"),"methodology":p.get("methodology"),"limitations":verified[p["id"]] or "Not explicitly stated"} for p in data]}
inp_s=json.dumps(inp,ensure_ascii=False,indent=1)
open(f"{T}/gap_writer_input.json","w").write(inp_s)
dw=claude("claude-sonnet-5-5",writer+"\n"+inp_s,"gapwrite"); cost["write"]=dw.get("total_cost_usd",0)
gaps=last(str(dw["result"]),"gaps")
json.dump(gaps,open(f"{T}/gaps_out_gaps.json","w"),indent=1,ensure_ascii=False)
for i,g in enumerate(gaps["gaps"],1): print(f"gap.{i} [{g['kind']}] {g['papers']}\n   {g['gap']}\n   basis: {g.get('basis')}")
# 3. Opus checks the gap list
dc=claude("claude-opus-5-5",checker+"\n"+inp_s+"\n"+json.dumps(gaps,ensure_ascii=False,indent=1),"gapcheck"); cost["check"]=dc.get("total_cost_usd",0)
ver_=last(str(dc["result"]),"verdicts")
json.dump(ver_,open(f"{T}/gaps_check_verdicts.json","w"),indent=1,ensure_ascii=False)
for v in ver_["verdicts"]: print(v)
print("COSTS",{k:round(v,3) for k,v in cost.items()},"total",round(sum(cost.values()),3))
