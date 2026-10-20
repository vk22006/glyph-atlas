cmake_minimum_required(VERSION 3.21)
project(GlyphAtlas LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include(FetchContent)
FetchContent_Declare(
    Slint
    GIT_REPOSITORY https://github.com/slint-ui/slint.git
    GIT_TAG        release/1
    GIT_SHALLOW    TRUE
    SOURCE_SUBDIR  api/cpp
)
FetchContent_MakeAvailable(Slint)

add_executable(GlyphAtlas src/main.cpp)
slint_target_sources(GlyphAtlas ui/app-window.slint)
target_link_libraries(GlyphAtlas PRIVATE Slint::Slint)

# On Windows, copy slint_cpp.dll to the target executable directory for direct execution
if(WIN32)
    add_custom_command(TARGET GlyphAtlas POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy_if_different
        "${CMAKE_BINARY_DIR}/_deps/slint-build/slint_cpp.dll"
        $<TARGET_FILE_DIR:GlyphAtlas>
    )
endif()
