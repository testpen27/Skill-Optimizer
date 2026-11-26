import json,subprocess,os,glob,concurrent.futures as cf
E="/tmp/claude-0/-home-user-Skill-Optimizer/32faaa39-f790-5f14-83c0-16c82a453572/scratchpad/exp"
R="/home/user/Skill-Optimizer/results/2026-11-26-overclaim-pipeline-and-verifier-test"
T=f"{R}/subtle_error_test"
plain=open(f"{R}/verifier_test/verifier_prompt.txt").read()
comb=open(f"{R}/combined_verifier_test/combined_prompt.txt").read()
files=sorted(os.path.basename(f)[3:-5] for f in glob.glob(f"{T}/in_*.json"))
jobs=[(tag,pr,f) for rep in (1,2) for f in files for tag,pr in ((f"P{rep}",plain),(f"C{rep}",comb))]
def run(j):
    tag,pr,f=j
    out=f"{E}/v3/out/{tag}-{f}.json"
    if os.path.exists(out) and os.path.getsize(out)>100: return tag,f,"cached"
    w=f"{E}/v3/work/{tag}/{f}"; os.makedirs(w,exist_ok=True)
    p=subprocess.run(["claude","-p",pr+open(f"{T}/in_{f}.json").read(),"--model","claude-opus-5-5","--output-format","json","--setting-sources","project"],
                     cwd=w,stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=900)
    open(out,"w").write(p.stdout)
    return tag,f,p.returncode
with cf.ThreadPoolExecutor(3) as ex:
    for r in ex.map(run,jobs):
        open(f"{E}/v3/out/progress.txt","a").write(str(r)+"\n")
open(f"{E}/v3/out/progress.txt","a").write("ALLDONE\n")
