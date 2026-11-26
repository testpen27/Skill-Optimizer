#!/bin/bash
# usage: run_readers.sh <model-alias> <model-id>
E=/tmp/claude-0/-home-user-Skill-Optimizer/32faaa39-f790-5f14-83c0-16c82a453572/scratchpad/exp
alias=$1; model=$2
for pid in india2025 piu2026 brink2022 tpack2024; do
  w=$E/work/$alias/$pid; mkdir -p $w; cp $E/papers/$pid.txt $w/paper.txt
  ( cd $w && claude -p "$(cat $E/reader_prompt.txt)

The id for this paper is: $pid" --model $model --output-format json --setting-sources project --allowedTools Read </dev/null > $E/out/$alias-$pid.json 2> $E/out/$alias-$pid.err )
  echo "$alias $pid rc=$?" >> $E/out/progress.txt
done
echo "$alias DONE" >> $E/out/progress.txt
