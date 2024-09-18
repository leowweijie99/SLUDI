import os
import subprocess as sub
import json
import javalang
import re

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
TEST_LOG_DIR = SCRIPT_DIR + '/knowledge/_test_logs'
DOWNLOADS_DIR = SCRIPT_DIR + '/knowledge/_downloads'

INCOMPATIBILITIES_JSON_FILE = SCRIPT_DIR + '/incompatibilities.json'
KNOWLEDGE_JSON_FILE = SCRIPT_DIR + '/knowledge.json'

def get_test_result(id: str) -> bool:
    """
    Reads the project's test log and checks for the build status.

    This function scans the project's test log to determine whether the build was successful or failed. It searches for the keywords 'BUILD SUCCESS' and 'BUILD FAILURE' in the log. 

    If 'BUILD SUCCESS' is found, the function returns True. 
    If 'BUILD FAILURE' is found, the function returns False.

    :return: A boolean indicating the build status. Returns True for success, and False for failure.
    """
    test_log_path = TEST_LOG_DIR + '/' + id + '/test.log'
    fail_msg = "BUILD FAILURE"
    with open(test_log_path, 'r') as fr:
        lines = fr.readlines()
    for i in range(len(lines)):
        if fail_msg in lines[i].strip():
            return False
    return True


def clone_project(client: str, url: str, sha: str) -> None:
    """
    Clones a Github project into the '_downloads' directory.

    This function takes in the client name, repository URL, and commit SHA, 
    and clones the project into the '_downloads' directory using the provided commit SHA.

    Args:
        client (str): Name of the repository client.
        url (str): The URL of the repository.
        sha (str): The SHA of the specific commit to be cloned.

    Returns:
        None
    """
    print(f"Cloning project {client} from {url}")
    cwd = os.getcwd()
    os.chdir(DOWNLOADS_DIR)
    sub.run('git clone ' + url, shell=True)
    os.chdir(DOWNLOADS_DIR + '/' + client)
    sub.run('git checkout ' + sha, shell=True)
    os.chdir(cwd)


def changeLibVersion(client: str, lib: str, lib_version: str,
                     downloads_dir=DOWNLOADS_DIR) -> None:
    client_dir = downloads_dir + '/' + client
    for dir_path, subpaths, files in os.walk(client_dir):
        for f in files:
            if f == 'pom.xml':
                pom_file = dir_path + '/' + f
                changeLibVersionOfOnePomFile(lib, lib_version, pom_file)
                

def changeLibVersionOfOnePomFile(lib: str, lib_version: str, pom_file: str) -> None:
    group_id = lib.split(':')[0]
    artifact_id = lib.split(':')[1]
    fr = open(pom_file, 'r', encoding='utf-8')
    lines = fr.readlines()
    fr.close()
    for i in range(len(lines)):
        if '<groupId>' + group_id + '</groupId>' in lines[i]:
            if '<artifactId>' + artifact_id + '</artifactId>' in lines[i + 1]:
                lines[i + 2] = re.sub('\<version\>.*\<\/version\>',
                                      '<version>' + lib_version + '</version>',
                                      lines[i + 2])
    fw = open(pom_file, 'w', encoding='utf-8')
    fw.write(''.join(lines))
    fw.close()


def get_knowledge_info(id: str, file_path: str) -> dict | None:
    """
    Reads a JSON file and searches for an object with the specified ID.

    Args:
        id (str): The ID to search for in the JSON data.
        file_path (str): The path to the JSON file.

    Returns:
        dict or None: The dictionary representing the object if the ID is found,
                      otherwise returns None.
    """
    try:
        with open(file_path, 'r') as file:
            clients_info = json.load(file)

        for ci in clients_info:
            if ci['id'] == id:
                return ci
        return None
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except json.JSONDecodeError:
        print(f"Error decoding JSON in file: {file_path}")


def write_knowledge_info(ci: dict, file_path: str = KNOWLEDGE_JSON_FILE) -> bool:
    """
    Appends the given client info to a JSON file.

    The function reads the existing data, updates the client info if exists, or appends the new client info and writes 
    the updated data back to the file.

    Args:
        ci (dict): The client information to be appended.
        file_path (str): The path to the JSON file. Defaults to `KNOWLEDGE_JSON_FILE`.

    Returns:
        None
    """
    try:
        with open(file_path, 'r') as file:
            clients_info = json.load(file)
    except FileNotFoundError as e:
        print(e)
        exit(-1)

    if get_knowledge_info(ci['id'], file_path) == None:
        clients_info.append(ci)

    for i in range(len(clients_info)):
        if ci['id'] == clients_info[i]['id']:
            clients_info[i] = ci.copy()
            break

    try:
        with open(KNOWLEDGE_JSON_FILE, 'w') as fw:
            json.dump(clients_info, fw, indent=2)
            return True
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error processing file {file_path}: {e}")
        return False

def search_for_file(client: str, target_file_name: str) -> str | None:
    """
    Searches for a specified file within a client's project directory under the _downloads directory.

    This function searches the directory tree of the specified client's project located in the 
    `_downloads` directory, looking for a file that matches the given name. If the file is found, 
    the full path to the file is returned. Else, `None` is returned.

    Args:
        client (str): The name of the client directory within the `_downloads` directory.
        target_file_name (str): The name of the file to search for.

    Returns:
        str | None: The full path to the target file if found, otherwise `None`.
    """
    print(f"Searching for file: {target_file_name}..")
    start_path = os.path.join(DOWNLOADS_DIR, client)
    for root, dirs, files in os.walk(start_path):
        if target_file_name in files:
            return os.path.join(root, target_file_name)
    return None

def get_method_by_line_no(source: str, line_no: int) -> str:
    """
    Given the source code of a Java file and a line number, this function uses the javalang library to identify and 
    return the full method in which the specified line number resides.

    Args:
        source (str): The Java source code as a string.
        line_no (int): The line number for which the containing method should be found.

    Returns:
        str: The complete source code of the method that contains the given line number. If the line number is not 
             within any method or the line number is invalid, it returns an empty string or appropriate message.
    """
    tree = javalang.parse.parse(source)
    methods = []
    
    for path, node in tree:
        if isinstance(node, javalang.tree.MethodDeclaration):
            methods.append(node)
    for method in methods:
        if (method.position and method.position.line <= line_no):
            if hasattr(method, 'body'):
                last_line = method.body[-1].position.line if method.body and method.body[-1].position else method.position.line
                if last_line >= line_no:
                    method_lines = source.splitlines()[method.position.line - 1 : last_line+1]
                    return "\n".join(method_lines)
    return source.splitlines()[line_no-1]


def get_code_from_source(client_info: dict) -> str:
    file_path = search_for_file(client_info["client"], client_info["file_name"])
    if not file_path:
        return ""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            lines = file.readlines()
        source = "".join(lines)
    except Exception as e:
        print(e)
        return ""
    method_body = get_method_by_line_no(source, int(client_info["line_no"]))
    return method_body if method_body else ""