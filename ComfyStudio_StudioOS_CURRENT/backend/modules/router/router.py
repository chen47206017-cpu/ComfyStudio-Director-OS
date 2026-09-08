class ModelRouter:


    def select(self,requirements):


        if requirements.get(
        "character_consistency"
        )=="high":

            return "MINIMAX_H3"


        return "SEEDANCE_2.5"


