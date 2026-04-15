# This is the project CMakeLists.txt file for the test subproject
cmake_minimum_required(VERSION 3.5)

# Include the components directory of the main application:
#
if(IDF_VERSION_MAJOR GREATER_EQUAL 6)
    set(EXTRA_COMPONENT_DIRS "$ENV{IDF_PATH}/tools/unit-test-app/components"
                            "../../../esp-sr")
else()
    set(EXTRA_COMPONENT_DIRS "$ENV{IDF_PATH}/tools/test_apps/components"
                                "../../../esp-sr")
endif()
include($ENV{IDF_PATH}/tools/cmake/project.cmake)
project(esp_sr_test)
