from utils import *
from services import openai_service
from services import anthropic_service

import subprocess

TEST_ENABLED = True

def run(id: str) -> None:
    client_info = get_knowledge_info(id, INCOMPATIBILITIES_JSON_FILE)
    if not client_info:
        print(f"Unable to find incompatibility id {id}..")
        return
    discover_client(client_info)
    change_version = True

    while True:
        user_input = input("Type 'test' to run Maven test build or 'exit' to quit: ")
        if user_input == "exit":
            break
        elif user_input != "test":
            print("Invalid input. Please type 'test' or 'exit'.")
            continue
        
        if TEST_ENABLED:
            test_success = test_upgrade_incompatibility(client_info, change_version)
            if test_success:
                print("Test successful!.")
                return
        # End of Discovery -------------------------------
        try:
            extract_info(client_info)
        except Exception as e:
            print(e)
            return
        code = get_code_from_source(client_info)
        file_path = search_for_file(client_info["client"], client_info["file_name"])
        if code:
            query = f"{client_info['exception']}\n{client_info['exception_info']}\n{code.strip()}"
            print(query)
            send_AI = input("Send to AI to diagnose and resolve this issue? (Y/N): ")
            if send_AI.strip() == "Y":
                #query += f"\nthis occurred after upgrading {client_info['lib']} from {client_info['old']} to {client_info['new']}"
                response = openai_service.query(query)
                print('\n' + response)
                if "pom.xml" in response:
                    open_pom_file(client_info)
                else:
                    subprocess.Popen(["notepad.exe", file_path])
                change_version = False
            prompt = input("Enter prompt manually? (Y/N): ")
            if prompt.strip() == "Y":
                prompt = input("Prompt: ")
                response = anthropic_service.query(prompt)
                print('\n' + response)
        else:
            print(f"Unable to automatically extract information, please refer to {TEST_LOG_DIR}/{id}/test.log for details.")
            break


def discover_client(client_info: dict) -> None:
    client, sha, url = client_info["client"], client_info["sha"], client_info["url"]

    if not os.path.exists(DOWNLOADS_DIR):
        os.makedirs(DOWNLOADS_DIR)
    
    client_dir = f"{DOWNLOADS_DIR}/{client}"
    if not os.path.isdir(client_dir):
        clone_project(client, url, sha)
    else:
        print(f"{client_dir} already exists, reverting changes...")
        cwd = os.getcwd()
        os.chdir(f"{DOWNLOADS_DIR}/{client}")
        sub.run("git checkout .", shell=True)
        os.chdir(cwd)
    
    if not os.path.exists(KNOWLEDGE_JSON_FILE):
        with open(KNOWLEDGE_JSON_FILE, 'w') as file:
            json.dump([], file, indent=2)
    write_knowledge_info(client_info)
    

def test_upgrade_incompatibility(client_info: dict, change_version: bool) -> bool:
    id, client, lib, new, test = client_info['id'], client_info['client'], client_info['lib'], client_info['new'], client_info['test']
    submodule, test_cmd = client_info['submodule'], client_info['test_cmd']
    print(f"Running Test for Maven Project '{client}' with id: {id}...")

    cwd = os.getcwd()
    os.chdir(f"{DOWNLOADS_DIR}/{client}")
    sub.run('mvn install -DskipTests -fn -Denforcer.skip -Dgpg.skip -Drat.skip -Dcheckstyle.skip -Danimal.sniffer.skip', shell=True, stdout=open(os.devnull, 'w'), stderr=sub.STDOUT)
    if submodule != "N/A":
        os.chdir(f"{DOWNLOADS_DIR}/{client}/{submodule}")
    sub.run(f"mvn test -fn -Drat.ignoreErrors=true -DtrimStackTrace=false -Dtest={test}", shell=True, stdout=open(os.devnull, 'w'), stderr=sub.STDOUT)

    if change_version:
        changeLibVersion(client, lib, new)

    if not os.path.isdir(f"{TEST_LOG_DIR}/{id}"):
        os.makedirs(f"{TEST_LOG_DIR}/{id}")
    test_log_file = f"{TEST_LOG_DIR}/{id}/test.log"

    if submodule != "N/A":
        os.chdir(f"{DOWNLOADS_DIR}/{client}/{submodule}")
    if test_cmd == "N/A":
        test_cmd = f"mvn test -fn -Drat.ignoreErrors=true -DtrimStackTrace=false -Dtest={test}"
    sub.run(test_cmd, shell=True, stdout=open(test_log_file, 'w'), stderr=sub.STDOUT)
    os.chdir(cwd)

    return get_test_result(id)


def extract_info(client_info: dict) -> None:
    """
    Extracts key details about an exception from the provided client_info.

    This function attempts to extract the following details from the test_log:
        - Exception message
        - Cause of the exception
        - Java file where the exception occurred
        - Line number where the exception occurred
    If any of the information cannot be extracted, the fields are set to an empty string ("").
    Args:
        client_info (dict): A dictionary containing details about a client's exception, such as error logs.

    Returns:
        None: This function modifies the 'client_info' dictionary in place and does not return any value.
    """
    print("Extracting Exception and Error Information...\n")
    client_info["exception"], client_info["exception_info"] = find_exception(client_info["id"])
    error_location = find_error_location(client_info['id'], client_info['test'].split('#')[0])
    if error_location:    
        client_info["file_name"] = error_location.strip().split('(')[-1].split(':')[0]
        client_info['line_no'] = error_location.strip().split(')')[0].split(':')[-1]
    else:
        client_info["file_name"], client_info['line_no'] = "", ""
    write_knowledge_info(client_info)
    return


def find_exception(id: str) -> tuple[str, str]:
    test_log_path = f"{TEST_LOG_DIR}/{id}/test.log"
    with open(test_log_path, 'r') as fr:
        lines = fr.readlines()
    for i in range(len(lines)):
        if lines[i].strip().endswith("<<< ERROR!") or lines[i].strip().endswith("<<< FAILURE!"):
            n = i+1
            exception = ""
            while not lines[n].strip().startswith("at "):
                exception += lines[n]
                n+= 1
            
            if not exception:
                raise ValueError("No exception found.")

            exception = exception.split(":")
            if len(exception) == 1:
                return exception[0].strip(), ""
            else:
                return exception[0].strip(), "".join(exception[1:]).strip()
    raise ValueError("No exception found.")


def find_error_location(id: str, test_name: str) -> str:
    test_log_path = f"{TEST_LOG_DIR}/{id}/test.log"
    with open(test_log_path, 'r') as fr:
        lines = fr.readlines()

    for line in lines:
        if line.strip().startswith("at ") and line.strip().endswith(")"):
            line = line.strip().split("at ")[-1]
            if test_name in line.split('(')[1]:
                return line