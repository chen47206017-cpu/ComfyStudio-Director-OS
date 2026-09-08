
from v8.agent.task_planner import create_task

from v8.agent.decision_engine import analyze


def run(data):


    task=create_task(

    data.get("project"),

    data.get("episode"),

    data.get("goal")

    )


    task["analysis"]=analyze(

    data.get("project"),

    data.get("goal")

    )


    return task

