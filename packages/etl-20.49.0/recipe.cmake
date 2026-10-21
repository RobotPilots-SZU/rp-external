set(package_name "etl")
set(${package_name}_DEPEND_PACKAGES "")
set(${package_name}_INCLUDEDIRS "include") # 保持官方的使用方法：<etl/vector.h>
set(LIBRARY_TYPE "header-library")


ExternalProject_Add(${package_name}
    URL "${CMAKE_CURRENT_LIST_DIR}/etl-20.49.0.tar.gz"
    DOWNLOAD_EXTRACT_TIMESTAMP TRUE
    CMAKE_ARGS
        -DCMAKE_TOOLCHAIN_FILE=${RP_CMAKE_TOOLCHAIN_FILE}
        -DCMAKE_INSTALL_PREFIX=${RP_EXTERNALS_STAGE_DIR}
        -DCMAKE_INSTALL_LIBDIR=lib
        -DCMAKE_BUILD_TYPE=${CMAKE_BUILD_TYPE}
        -DBUILD_TESTS=OFF
        -DNO_SYSTEM_INCLUDE=OFF

    BUILD_COMMAND
        "${CMAKE_COMMAND}" --build <BINARY_DIR> --config $<CONFIG>
        --parallel ${RP_EXTERNALS_SUBBUILD_JOB_LIMIT}
    INSTALL_COMMAND
        "${CMAKE_COMMAND}" --install <BINARY_DIR> --config $<CONFIG>
)
