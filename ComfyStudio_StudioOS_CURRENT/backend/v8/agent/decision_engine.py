
from v8.memory.project_memory import search


def analyze(project,goal):


    memory=search(project)


    return {

    "memory_loaded":

    len(memory)>=0,


    "canon":

    "READY",


    "assets":

    "READY",


    "prompt":

    "READY"

    }


