import pytest
import logging
import os
import subprocess
from src.ssh_client import SSHClient

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

#global vars
HOST = "192.168.56.12"
USERNAME = "adouhani"
FILENAME = "syslog"
REMOTE_FILE_PATH = f"/var/log/{FILENAME}"
LOCAL_FILE_PATH = f"./{FILENAME}"

FILES_PATH = "/tmp"
FILES = [
    (f"{FILES_PATH}/file1.txt", 1024),
    (f"{FILES_PATH}/file2.txt", 2048),
    (f"{FILES_PATH}/file3.txt", 512),
    (f"{FILES_PATH}/file4.txt", 4096),
    (f"{FILES_PATH}/file5.txt", 256)
]

@pytest.fixture(scope="module")
def ssh_client():
    """Fixture to establish an SSH connection."""
    #setup
    logger.info("Setting up...")
    client = SSHClient(host=HOST, username=USERNAME)
    client.connect()
    assert client.is_connected() == True, f"Error checking connection."
    # for test case 3
    create_remote_files(client,FILES)

    yield client

    #teardown
    logger.info("Tearing down : closing SSH connnection and removing files...")
    client.close()
    result = subprocess.run(["rm", LOCAL_FILE_PATH], capture_output=True, text=True)
    assert result.returncode == 0, f"Error removing {LOCAL_FILE_PATH} : {result.stderr}"

    
# Test case 1
def test_ssh_connection(ssh_client):
    """
    Verify SSH connection by checking if the file exists.
    """
    logger.info(f"Testing SSH connection by checking if {FILENAME} exists.")
    cmd = f"ls {REMOTE_FILE_PATH}"
    output, error = ssh_client.exec_command(cmd)
    
    assert error == "", f"Error executing command: {error}"
    assert FILENAME in output, f"{FILENAME} file not found"

# Test case 2
def test_file_copy(ssh_client):
    """
    Test copying a file from a remote machine to the local machine and check CRON job occurrences per day.
    """
    logger.info("Step 1 : copying file from remote machine to local")
    ssh_client.copy_file_from_remote(REMOTE_FILE_PATH, LOCAL_FILE_PATH)

    assert os.path.exists(LOCAL_FILE_PATH), "File copy failed"
    logger.info("File successfully copied to local machine")

    logger.info("Step 2 : check CRON job occurrences per day")
    with open(LOCAL_FILE_PATH, 'r') as file:
        occurrences = {}
        for line in file:
            if 'CRON' in line:
                # Extract the date from the log (format: 'Mar  5 00:17:01 vm2 CRON...')
                date = ' '.join(line.split()[:2])  # Get the first 2 elements (month, date)
                occurrences[date] = occurrences.get(date, 0) + 1
        logger.debug(f"occurrences = {occurrences}")

    # Check that there are occurrences for each day
    for date, count in occurrences.items():
        assert count > 0, f"Expected CRON logs for {date}, but found {count} occurrences."

# Test case 3
def test_check_files_on_remote(ssh_client):
    """
    Test that files created on set up exist on remote machine and the size is as expected.
    """
    for file_path, expected_size in FILES:
        logger.info(f"Step 1 : check if file {file_path} exists.")
        command = f"ls {file_path}"
        output, error = ssh_client.exec_command(command)
        if error:
            logger.error(f"File {file_path} does not exist: {error}")

        logger.info(f"Step 2 : check if size of {file_path} is as expected.")
        command = f"stat --format=%s {file_path}"
        output, error = ssh_client.exec_command(command)
        if error:
            logger.error(f"Error while getting size of {file_path}: {error}")
        file_size = int(output)

        assert file_size == expected_size, f"File {file_path} size mismatch: expected {expected_size} bytes, got {file_size} bytes."

def create_remote_files(ssh_client, files):
    """
    Creates files with random content and a specific size on the remote machine.
    """
    for file_path, size in files:
        command = f"head -c {size} /dev/urandom > {file_path}"
        logger.info(f"Creating file {file_path} with {size} bytes on the remote machine.")
        output, error = ssh_client.exec_command(command)
        if error:
            logger.error(f"Error while creating {file_path}: {error}")
        else:
            logger.debug(f"File {file_path} successfully created.")

    logger.info("All files have been created.")