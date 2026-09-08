
import json
from pathlib import Path


CONFIG = Path(
"runtime/providers/providers.json"
)


class ModelRouter:


    def __init__(self):

        self.config=json.loads(
            CONFIG.read_text(
            encoding="utf-8")
        )


    def get_provider(self,name=None):

        if not name:

            name=self.config[
            "default_provider"
            ]


        for p in self.config["providers"]:

            if p["id"]==name:

                return p


        raise Exception(
        f"Provider not found:{name}"
        )



router=ModelRouter()

