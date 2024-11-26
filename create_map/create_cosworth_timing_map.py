from typing import Any
from datetime import datetime

from prettytable import PrettyTable
import argparse
import os
import re

# Task details
signals = [
    {"name": "Network Timeout", "frequency": 200, "priority": 1},
    {"name": "Power State", "frequency": 125, "priority": 2},
    {"name": "Engine Status", "frequency": 100, "priority": 3},
    {"name": "GPS Position", "frequency": 1, "priority": 4},
]
# if you are thinking of modifying ..this parameter should be greater than
MAX_TIMING_MAP_DURATION = 1000
P1_PERIOD = 5
P2_PERIOD = 8
P3_PERIOD = 10
P4_PERIOD = 1000
SMOKE_TEST_DATA = 1
NUMBER_OF_CYCLES_IN_TIMING_MAP = MAX_TIMING_MAP_DURATION/(P1_PERIOD * P2_PERIOD)
PRINT_MAPS = 1



def create_timing_map_output_dir():
    now = datetime.now()
    formatted_now = now.strftime("%Y-%m-%d_%H-%M")
    # Get the current working directory
    cwd = os.getcwd()
    if cwd.find("test_create_map") < 0:
        subdir = f"../data/timing_maps/{formatted_now}/"
    else:
        subdir = f"../../../data/timing_maps/{formatted_now}/"  # Check if the subdirectory exists

    if not os.path.exists(subdir):
        # Create the subdirectory if it doesn't exist
        os.makedirs(subdir)
        print(f"\nSubdirectory '{subdir}' created.\n")
    else:
        subdir = subdir.rstrip('/') + '_' + str(datetime.now().second)
        os.makedirs(subdir)
    return subdir


def clean_filename(filename):
    # Remove the _test prefix
    file = os.path.basename(filename)
    if file.startswith('_test_'):
        file = file[len('_test_'):]

    # Remove the [1000] suffix before the file extension
    file = re.sub(r'\[1000\]$', '', file)

    return file


def create_timing_maps(testcase_map_file, timing_map_length):
    testcase_map_file = clean_filename(testcase_map_file)
    # a timing map of 3000 should be created regardless of the required length

    mapList: list[list[Any]] = create_timing_map(testcase_map_file,3000)

    # unless a length of 3000ms has already been requested create a timing map of that length
    if timing_map_length != 3000:
        mapList = create_timing_map(testcase_map_file,timing_map_length)

    return mapList


def print_timing_maps(testcase_map_file, sorted_result,map_length):
    table = PrettyTable()
    map_directory = os.getcwd()
    if testcase_map_file != "command_line":
        map_time_directory = os.path.join(map_directory, "../../../data/timing_maps/")
    else:
        map_time_directory = os.path.join(map_directory, "../data/timing_maps/")
    subdirs = [os.path.join(map_time_directory, d) for d in os.listdir(map_time_directory) if os.path.isdir(os.path.join(map_time_directory, d))]
    latest_subdir = max(subdirs, key=os.path.getctime)

    # Add columns
    time_column = [item[0] for item in sorted_result]
    signal_column = [item[1] for item in sorted_result]

    table.add_column("Time (ms)", time_column)
    table.add_column("Signal Name", signal_column)
    # get latest log directory

    with open(f'{latest_subdir}/{testcase_map_file}_timing_map_{map_length}_ms.txt', 'w') as w:
        w.write(str(table))
    w.close()


def create_timing_map(testcase_map_file,map_length):
    # Calculate periods (in ms) and add to signals json
    for signal in signals:
        signal["period"] = int(1000 / signal["frequency"])
    # initialise the signal start times with teh first 4 signals
    signal_start_times = {signal["name"]: [signal["priority"] - 1] for signal in signals}
    # Adjust start times to ensure minimum 1ms gap and no overlapping signals
    current_time = 0
    # create the timing map for all time intervals
    while current_time <= map_length:
        for signal in signals:
            # for each signal work out if it is time to transmit for that signal
            if current_time % signal["period"] == 0 and current_time > 0:
                # if there is no conflict in transmission times add the time to the list for the signal eg
                # 'Network Timeout' = {list: 2} [0, 5, 10, 15]
                # 'Power State' = {list: 1} [1, 8, 16]
                # 'Engine Status' = {list: 1} [2, 11]
                # 'GPS Position' = {list: 1} [3]

                # if the timestamp is not already in the list of lists ie its a new timestamp for that signal
                if all(current_time not in start_times for start_times in signal_start_times.values()):
                    # add the timestamp to the signal
                    signal_start_times[signal["name"]].append(current_time)
                else:
                    # there must be a clash of transmission times so get the largest value already transmitted
                    # and add 1
                    max_time = max(
                        time for signal_start_times in signal_start_times.values() for time in signal_start_times)
                    signal_start_times[signal["name"]].append(max_time + 1)

        current_time += 1

    # Initialize an empty list to store results
    results = []

    # Iterate over the dictionary items remove any values which are greater than the map length under test
    for list_name, values in signal_start_times.items():
        # Iterate over the values in each list
        for value in values:
            # Append tuple (value, list_name) to result
            if value <= map_length:
                results.append([value, list_name])
    sorted_result = sorted(results, key=lambda x: x[0])

    if PRINT_MAPS:
        print_timing_maps(testcase_map_file,sorted_result,map_length)

    return sorted_result


def handle_boundary_cases(total_number_of_events,length_of_map):

    if length_of_map % P1_PERIOD == 0 and length_of_map % P3_PERIOD == 0 and not length_of_map % P2_PERIOD == 0 \
            and not length_of_map % P4_PERIOD == 0:
        # handles when P1 and P3 clash (every 10ms) we are expecting 2 packets but due to the clash one is shifted 1ms
        # therefore we need to subtract 1
        total_number_of_events = total_number_of_events - 1

    elif length_of_map % (P1_PERIOD * P2_PERIOD) == 0:
        # catches 5x8ms ..40 80 120 ..1000 etc cases
        # every 40ms the cycle repeats where 3 signals P1,P2 and P3 are being sent at the same time but since
        # two signals are delayed 1ms each we need to subtract the expected number by 2
        if length_of_map % P3_PERIOD == 0 and length_of_map % P4_PERIOD == 0:
            # catches the 1000ms case where 4 signals are to be sent at the same
            # time but have been delayed so we don't count 3 of them
            total_number_of_events = total_number_of_events - 3
        else:
            # on a normal 40ms boundary we would transmit 3 signals at the same time so 2 are delayed
            # and we don't count them
            total_number_of_events = total_number_of_events - 2


    elif (length_of_map - 1) % (P1_PERIOD * P2_PERIOD) == 0:
        # catches 5x8 + 1 ...41 81 121 1001..etc cases
        # as above in the 40 we case should have 3 simultaneous signals but since two are delayed
        # at time 41 we have one sent at 40 another delayed sent at 41 but would still
        # need to subtract an additional event to get the expected sent at 41
        if (length_of_map - 1) % P3_PERIOD == 0 and (length_of_map - 1) % P4_PERIOD == 0:
            # catches the 1001ms case
            total_number_of_events = total_number_of_events - 2
        else:
            total_number_of_events = total_number_of_events - 1

    elif (length_of_map - 2) % (P1_PERIOD * P2_PERIOD) == 0:
        # catches 5x8 + 2 ...44 82 122 1002 ..etc cases
        # as above in the 40 we case should have 3 simultaneous signals but since two are delayed
        # at time 41 we have one sent at 40 another delayed sent at 41 but would still
        # need to subtract an additional event to get the expected sent at 41
        if (length_of_map - 2) % P3_PERIOD == 0 and (length_of_map - 2) % P4_PERIOD == 0:
            # catches the 1000ms case
            total_number_of_events = total_number_of_events - 1

    return total_number_of_events


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Call create_timing_maps from the command line")
    parser.add_argument("length_of_timing_map", help="Input for the required timing map length parameter")

    args = parser.parse_args()

    # Assuming timing_map is a string; adjust as necessary for your actual implementation
    length_timing_map = int(args.length_of_timing_map)

    create_timing_map_output_dir()

    result = create_timing_maps('command_line',length_timing_map)