import re
import sys
import os


def linux_version(version_string, log_file_name):
    # Read the content of the log file

    if version_string == "OS Version":
        version_string = "OS Version\\s*:\\s*(.*)"
    log_dir = os.getcwd()
    if log_dir.find("scripts") > 0:
        log_directory = os.path.join(log_dir, "../../../data/linux_logs/", log_file_name)
    else:
        log_directory = os.path.join(log_dir, "../data/linux_logs/", log_file_name)

    try:
        with open(log_directory, 'r') as file:
            log_content = file.read()
    except Exception as e:
        print(f"Log File Not Found: {log_file_name}")
        sys.exit(1)

    # regex pattern to extract the OS version
    # Define the regex pattern

    # Search for the pattern in the text
    match = re.search(version_string, log_content)
    if match:
        os_version = match.group(1)
        print(f"\nFOUND : OS Version: {os_version}\n")
    else:
        print("\nOS Version not found.\n")
        os_version = None

    return os_version



if __name__ == "__main__":

    expected_num_args = 2

    if len(sys.argv) != expected_num_args + 1:
        print(f"Error: This script requires exactly {expected_num_args} arguments.")
        print("Usage: python check_os_version.py \"OS Version\" logFile.log")
        sys.exit(1)


    # Assuming timing_map is a string; adjust as necessary for your actual implementation
    searchString = sys.argv[1]
    file = sys.argv[2]

    res = linux_version(searchString, file)
