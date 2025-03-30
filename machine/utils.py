
import os

def path_to_id(workflow_path):
    return os.path.splitext(os.path.normpath(workflow_path).replace('\\', '/'))[0].replace("/", ".")

def id_to_path(workflow_id, json=True):
    if json:
        return os.path.normpath(workflow_id.replace(".", "/") + ".json")
    else:
        return os.path.normpath(workflow_id.replace(".", "/") + ".py")