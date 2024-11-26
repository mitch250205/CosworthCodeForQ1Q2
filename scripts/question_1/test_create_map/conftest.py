import pytest
import os
from glob import glob
from create_map.create_cosworth_timing_map import create_timing_map_output_dir
import glob

test_execution_dir = None


@pytest.fixture(scope='session', autouse=True)
def create_map_directory():
    global test_execution_dir
    test_execution_dir = create_timing_map_output_dir()


@pytest.fixture(scope='session', autouse=True)
def search_and_assert_file():
    # This fixture will run after all tests
    yield  # This ensures the fixture runs at the end
    PARTIAL_FILE_NAME = 'timing_map_3000_ms'

    matching_dirs = [d for d in glob.glob(test_execution_dir, recursive=True) if os.path.isdir(d)]
    for directory in matching_dirs:
        files_in_directory = os.listdir(directory)

    matching_file_count = 0
    # count the number of 3000ms files in the log dir
    for file_name in files_in_directory:
        if PARTIAL_FILE_NAME in file_name:
            matching_file_count += 1

    assert matching_file_count >= len(files_in_directory)/2, f" numbers of '{PARTIAL_FILE_NAME}' dont match in '{test_execution_dir}'"


# this is designed to capture the test case name so it can be added to the map file
@pytest.fixture(scope='function')
def testcase_map_file(request):
    name = request.node.name
    output_file_name = test_execution_dir + '_' + name
    return output_file_name


