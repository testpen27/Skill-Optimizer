#!/bin/bash
E=/tmp/claude-0/-home-user-Skill-Optimizer/32faaa39-f790-5f14-83c0-16c82a453572/scratchpad/exp
for pid in india2025 piu2026 brink2022 tpack2024; do
  ( cd $E/grade/$pid && claude -p "$(cat $E/grader_prompt.txt)" --model claude-opus-5-5 --output-format json --setting-sources project --allowedTools Read </dev/null > $E/out/grade-$pid.json 2> $E/out/grade-$pid.err )
  echo "grade $pid rc=$?" >> $E/out/progress.txt
done
echo "grade DONE" >> $E/out/progress.txt
