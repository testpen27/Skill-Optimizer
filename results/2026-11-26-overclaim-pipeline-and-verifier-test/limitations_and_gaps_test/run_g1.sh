#!/bin/bash
E=/tmp/claude-0/-home-user-Skill-Optimizer/32faaa39-f790-5f14-83c0-16c82a453572/scratchpad/exp
T=/home/user/Skill-Optimizer/results/2026-11-26-overclaim-pipeline-and-verifier-test/limitations_and_gaps_test
one() { pid=$1; w=$E/g/work/$pid; mkdir -p $w; cp $E/papers/$pid.txt $w/paper.txt
  ( cd $w && claude -p "$(cat $T/stage1_prompt_v3.txt)

The id for this paper is: $pid" --model claude-haiku-5-5 --output-format json --setting-sources project --allowedTools Read </dev/null > $E/g/out/s1-$pid.json 2> $E/g/out/s1-$pid.err )
  echo "s1 $pid rc=$?" >> $E/g/out/progress.txt; }
one india2025 & one piu2026 & wait
one brink2022 & one tpack2024 & wait
echo "s1 DONE" >> $E/g/out/progress.txt
