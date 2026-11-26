import json,subprocess,os,re,sys,concurrent.futures as cf
E="/tmp/claude-0/-home-user-Skill-Optimizer/32faaa39-f790-5f14-83c0-16c82a453572/scratchpad/exp"
PIDS=["india2025","piu2026","brink2022","tpack2024"]
def run(tag,model,prompt,pid):
    w=f"{E}/v/work/{tag}/{pid}"; os.makedirs(w,exist_ok=True)
    p=subprocess.run(["claude","-p",prompt,"--model",model,"--output-format","json","--setting-sources","project"],
                     cwd=w,stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=900)
    open(f"{E}/v/out/{tag}-{pid}.json","w").write(p.stdout)
    return tag,pid,p.returncode
def stage(tag,model,mk):
    with cf.ThreadPoolExecutor(2) as ex:
        res=list(ex.map(lambda pid:run(tag,model,mk(pid),pid),PIDS))
    open(f"{E}/v/out/progress.txt","a").write(f"{tag} {res}\n")
ver=open(f"{E}/v/verifier_prompt.txt").read(); chal=open(f"{E}/v/challenger_prompt.txt").read()
vin=lambda pid:open(f"{E}/vin_{pid}.json").read()
stage("sonnetV","claude-sonnet-5-5",lambda pid:ver+vin(pid))
stage("opusV","claude-opus-5-5",lambda pid:ver+vin(pid))
def objs(txt):
    dec=json.JSONDecoder(); out=[]; i=0
    while True:
        j=txt.find("{",i)
        if j<0: return out
        try: o,end=dec.raw_decode(txt[j:]); out.append(o); i=j+end
        except Exception: i=j+1
def verdicts(tag,pid):
    d=json.load(open(f"{E}/v/out/{tag}-{pid}.json")); 
    for o in reversed(objs(str(d["result"]))):
        if "verdicts" in o: return o["verdicts"]
    return []
def mk_chal(pid):
    first=verdicts("sonnetV",pid)
    return chal+json.dumps({"sentences":json.load(open(f"{E}/vin_{pid}.json"))["sentences"],
                            "quotes":json.load(open(f"{E}/vin_{pid}.json"))["quotes"],
                            "first_verifier_verdicts":first},ensure_ascii=False,indent=1)
stage("opusChallengesSonnet","claude-opus-5-5",mk_chal)
open(f"{E}/v/out/progress.txt","a").write("ALLDONE\n")
