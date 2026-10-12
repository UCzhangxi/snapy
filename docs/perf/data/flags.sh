#!/bin/bash
source /tmp/claude-0/venv/bin/activate
B=/home/user/survey/build/bin/perf_step.release
F=/home/user/perf/flags; cd $F
run() { # name envs...
  local name=$1; shift
  ( env "$@" PERF_STEPS=200 PERF_COUNT=3 PERF_DUMP=$F/${name}_dry.pt $B -i /home/user/perf/dry2d.yaml > $F/${name}_dry.log 2>&1 ) &
  ( env "$@" PERF_STEPS=200 PERF_COUNT=3 PERF_KINETICS=1 PERF_DUMP=$F/${name}_moist.pt $B -i /home/user/perf/moist2d.yaml > $F/${name}_moist.log 2>&1 ) &
  wait
  for d in dry moist; do
    k=$(grep -o "leaf_ops_per_step=[0-9.]*" $F/${name}_$d.log)
    if [ "$name" != default ]; then
      c=$($B --compare $F/default_$d.pt $F/${name}_$d.pt)
      p=$(diff <(grep "^cycle=" $F/default_$d.log | head -200) <(grep "^cycle=" $F/${name}_$d.log | head -200) > /dev/null && echo print_same || echo print_DIFF)
    fi
    echo "$name $d $k $c $p"
  done
}
run default X=0
run geom SNAP_GEOM_CACHE=1
run skiplim SNAP_SKIP_STAGE_LIMITER=1
run screens SNAP_DEVICE_SCREENS=1
run fixvap SNAP_DEVICE_FIX_VAPOR=1
run print SNAP_BATCH_PRINT=1
run carry SNAP_FUSED_CARRY=1
run cov SNAP_FUSED_COV=1
run refsmem SNAP_REF_X1_SMEM=1
run all SNAP_GEOM_CACHE=1 SNAP_SKIP_STAGE_LIMITER=1 SNAP_DEVICE_SCREENS=1 SNAP_DEVICE_FIX_VAPOR=1 SNAP_BATCH_PRINT=1 SNAP_FUSED_CARRY=1 SNAP_FUSED_COV=1 SNAP_REF_X1_SMEM=1
