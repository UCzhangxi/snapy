# run_bryan_balance_ic.cmake: examples/bryan.cpp problem/balance-ic (#250 D1)
# on a 200 x 16 rest column (dT = 0) run to t = 0. With one pass allowed the
# moist IC must stop with the cap error; with the default cap it must converge.

file(READ "../bin/bryan.yaml" config)
string(REPLACE "nx2: 400" "nx2: 16" config "${config}")
string(REPLACE "tlim: 1000." "tlim: 0." config "${config}")
string(REPLACE "dT: 2.0" "dT: 0." config "${config}")
string(REPLACE "balance-ic: false" "balance-ic: true" config "${config}")
file(WRITE "bryan_balance_ic.yaml" "${config}")
string(REPLACE "balance-ic-passes: 12" "balance-ic-passes: 1" config
       "${config}")
file(WRITE "bryan_balance_ic_cap.yaml" "${config}")

execute_process(
  COMMAND ../bin/bryan.${buildl} -i bryan_balance_ic_cap.yaml
  RESULT_VARIABLE res
  OUTPUT_VARIABLE out
  ERROR_VARIABLE out)
message("${out}")
if(res EQUAL 0)
  message(FATAL_ERROR "balance-ic-passes: 1 was accepted")
endif()
if(NOT out MATCHES "balance-ic did not converge in 1 passes")
  message(FATAL_ERROR "balance-ic-passes: 1 failed without the cap error")
endif()

execute_process(
  COMMAND ../bin/bryan.${buildl} -i bryan_balance_ic.yaml
  RESULT_VARIABLE res
  OUTPUT_VARIABLE out
  ERROR_VARIABLE out)
message("${out}")
if(NOT res EQUAL 0)
  message(FATAL_ERROR "balance-ic did not converge: ${res}")
endif()
