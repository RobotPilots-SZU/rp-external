set(package_name "nanopb")
set(${package_name}_DEPEND_PACKAGES "")
set(${package_name}_INCLUDEDIRS "include/nanopb")
set(LIBRARY_TYPE "library")

if(MCU_PLATFORM)
    set(nanopb_static ON)
else()
    set(nanopb_static OFF)
endif()

ExternalProject_Add(${package_name}
    URL "${CMAKE_CURRENT_LIST_DIR}/nanopb-0.4.9.2.tar.gz"
    DOWNLOAD_EXTRACT_TIMESTAMP TRUE
    CMAKE_ARGS
        -DCMAKE_TOOLCHAIN_FILE:FILEPATH=${RP_CMAKE_TOOLCHAIN_FILE}
        -DCMAKE_INSTALL_PREFIX:PATH=${RP_EXTERNALS_STAGE_DIR}
        -DCMAKE_INSTALL_LIBDIR:STRING=lib
        -DCMAKE_BUILD_TYPE:STRING=${CMAKE_BUILD_TYPE}
        -DBUILD_SHARED_LIBS:BOOL=${RP_EXTERNALS_SHARED}
        -DBUILD_STATIC_LIBS:BOOL=${nanopb_static}
        -Dnanopb_BUILD_RUNTIME:BOOL=ON
        -Dnanopb_BUILD_GENERATOR:BOOL=OFF
    BUILD_COMMAND
        "${CMAKE_COMMAND}" --build <BINARY_DIR> --config $<CONFIG>
        --parallel ${RP_EXTERNALS_SUBBUILD_JOB_LIMIT}
    INSTALL_COMMAND
        "${CMAKE_COMMAND}" --install <BINARY_DIR> --config $<CONFIG>
)
