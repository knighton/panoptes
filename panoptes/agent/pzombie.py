from random import randint

from panoptes.agent.agent import Agent
from panoptes.ling.english import English


class PhilosophicalZombie(Agent):
    def __init__(self):
        # Static state.
        self.english = English()

        # Dynamic state.
        self.reset()

    def reset(self):
        self.user_ids_set = set()

    def new_user(self):
        uid = randint(0, 0x7FFFFFFFFFFFFFFF)
        assert uid not in self.user_ids_set
        self.user_ids_set.add(uid)
        return uid

    def put(self, uid, text):
        assert uid in self.user_ids_set
        dsens = list(self.english.each_dsen_from_text(text))
        if not dsens:
            return

        dsen = dsens[0]
        import json
        print json.dumps(dsen.dump(), indent=4, sort_keys=True)
