# fixture for tools/tests/test_do_cards.py: the build options a needs-build-option card may name
option(NETCDF "Build with netcdf support" ON)
if(APPLE)
  option(PNETCDF "Build with pnetcdf support" OFF)
else()
  option(PNETCDF "Build with pnetcdf support" ON)
endif()
