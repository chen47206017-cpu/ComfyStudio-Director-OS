import json
from pathlib import Path


CONFIG = Path(
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

        return self.config.get(
            "providers",
            []
        )


    def select(self,name=None):

        if not name:

            name=self.config.get(
                "default_provider"
            )


        for p in self.providers():

            if p["id"]==name:

                return p


        return None



router_service=RouterService()

