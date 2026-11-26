"""Gap-list simulations: (A) Sonnet writer x5 + Opus checker on each; (B) seeded flawed gaps, Opus checker x3."""
import json,os,re,subprocess,sys,concurrent.futures as cf,collections
E="/tmp/claude-0/-home-user-Skill-Optimizer/32faaa39-f790-5f14-83c0-16c82a453572/scratchpad/exp"
T="/home/user/Skill-Optimizer/results/2026-11-26-overclaim-pipeline-and-verifier-test/limitations_and_gaps_test"
O=f"{E}/g/sim"; os.makedirs(O,exist_ok=True)
gl=open("/home/user/Skill-Optimizer/skills/research-matrix/references/gap-list.md").read()
blocks=re.findall(r"```\n(.*?)\n```",gl,re.S)
writer=[b for b in blocks if b.startswith("You write the research-gap list")][0]
checker=[b for b in blocks if b.startswith("You check a research-gap list")][0]
inp=open(f"{T}/gap_writer_input.json").read()
def claude(model,prompt,tag):
    out=f"{O}/{tag}.json"
    if os.path.exists(out) and os.path.getsize(out)>100: return json.load(open(out))
    w=f"{O}/w/{tag}"; os.makedirs(w,exist_ok=True)
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
IDS=["brink2022","india2025","piu2026","tpack2024"]
# A. writer x5 then checker
def a_run(k):
    dw=claude("claude-sonnet-5-5",writer+"\n"+inp,f"A{k}-write"); g=last(str(dw["result"]),"gaps")
    dc=claude("claude-opus-5-5",checker+"\n"+inp+"\n"+json.dumps(g,ensure_ascii=False,indent=1),f"A{k}-check"); v=last(str(dc["result"]),"verdicts")
    return k,g,v,dw.get("total_cost_usd",0),dc.get("total_cost_usd",0)
# B. seeded
S=lambda g,kind,p:{"gap":g,"kind":kind,"papers":p,"basis":"seeded"}
seeds=[
 ("SOUND","Among these 4 papers, the authors of piu2026, india2025 and tpack2024 report limits on group allocation.","stated by authors",["piu2026","india2025","tpack2024"]),
 ("F-field","No study has examined adolescents' digital literacy beyond one year.","across papers",["india2025","piu2026"]),
 ("SOUND","Among these 4 papers, the authors of india2025 and piu2026 call for longer follow-up.","stated by authors",["india2025","piu2026"]),
 ("F-count","Among these 4 papers, all four used control or comparison groups.","across papers",["brink2022","india2025","piu2026","tpack2024"]),
 ("F-wrongpaper","Among these 4 papers, the authors of brink2022 and tpack2024 call for longer follow-up.","stated by authors",["brink2022","tpack2024"]),
 ("SOUND","Among these 4 papers, the authors of piu2026 and tpack2024 name self-reported outcomes as a limitation.","stated by authors",["piu2026","tpack2024"]),
 ("F-cause","Among these 4 papers, piu2026 and india2025 found smaller effects because they lacked randomisation.","across papers",["piu2026","india2025"]),
 ("F-kind","Among these 4 papers, the samples come from four different countries.","stated by authors",["brink2022","india2025","piu2026","tpack2024"]),
 ("F-contradicted","Among these 4 papers, none used interviews.","across papers",["india2025","piu2026"]),
 ("SOUND","Among these 4 papers, the authors of india2025 and piu2026 state that digital literacy was not fully assessed.","stated by authors",["india2025","piu2026"]),
 ("F-outside","Among these 4 papers, TPACK-based training remains under-researched in Asia.","across papers",["tpack2024"]),
 ("F-claim","Among these 4 papers, the findings show that digital literacy training improves wellbeing.","across papers",["piu2026","india2025"]),
]
seeded={"gaps":[S(g,k,p) for _,g,k,p in seeds]}
def b_run(k):
    dc=claude("claude-opus-5-5",checker+"\n"+inp+"\n"+json.dumps(seeded,ensure_ascii=False,indent=1),f"B{k}-check"); v=last(str(dc["result"]),"verdicts")
    return k,v,dc.get("total_cost_usd",0)
with cf.ThreadPoolExecutor(3) as ex:
    fa=[ex.submit(a_run,k) for k in range(1,6)]; fb=[ex.submit(b_run,k) for k in range(1,4)]
    A=[f.result() for f in fa]; B=[f.result() for f in fb]
res={"A":[{"run":k,"gaps":g["gaps"],"verdicts":v["verdicts"],"cost_write":cw,"cost_check":cc} for k,g,v,cw,cc in A],
     "B":{"seeds":[{"label":l,"gap":g} for l,g,_,_ in seeds],"runs":[{"run":k,"verdicts":v["verdicts"],"cost":c} for k,v,c in B]}}
json.dump(res,open(f"{T}/gap_simulations.json","w"),indent=1,ensure_ascii=False)
print("A costs: write",round(sum(a[3] for a in A),3),"check",round(sum(a[4] for a in A),3),"| B cost",round(sum(b[2] for b in B),3))
