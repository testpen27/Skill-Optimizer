import json,glob,os,math,sys,collections
E="/tmp/claude-0/-home-user-Skill-Optimizer/32faaa39-f790-5f14-83c0-16c82a453572/scratchpad/exp/v3/out"
T=os.path.dirname(os.path.abspath(__file__))
key=json.load(open(f"{T}/seedkey.json"))
files=sorted(os.path.basename(f)[3:-5] for f in glob.glob(f"{T}/in_*.json"))
def objs(txt):
    dec=json.JSONDecoder(); out=[]; i=0
    while True:
        j=txt.find("{",i)
        if j<0: return out
        try: o,end=dec.raw_decode(txt[j:]); out.append(o); i=j+end
        except Exception: i=j+1
def load(tag,f):
    p=f"{E}/{tag}-{f}.json"
    if not os.path.exists(p): return None
    d=json.load(open(p))
    for o in reversed(objs(str(d.get("result","")))):
        if "verdicts" in o: return {v["id"]:v for v in o["verdicts"]},d
    return None
planted={(k["file"],k["id"]):k for k in key}
def wilson(k,n,z=1.96):
    if n==0: return (0,0)
    p=k/n; d=1+z*z/n; c=p+z*z/(2*n); r=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))
    return ((c-r)/d,(c+r)/d)
def sign_p(b,c):
    n=b+c
    if n==0: return 1.0
    k=min(b,c); return min(1.0,2*sum(math.comb(n,i) for i in range(k+1))/2**n)
res={}
for setup in ("P","C"):
    for rep in (1,2):
        tag=f"{setup}{rep}"; caught=collections.Counter(); tot=collections.Counter(); false=0; nun=0; cost=0; outtok=0; runs=0; detail={}; flagged_un=[]
        for f in files:
            r=load(tag,f)
            if not r: continue
            vs,d=r; runs+=1; cost+=d.get("total_cost_usd",0); outtok+=d["usage"]["output_tokens"]
            sents=[s["id"] for s in json.load(open(f"{T}/in_{f}.json"))["sentences"]]
            for sid in sents:
                v=vs.get(sid,{}).get("verdict","MISSING")
                if (f,sid) in planted:
                    t=planted[(f,sid)]["type"]; tot[t]+=1; tot["ALL"]+=1
                    hit=v!="keep" ; detail[(f,sid)]=hit
                    if hit: caught[t]+=1; caught["ALL"]+=1
                else:
                    nun+=1
                    if v!="keep": false+=1; flagged_un.append((f,sid))
        res[tag]=dict(runs=runs,caught=caught,tot=tot,false=false,nun=nun,cost=cost,outtok=outtok,detail=detail,flagged_un=flagged_un)
def line(tag):
    r=res[tag]
    if not r["runs"]: return f"{tag}: no data"
    c,t=r["caught"]["ALL"],r["tot"]["ALL"]; lo,hi=wilson(c,t)
    return (f"{tag}: runs {r['runs']}/8  planted caught {c}/{t} ({100*c/t:.0f}%, 95% CI {100*lo:.0f}-{100*hi:.0f})  "
            f"untouched flagged {r['false']}/{r['nun']}  cost ${r['cost']:.2f} (${r['cost']/r['runs']:.3f}/file)  out tokens/file {r['outtok']//r['runs']}")
for tag in ("P1","P2","C1","C2"): print(line(tag))
# by type, pooled over reps
for setup in ("P","C"):
    c=sum((res[f"{setup}{r}"]["caught"] for r in (1,2)),collections.Counter()); t=sum((res[f"{setup}{r}"]["tot"] for r in (1,2)),collections.Counter())
    print(setup,"pooled",{k:f"{c[k]}/{t[k]}" for k in sorted(t)})
# paired comparison per planted error per rep
b=c_=both=none=0
for rep in (1,2):
    for k in planted_keys if False else planted:
        p=res[f"P{rep}"]["detail"].get(k); c=res[f"C{rep}"]["detail"].get(k)
        if p is None or c is None: continue
        if p and c: both+=1
        elif p and not c: b+=1
        elif c and not p: c_+=1
        else: none+=1
print(f"paired trials: both caught {both}, only plain {b}, only combined {c_}, neither {none}; exact sign test p={sign_p(b,c_):.3f}")
# errors missed by anyone
miss=collections.defaultdict(list)
for tag in ("P1","P2","C1","C2"):
    for k,v in res[tag]["detail"].items():
        if not v: miss[k].append(tag)
for k,v in sorted(miss.items()): print("MISSED",k,planted[k]["type"],planted[k]["new"][:60],"by",v)
# run-to-run consistency on untouched flags
for setup in ("P","C"):
    a=set(res[f"{setup}1"]["flagged_un"]); b2=set(res[f"{setup}2"]["flagged_un"])
    print(setup,"untouched flags rep1",len(a),"rep2",len(b2),"in both",len(a&b2))
