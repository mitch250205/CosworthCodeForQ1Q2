import pytest
from create_map.create_cosworth_timing_map import create_timing_maps

from create_map.create_cosworth_timing_map import create_timing_map_output_dir

import math
from prettytable import PrettyTable
import argparse
import os

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


def check_priority_3(timing_table):
    # check that priority 3 timestamps are not divisible by 10 due to all Engine status packets are delayed
    count_divisible_by_10: int = sum(arr[0] % 10 == 0 for arr in timing_table if arr[1] == 'Engine Status')
    return count_divisible_by_10


def check_priority_three_shifted_by_1ms(timing_table):
    # test that all p3's have been shift and none are divisible by 10ms because all p3's have
    count_divisible_by_50_minus1: int = sum((arr[0] - 1) % 10*5 == 0 for arr in timing_table if arr[1]
                                            == 'Engine Status') - 1
    return count_divisible_by_50_minus1


def check_num_priority_one(timing_table):
    # test that all p3's have been shift and none are divisible by 10ms because all p3's have
    count_num_priority_one: int = sum(1 for arr in timing_table if arr[1] == 'Network Timeout')
    return count_num_priority_one


def check_num_priority_two(timing_table):
    # test that all p3's have been shift and none are divisible by 10ms because all p3's have
    count_p2: int = sum(1 for arr in timing_table if arr[1] == 'Power State')
    return count_p2


def check_num_priority_three(timing_table):
    # test that all p3's have been shift and none are divisible by 10ms because all p3's have
    count_p3: int = sum(1 for arr in timing_table if arr[1] == 'Engine Status')
    return count_p3


def check_num_priority_four(timing_table):
    # test that all p3's have been shift and none are divisible by 10ms because all p3's have
    count_p4: int = sum(1 for arr in timing_table if arr[1] == 'GPS Position')
    return count_p4


def check_num_priority_four_shifted_1ms(timing_table):
    # test that all p3's have been shift and none are divisible by 10ms because all p3's have
    count_p4 = all(arr[0] - 1 % P4_PERIOD == 0 for arr in timing_table if arr[1] == 'GPS Position')

    return count_p4


def check_num_priority_four_shifted_2ms(timing_table):
    # test that all p3's have been shift and none are divisible by 10ms because all p3's have
    count_p4 = all(arr[0] - 2 % P4_PERIOD == 0 for arr in timing_table if arr[1] == 'GPS Position')

    return count_p4


def check_num_priority_four_shifted_3ms(timing_table):
    # test that all p3's have been shift and none are divisible by 10ms because all p3's have
    count_p4 = all(arr[0] - 3 % P4_PERIOD == 0 for arr in timing_table if arr[1] == 'GPS Position')

    return count_p4



def check_priority_three_shifted_by_2ms(timing_table):
    # test that all p3's have been shift and none are divisible by 10ms because all p3's have
    count_divisible_by_50_minus2: int = sum((arr[0] - 2) % 10*4 == 0 for arr in timing_table if arr[1]
                                            == 'Engine Status') - 1
    return count_divisible_by_50_minus2


def check_priority_1(timing_table):
    # test that all p1's are divisible by 5
    all_divisible_by_5 = all(arr[0] % 5 == 0 for arr in timing_table if arr[1] == 'Network Timeout')
    return all_divisible_by_5


def check_priority_2(timing_table):
    # test that all p2's timestamps are divisible by 8
    count_divisible_by_8 = sum(arr[0] % 8 == 0 for arr in timing_table if arr[1] == 'Power State')
    return count_divisible_by_8


def check_priority_2_shifted_by_1ms(timing_table):
    count_divisible_by_40_minus1 = sum((arr[0] - 1) % 8*5 == 0 for arr in timing_table if arr[1] == 'Power State') - 1
    return count_divisible_by_40_minus1


def search_for_duplicates(timing_table):
    seen = set()
    duplicates = set()

    for signal in timing_table:
        # unpack the data
        sig_time, signal_type = signal
        if sig_time in seen:
            duplicates.add(sig_time)
        else:
            seen.add(sig_time)
    return len(duplicates)


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
            # catches the 1002ms case
            total_number_of_events = total_number_of_events - 1

    return total_number_of_events


@pytest.fixture()
def calculate_expected_length_of_map(request):
    ms = request.param
    if 0 <= ms <= 3:
        total_number_of_events = ms + 1
    else:
        total_number_of_events = 4
        for signal in signals:
            period = 1000/signal["frequency"]
            num_packets = math.floor(ms/period)
            total_number_of_events += num_packets
        # because sending of packets are delayed according to priority when they are designated to be sent at the
        # same time we need to adjust the expected number at a given boundary time.
        total_number_of_events = handle_boundary_cases(total_number_of_events, ms)


    return total_number_of_events


def generate_timing_map_data(highest_value):

    if highest_value == SMOKE_TEST_DATA:
        data = [(0, 0), (1, 1), (2, 2), (3, 3),(4, 4),(5, 5), (6, 6),
                (20, 20), (39, 39), (40, 40),(41, 41),(42, 42),(43, 43),(44, 44),
                (79, 79),(80,80),(81,81),(2001,2001),(3000,3000),(4001,4001)]
    elif highest_value == MAX_TIMING_MAP_DURATION:
        # set up
        data = [(val, val) for val in range(0, highest_value + 1)]
    elif highest_value == 1000:
        data = [(1000,1000)]
    else:
        data = [(3,3)]
    return data


@pytest.mark.test_all_max_length_map
@pytest.mark.parametrize('timing_map,calculate_expected_length_of_map',
                         generate_timing_map_data(MAX_TIMING_MAP_DURATION),
                         indirect=['calculate_expected_length_of_map'])
def test_full_timing_map_length(testcase_map_file,timing_map, calculate_expected_length_of_map):
    # actual = len(create_timing_map(timing_map))
    # expected = calculate_expected_length_of_map
    # print(f"actual = {actual} expected = {expected}")
    assert len(create_timing_maps(testcase_map_file,timing_map)) == calculate_expected_length_of_map


@pytest.mark.smoke_test_map_length
@pytest.mark.parametrize('timing_map,calculate_expected_length_of_map',
                         generate_timing_map_data(SMOKE_TEST_DATA), indirect=['calculate_expected_length_of_map'])
def test_smoke_timing_map_length(testcase_map_file,timing_map, calculate_expected_length_of_map):
    assert len(create_timing_maps(testcase_map_file,timing_map)) == calculate_expected_length_of_map


@pytest.mark.priorities
@pytest.mark.parametrize('timing_map', [1000])
def test_duplicate_timestamps(testcase_map_file,timing_map):
    #  timestamps should be unique, test for max map duration
    assert search_for_duplicates(create_timing_maps(testcase_map_file,timing_map)) == 0


@pytest.mark.priorities
@pytest.mark.parametrize('timing_map', [MAX_TIMING_MAP_DURATION])
def test_priority_one_timestamps(testcase_map_file,timing_map):
    # test that all p1's timestamps are divisible by 5, test for max map duration
    assert check_priority_1(create_timing_maps(testcase_map_file,timing_map)) is True


@pytest.mark.priorities
@pytest.mark.parametrize('timing_map', [1000])
def test_priority_two_timestamps(testcase_map_file,timing_map):
    assert check_priority_2(create_timing_maps(testcase_map_file,timing_map)) == 4/5 * (1000/P2_PERIOD)


@pytest.mark.priorities
@pytest.mark.parametrize('timing_map', [1000])
def test_priority_two_shifted_1ms_timestamps(testcase_map_file,timing_map):
    # one in five P2 signals are shifted by 1ms every cycle duration ignore last one as it is outside max duration
    assert check_priority_2_shifted_by_1ms(create_timing_maps(testcase_map_file,timing_map)) == 1000/(P1_PERIOD * P2_PERIOD) - 1


@pytest.mark.priorities
@pytest.mark.parametrize('timing_map', [MAX_TIMING_MAP_DURATION])
def test_priority_three_timestamps(testcase_map_file,timing_map):
    # test that all p3's have been shifted and no timestamps are divisible by 10ms because
    # all p3's have been shifted in time due to clash with other higher priority signals
    assert check_priority_3(create_timing_maps(testcase_map_file,timing_map)) == 0


@pytest.mark.priorities
@pytest.mark.parametrize('timing_map', [1000])
def test_priority_three_shifted_by_1ms(testcase_map_file,timing_map):
    # 3 p3 should be shifted 1ms every 40 signals and ignore the last one as this is
    # outside the duration under test
    assert check_priority_three_shifted_by_1ms(create_timing_maps(testcase_map_file,timing_map)) == 3*(1000/(P1_PERIOD * P2_PERIOD)) - 1


@pytest.mark.priorities
@pytest.mark.parametrize('timing_map', [1000])
def test_priority_three_shifted_by_2ms(testcase_map_file,timing_map):
    # 1 p3 should be shifted 2ms every 40 signals and ignore the last one as this is
    # outside the duration under test
    assert check_priority_three_shifted_by_2ms(create_timing_maps(testcase_map_file,timing_map)) == 1000/(P1_PERIOD * P2_PERIOD) - 1


@pytest.mark.priorities
@pytest.mark.parametrize('timing_map', [1000])
def test_num_priority_three(testcase_map_file,timing_map):
    assert check_num_priority_three(create_timing_maps(testcase_map_file,timing_map)) == 1000/P3_PERIOD


@pytest.mark.priorities
@pytest.mark.parametrize('timing_map', [MAX_TIMING_MAP_DURATION])
def test_num_priority_one(testcase_map_file,timing_map):
    assert check_num_priority_one(create_timing_maps(testcase_map_file,timing_map)) == MAX_TIMING_MAP_DURATION/P1_PERIOD + 1


@pytest.mark.priorities
@pytest.mark.parametrize('timing_map', [1000])
def test_num_priority_two(testcase_map_file,timing_map):
    assert check_num_priority_two(create_timing_maps(testcase_map_file,timing_map)) == 1000/P2_PERIOD


@pytest.mark.priorities
@pytest.mark.parametrize('timing_map', [1000])
def test_num_priority_four(testcase_map_file,timing_map):
    assert check_num_priority_four(create_timing_maps(testcase_map_file,timing_map)) == 1000/P4_PERIOD


@pytest.mark.priorities
@pytest.mark.parametrize('timing_map', [4000])
def test_num_priority_four_shifted_1ms(testcase_map_file,timing_map):
    assert check_num_priority_four_shifted_1ms(create_timing_maps(testcase_map_file,timing_map)) == 0


@pytest.mark.priorities
@pytest.mark.parametrize('timing_map', [4000])
def test_num_priority_four_shifted_2ms(testcase_map_file, timing_map):
    assert check_num_priority_four_shifted_2ms(create_timing_maps(testcase_map_file, timing_map)) == 0



@pytest.mark.priorities
@pytest.mark.parametrize('timing_map', [4000])
def test_num_priority_four_shifted_3ms(testcase_map_file,timing_map):
    assert check_num_priority_four(create_timing_maps(testcase_map_file,timing_map)) == 4