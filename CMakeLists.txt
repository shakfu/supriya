cmake_minimum_required(VERSION 3.20...3.31)
project(${SKBUILD_PROJECT_NAME} VERSION ${SKBUILD_PROJECT_VERSION} LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

find_package(Python REQUIRED COMPONENTS Interpreter Development.Module)
find_package(nanobind CONFIG REQUIRED)

# --- _shm: Server shared memory interface ---
nanobind_add_module(_shm
    src/supriya/_shm.cpp
    vendor/TLSF-2.4.6/src/tlsf.c
)
target_include_directories(_shm PRIVATE
    vendor/supercollider/common
    vendor/TLSF-2.4.6/src
    vendor
)
if(MSVC)
    target_compile_options(_shm PRIVATE /W4)
else()
    target_compile_options(_shm PRIVATE -Wall -Wextra)
endif()
if(CMAKE_SYSTEM_NAME STREQUAL "Linux")
    target_link_libraries(_shm PRIVATE rt)
endif()
install(TARGETS _shm DESTINATION supriya)

# --- _osc: OSC encode/decode ---
nanobind_add_module(_osc src/supriya/_osc.cpp)
if(MSVC)
    target_compile_options(_osc PRIVATE /W4)
else()
    target_compile_options(_osc PRIVATE -Wall -Wextra)
endif()
install(TARGETS _osc DESTINATION supriya)

# --- Option to embed libscsynth as a nanobind extension ---
option(SUPRIYA_EMBED_SCSYNTH "Build _scsynth extension with embedded libscsynth" OFF)

if(SUPRIYA_EMBED_SCSYNTH)
    set(SC_SOURCE_DIR "" CACHE PATH "Path to SuperCollider source directory")
    set(SC_BUILD_DIR "" CACHE PATH "Path to SuperCollider build directory")

    nanobind_add_module(_scsynth src/supriya/_scsynth.cpp)

    # SC headers
    target_include_directories(_scsynth PRIVATE
        ${SC_SOURCE_DIR}/include/server
        ${SC_SOURCE_DIR}/include/common
        ${SC_SOURCE_DIR}/include/plugin_interface
        ${SC_SOURCE_DIR}/common
    )

    # Pre-built static libs from SC build
    target_link_libraries(_scsynth PRIVATE
        ${SC_BUILD_DIR}/server/scsynth/libscsynth.a
        ${SC_BUILD_DIR}/external_libraries/libtlsf.a
    )

    # Homebrew libsndfile (dynamic)
    find_package(PkgConfig REQUIRED)
    pkg_check_modules(SNDFILE REQUIRED IMPORTED_TARGET sndfile)
    target_link_libraries(_scsynth PRIVATE PkgConfig::SNDFILE)

    # macOS system frameworks required by libscsynth
    if(APPLE)
        target_link_libraries(_scsynth PRIVATE
            "-framework CoreAudio"
            "-framework Accelerate"
            "-framework CoreServices"
            "-framework Foundation"
            "-framework AppKit"
        )
    endif()

    # Linux: pthread and rt
    if(CMAKE_SYSTEM_NAME STREQUAL "Linux")
        target_link_libraries(_scsynth PRIVATE pthread rt)
    endif()

    if(MSVC)
        target_compile_options(_scsynth PRIVATE /W4)
    else()
        target_compile_options(_scsynth PRIVATE -Wall -Wextra)
    endif()

    install(TARGETS _scsynth DESTINATION supriya)
endif()
