import json
from pathlib import Path


CONFIG=Path(
"runtime/providers/providers.json"
)


class RouterService:


    def __init__(self):

        self.config=json.loads(
            CONFIG.read_text(
                encoding="utf-8"
            )
        )


    def providers(self):

        return self.config["providers"]



    def select(self,name=None):

        if not name:
            name=self.config["default_provider"]


        for p in self.config["providers"]:

            if p["id"]==name:
                return p


        raise Exception(
            "Provider not found"
        )



router_service=RouterService()

