cmake_minimum_required(VERSION 3.6)

project(Smart-UAV-Return-GNSS-Station)

set(CMAKE_INCLUDE_CURRENT_DIR ON)
set(CMAKE_CXX_STANDARD 11)

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wno-terminate")

set(TARGET_NAME Smart-UAV-Return-GNSS-Station)

set(SOURCES_SQLITE
    sqlite-amalgamation/sqlite3.c
    sqlite-amalgamation/sqlite3.h
)

set(SOURCES
    src/geomap_db.cpp

    include/geomap_db.hpp
)

add_library(${TARGET_NAME}
    ${SOURCES}
    ${SOURCES_SQLITE}
)

target_include_directories(${TARGET_NAME}
    PUBLIC
    include
    sqlite-amalgamation
)

add_executable(test
    test.cpp
)


target_link_libraries(test
    ${TARGET_NAME}
)

add_executable(add_embedding_db
    add_embedding_db.cpp
)

target_link_libraries(add_embedding_db
    ${TARGET_NAME}
)

add_executable(print_table
    print_table.cpp
)

target_link_libraries(print_table
    ${TARGET_NAME}
)

add_executable(get_approximate_location_db
    get_approximate_location_db.cpp
)

target_link_libraries(get_approximate_location_db
    ${TARGET_NAME}
)
