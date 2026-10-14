cmake_minimum_required(VERSION 3.24)

# This project only drives ExternalProject; compilers belong to each recipe.
project(rp_external LANGUAGES NONE)

include(ExternalProject)
set_property(DIRECTORY PROPERTY EP_BASE "${CMAKE_BINARY_DIR}/subbuild")

if(NOT EXISTS "${RP_EXTERNALS_RECIPE}")
    message(FATAL_ERROR "RP_EXTERNALS_RECIPE must point to a recipe.cmake")
endif()

if(NOT RP_EXTERNALS_STAGE_DIR)
    set(RP_EXTERNALS_STAGE_DIR "${CMAKE_BINARY_DIR}/staging")
endif()

if(NOT RP_EXTERNALS_SUBBUILD_JOB_LIMIT)
    set(RP_EXTERNALS_SUBBUILD_JOB_LIMIT 8)
endif()

file(MAKE_DIRECTORY "${RP_EXTERNALS_STAGE_DIR}")
include("${RP_EXTERNALS_RECIPE}")

install(DIRECTORY "${RP_EXTERNALS_STAGE_DIR}/" DESTINATION .
        USE_SOURCE_PERMISSIONS)
