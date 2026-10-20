cmake_minimum_required(VERSION 3.21)
project(GlyphAtlas LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# ── Standalone Unicode Core Library (No UI or Slint dependencies) ────────────
add_library(glyph_core STATIC
    src/core/unicode_core.cpp
)
target_include_directories(glyph_core PUBLIC
    src/core
)

# ── Slint UI Integration ──────────────────────────────────────────────────────
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
target_link_libraries(GlyphAtlas PRIVATE Slint::Slint glyph_core)

# On Windows, copy slint_cpp.dll to the target executable directory for direct execution
if(WIN32)
    add_custom_command(TARGET GlyphAtlas POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy_if_different
        "${CMAKE_BINARY_DIR}/_deps/slint-build/slint_cpp.dll"
        $<TARGET_FILE_DIR:GlyphAtlas>
    )
endif()

# ── Focused Unit Tests ────────────────────────────────────────────────────────
enable_testing()
add_executable(test_unicode_core tests/test_unicode_core.cpp)
target_link_libraries(test_unicode_core PRIVATE glyph_core)
add_test(NAME UnicodeCoreTests COMMAND test_unicode_core)
