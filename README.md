There are two programming tasks included in this repository.
1. Generate a timing map
   code architecture:
create_map-> create_cosworth_timing_map.py … This code creates the mapping tables.
data -> timing_maps -> /2024-07-11_10/command_line_timing_map_0_ms.txt … This is where the timing maps are saved. For example this is a timing map of 0ms saved in a directory which is the execution time. This map was created from the command line and not test automation.
scripts-> question_1 -> test_create_map:
test_cosworth_1.py … Contains all the parameterised pytest test cases.  
conftest.py … some fixtures for set up of all pytest test cases, creates the log directory before pytests are executed.
pytest.ini … initialising the custom markers.

How to use or test:
Unzip the code found in CosworthCodeForQ1Q2.zip in a suitable location which can execute python3 scripts and use pytest framework.

To run from Command line:

cd create_map.
python3 create_cosworth_timing_map.py 100 To create a 100ms and 3000ms map respectively.
> Subdirectory '../data/timing_maps/2024-07-11_15-58/' created.
cd ../data/timing_maps/2024-07-11_15-5c  To view the 100ms and 3000ms maps.


To run using Pytest Parameterisation:

cd scripts/question_1/test_create_map.
pytest will run 1035 parameterised test cases in 103 sec 
pytest -v -s test_cosworth_1.py -m "priorities" will execute all the tests with “priorities” as a mark

cd ../data/timing_maps/204-07-11_16-11/ to view the maps

2. Python Regular expression:

Given a certain log output produce a single python script or pseudo code which uses regex to extract the OS Version,

check_linux_os -> check_os_version.py … This code accepts a string to search like “OS Version” and the name of a log to search within.
data-> linux_logs … this directory contains two logs one with the OS Version and another without.
scripts->question_2->test_linux_version->test_linux_version_2.py …this is the location of the pytest parameterised test cases (It may appear to be over kill as it’s a relatively simple script but it was intended to maintain the structure of question 1).

How to use or test:
Unzip the code found in CosworthCodeForQ1Q2.zip in a suitable location which can execute python3 scripts and use pytest framework.

To run from Command line:

cd check_linux_os.
python3 check_os_version.py “OS Version” outputlog1.log
>FOUND : OS Version: kappa 6.2.0 (Release) Mar 15 2021

To run using Pytest Parameterisation:

cd scripts/question_2/test_linux_version
pytest -v -s will run 2 parameterised test cases 

