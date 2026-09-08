
from v8.agents.script_agent import run as script

from v8.agents.art_agent import run as art

from v8.agents.camera_agent import run as camera

from v8.agents.voice_agent import run as voice

from v8.agents.qc_agent import run as qc

from v8.agents.repair_agent import run as repair



def execute(task):

    return [

    script(task),

    art(task),

    camera(task),

    voice(task),

    qc(task),

    repair(task)

    ]

