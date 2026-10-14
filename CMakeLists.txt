cmake_minimum_required(VERSION 3.18)

project(rp-externals LANGUAGES C CXX Fortran)

include(ExternalProject)
set_property(DIRECTORY PROPERTY EP_BASE "${CMAKE_BINARY_DIR}/subbuild")

# subbuild job limit
if(NOT DEFINED RP_EXTERNALS_SUBBUILD_JOB_LIMIT)
    set(RP_EXTERNALS_SUBBUILD_JOB_LIMIT 8)
endif()
message(STATUS "RP_EXTERNALS_SUBBUILD_JOB_LIMIT: ${RP_EXTERNALS_SUBBUILD_JOB_LIMIT}")

# stage directory
if(NOT DEFINED RP_EXTERNALS_STAGE_DIR)
    set(RP_EXTERNALS_STAGE_DIR "${CMAKE_BINARY_DIR}/staging")
endif()
message(STATUS "Using stage directory: ${RP_EXTERNALS_STAGE_DIR}")

# import profile
set(profile_file "${CMAKE_CURRENT_LIST_DIR}/profiles/${RP_PLATFORM}-${RP_MILITARY}.cmake")
message(STATUS "Using profile: ${profile_file}")
if(EXISTS "${profile_file}")
    include("${profile_file}")
else()
    message(FATAL_ERROR "Profile file not found: ${profile_file}")
endif()

# import packages
set(package_list "")
foreach(package ${include_packages})
    message(STATUS "Importing package: ${package}")
    include(packages/${package}/recipe.cmake)
endforeach()

foreach(package ${package_list})
    foreach(depend_package ${${package}_DEPEND_PACKAGES})
        message(STATUS "Adding dependency for ${package}: ${depend_package}")
        ExternalProject_Add_StepDependencies(${package} configure ${depend_package})
    endforeach()
endforeach()

install(
    DIRECTORY ${RP_EXTERNALS_STAGE_DIR}/
    DESTINATION .
    USE_SOURCE_PERMISSIONS
)

install(
    DIRECTORY ${RP_EXTERNALS_STAGE_DIR}/bin
    DESTINATION .
    USE_SOURCE_PERMISSIONS
)

install(
    DIRECTORY ${RP_EXTERNALS_STAGE_DIR}/lib
    DESTINATION .
    USE_SOURCE_PERMISSIONS
)
