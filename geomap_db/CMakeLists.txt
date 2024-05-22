cmake_minimum_required(VERSION 3.15)

project(Smart-UAV-Return-GNSS-Station)

set(CMAKE_INCLUDE_CURRENT_DIR ON)
set(CMAKE_CXX_STANDARD 11)

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wno-terminate")

set(TARGET_NAME Smart-UAV-Return-GNSS-Station)

find_package(PythonLibs REQUIRED)
add_subdirectory(pybind11)

set(SOURCES_SQLITE
    sqlite-amalgamation/sqlite3.c
    sqlite-amalgamation/sqlite3.h
)

set(SOURCES
    src/geomap_db.cpp
    src/location_seeker.cpp

    include/geomap_db.hpp
    include/location_seeker.hpp
)

add_library(${TARGET_NAME}
    ${SOURCES}
    ${SOURCES_SQLITE}
)

target_include_directories(${TARGET_NAME} PUBLIC
    ${PYTHON_INCLUDE_DIRS}
    pybind11/include
    include
    sqlite-amalgamation
)


add_executable(add_embeddings
    src/add_embeddings.cpp
)

target_link_libraries(add_embeddings
    ${TARGET_NAME}
)

add_executable(print_table
    src/print_table.cpp
)

target_link_libraries(print_table
    ${TARGET_NAME}
)

add_executable(get_aprox_location
    src/get_aprox_location.cpp
)

target_include_directories(get_aprox_location PRIVATE pybind11::embed pybind11::lto)

target_link_libraries(get_aprox_location
    ${TARGET_NAME}
    pybind11::embed
    pybind11::lto
)
