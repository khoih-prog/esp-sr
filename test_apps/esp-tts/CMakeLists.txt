# This is the project CMakeLists.txt file for the test subproject
cmake_minimum_required(VERSION 3.5)

# Include the components directory of the main application:
#
# Check which components directory exists
if(EXISTS "$ENV{IDF_PATH}/tools/test_apps/components")
    set(EXTRA_COMPONENT_DIRS "$ENV{IDF_PATH}/tools/test_apps/components"
                            "../../../esp-sr")
elseif(EXISTS "$ENV{IDF_PATH}/tools/unit-test-app/components")
    set(EXTRA_COMPONENT_DIRS "$ENV{IDF_PATH}/tools/unit-test-app/components"
                            "../../../esp-sr")
else()
    message(FATAL_ERROR "Neither test_apps/components nor unit-test-app/components found in IDF_PATH")
endif()

include($ENV{IDF_PATH}/tools/cmake/project.cmake)
project(esp_sr_test)
