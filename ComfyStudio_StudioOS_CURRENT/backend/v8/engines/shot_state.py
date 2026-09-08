

STATES=[

"DRAFT",

"ASSET_CHECK",

"CANON_CHECK",

"PROMPT_READY",

"QUEUE",

"GENERATING",

"QC",

"DONE",

"REFERENCE_READY"

]


def set_state(shot,state):

    if state not in STATES:

        raise Exception(
        "invalid state"
        )


    shot["status"]=state

    return shot


