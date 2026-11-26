"""Build 8 verifier inputs (4 papers x versions A/B) with 6 subtle planted errors each.
Base = the reader's original sentences; quotes = the same quotes as the earlier test."""
import json,sys,os
sys.path.insert(0,"/home/user/Skill-Optimizer/skills/research-matrix/scripts")
from common import split_sentences
E="/tmp/claude-0/-home-user-Skill-Optimizer/32faaa39-f790-5f14-83c0-16c82a453572/scratchpad/exp"
V="/home/user/Skill-Optimizer/results/2026-11-26-overclaim-pipeline-and-verifier-test/verifier_test"
OUT=os.path.dirname(os.path.abspath(__file__))
base={p["id"]:p for p in json.load(open(f"{E}/sonnet_lrm.json"))["papers"]}
M={ # (pid,ver): [(sentence_id, old, new, type)]
("india2025","A"):[("introduction.1","can create","creates","HEDGE"),
 ("methodology.1","eight blocks","eight rural blocks","ADD"),
 ("methodology.2","two as comparison","two as matched comparison","ADD"),
 ("results.3","at endline","at midline","NUMBER"),
 ("discussion.3","They did not apply advanced statistics,","They did not apply advanced statistics because of the small sample,","CAUSE"),
 ("discussion.4","scale-up of tailor-made training.","scale-up of tailor-made training in all low- and middle-income countries.","QUANT")],
("india2025","B"):[("introduction.2","three implementation phases","two implementation phases","NUMBER"),
 ("methodology.3","402 vs 202","402 vs 220","NUMBER"),
 ("methodology.4","compared by chi-square (P < 0.05)","compared by chi-square tests and logistic regression (P < 0.05)","ADD"),
 ("results.1","did not differ","was significantly higher in the intervention arm","HEDGE"),
 ("results.2","63.8% vs 41.2%","63.8% vs 47.2%","NUMBER"),
 ("discussion.1","digital literacy and its elements","digital literacy and all its elements","QUANT")],
("brink2022","A"):[("introduction.2","very little is known","nothing is known","HEDGE"),
 ("methodology.1","(five males, seven females)","(seven males, five females)","NUMBER"),
 ("methodology.3","were recorded digitally.","were recorded digitally and transcribed in full by an external service.","ADD"),
 ("results.1","to the pupils","to the teachers","SWAP"),
 ("results.3","The teachers did not experience","Most teachers did not experience","QUANT"),
 ("discussion.2","choice of content and method.","choice of content and method, a gap they link to teacher education.","CAUSE")],
("brink2022","B"):[("introduction.1","to describe lower","to explain lower","SWAP"),
 ("introduction.3","experience the teaching","experience and evaluate the teaching","ADD"),
 ("methodology.1","were strategically chosen.","were strategically chosen from schools across the country.","ADD"),
 ("methodology.2","September 2019","September 2020","NUMBER"),
 ("theory.1","knowledge, beliefs, purposes","knowledge, beliefs, emotions, purposes","ADD"),
 ("discussion.1","a common knowledge base","a common curriculum","SWAP")],
("tpack2024","A"):[("introduction.1","affects their","improves their","CAUSE"),
 ("methodology.2","at Al-Qasmi Academic College of Education.","at Al-Qasmi Academic College of Education, in their final year of study.","ADD"),
 ("methodology.4","Ten experimental-group participants were interviewed","Ten participants from each group were interviewed","QUANT"),
 ("results.2","p = 0.001)","p = 0.01)","NUMBER"),
 ("discussion.1","guided reflection and peer dialogue","guided reflection, peer dialogue and teaching experience","CAUSE"),
 ("discussion.3","are self-reported,","are self-reported and unvalidated,","ADD")],
("tpack2024","B"):[("introduction.2","and how DVR use affects them","and why DVR use affects them","SWAP"),
 ("methodology.1","A mixed methods approach was used.","A mixed methods approach combining a survey, interviews and classroom observation was used.","ADD"),
 ("methodology.2","pre/post design","pre/post/delayed post design","ADD"),
 ("results.2","in the TPACK domains","in all seven TPACK domains","QUANT"),
 ("discussion.2","by prospective and in-service teachers","by all teachers","QUANT"),
 ("theory.1","prospective teacher knowledge","teacher knowledge","QUANT")],
("piu2026","A"):[("introduction.1","6-week","8-week","NUMBER"),
 ("methodology.2","aged 12–18","aged 12–17","NUMBER"),
 ("methodology.3","and the short DGI.","and the short DGI, all with established reliability.","ADD"),
 ("results.3","−1.675]","−1.575]","NUMBER"),
 ("discussion.1","self-reported changes","changes","HEDGE"),
 ("discussion.3","and a single province.","a single province and a short follow-up.","ADD")],
("piu2026","B"):[("introduction.2","than a wait-list control group","than an active control group","SWAP"),
 ("methodology.1","at a community center","at a school","SWAP"),
 ("methodology.4","5,000 bootstrap","10,000 bootstrap","NUMBER"),
 ("theory.1","to inform the intervention logic","to explain the intervention effects","CAUSE"),
 ("results.1","DGI, F(1, 204) = 26.53, p < 0.001, ηp² = 0.115; and DSE, F(1, 204) = 18.62, p < 0.001, ηp² = 0.084","DGI, F(1, 204) = 26.53, p < 0.001, ηp² = 0.084; and DSE, F(1, 204) = 18.62, p < 0.001, ηp² = 0.115","NUMBER"),
 ("discussion.2","indicated DGI had","indicated DSE had","SWAP")]}
key=[]
for (pid,ver),muts in M.items():
    sents={}
    for f in ["introduction","methodology","theory","results","discussion"]:
        for k,s in enumerate(split_sentences(base[pid][f]),1): sents[f"{f}.{k}"]=s
    for sid,old,new,typ in muts:
        assert sid in sents and sents[sid].count(old)==1,(pid,ver,sid,old,sents.get(sid))
        sents[sid]=sents[sid].replace(old,new)
        key.append({"file":f"{pid}_{ver}","pid":pid,"id":sid,"type":typ,"old":old,"new":new})
    q=json.load(open(f"{V}/vin_{pid}.json"))["quotes"]
    json.dump({"sentences":[{"id":i,"sentence":s} for i,s in sents.items()],"quotes":q},
              open(f"{OUT}/in_{pid}_{ver}.json","w"),ensure_ascii=False,indent=1)
json.dump(key,open(f"{OUT}/seedkey.json","w"),ensure_ascii=False,indent=1)
print(len(key),"planted errors in",len(M),"files")
