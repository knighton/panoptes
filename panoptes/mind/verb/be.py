from panoptes.ling.glue.purpose import Purpose
from panoptes.ling.glue.relation import Relation
from panoptes.ling.morph.comparative.comparative import ComparativePolarity
from panoptes.mind.idea import Comparative, Direction, Query, Noun
from panoptes.mind.location import At, NotAt
from panoptes.mind.verb.base import ClauseMeaning, Response


class AgentIsTarget(ClauseMeaning):
    def __init__(self):
        self.purpose = Purpose.INFO
        self.lemmas = ['be']
        self.signatures = [
            [Relation.AGENT, Relation.TARGET],
        ]

    def handle(self, c, memory, (agent_xx, target_xx)):
        if len(agent_xx) != 1:
            return None

        if len(target_xx) != 1:
            return None

        agent_x, = agent_xx
        agent = memory.ideas[agent_x]
        target = memory.ideas[target_xx[0]]
        if isinstance(agent, Noun) and isinstance(target, Comparative):
            if target.polarity == ComparativePolarity.POS and \
                    target.adjective == 'big':
                memory.graph.link(agent_x, 'bigger', target.than_x)
                return Response()
            else:
                pass
        elif isinstance(agent, Noun) and isinstance(target, Direction):
            memory.graph.link(agent_x, target.which, target.of_x)
            return Response()
        else:
            pass

        return None


class AgentTargetQuestion(ClauseMeaning):
    def __init__(self):
        self.purpose = Purpose.WH_Q
        self.lemmas = ['be']
        self.signatures = [
            [Relation.AGENT, Relation.TARGET],
        ]

    def handle(self, c, memory, (agent_xx, target_xx)):
        if len(agent_xx) != 1:
            return None

        if len(target_xx) != 1:
            return None

        agent_x, = agent_xx
        agent = memory.ideas[agent_x]
        target_x, = target_xx
        target = memory.ideas[target_x]
        if isinstance(agent, Direction) and isinstance(target, Noun):
            if target.query == Query.IDENTITY:
                xx = memory.graph.look_toward_direction(agent.of_x, agent.which)
                rr = []
                for x in xx:
                    idea = memory.ideas[x]
                    if idea.name:
                        r = ' '.join(idea.name)
                    elif idea.kind:
                        r = idea.kind
                    else:
                        return None
                    rr.append(r)

                if not rr:
                    return Response('nothing')

                r = ','.join(rr)
                return Response(r)
            else:
                return None
        elif isinstance(agent, Noun) and isinstance(target, Direction):
            of = memory.ideas[target.of_x]
            if of.query == Query.IDENTITY:
                xx = memory.graph.look_from_direction(agent_x, target.which)
                rr = []
                for x in xx:
                    idea = memory.ideas[x]
                    if idea.name:
                        r = ' '.join(idea.name)
                    elif idea.kind:
                        r = idea.kind
                    else:
                        return None
                    rr.append(r)

                if not rr:
                    return Response('nothing')

                r = ','.join(rr)
                return Response(r)
            else:
                return None
        else:
            return None


class AgentPlaceQuestion(ClauseMeaning):
    def __init__(self):
        self.purpose = Purpose.WH_Q
        self.lemmas = ['be']
        self.signatures = [
            [Relation.AGENT, Relation.PLACE],
        ]

    def handle(self, c, memory, (agent_xx, loc_xx)):
        if len(agent_xx) != 1:
            return None

        if len(loc_xx) != 1:
            return None

        agent = memory.ideas[agent_xx[0]]
        place = memory.ideas[loc_xx[0]]

        if agent.query == Query.IDENTITY:
            return None
        elif place.query == Query.IDENTITY:
            x = agent.location_history.current_location()
            if x is None:
                return Response('dunno')
            loc = memory.ideas[x]
            return Response(loc.kind)
        else:
            assert False


class AgentPlaceBeforeQuestion(ClauseMeaning):
    def __init__(self):
        self.purpose = Purpose.WH_Q
        self.lemmas = ['be']
        self.signatures = [
            [Relation.AGENT, Relation.PLACE, Relation.BEFORE],
        ]

    def handle(self, c, memory, (what_xx, where_xx, before_xx)):
        if len(what_xx) != 1:
            return None

        if len(where_xx) != 1:
            return None

        if len(before_xx) != 1:
            return None

        what = memory.ideas[what_xx[0]]
        where = memory.ideas[where_xx[0]]
        before_x, = before_xx

        if what.query == Query.IDENTITY:
            return None
        elif where.query == Query.IDENTITY:
            x = what.location_history.location_before(before_x)
            if x is None:
                return Response('dunno')
            idea = memory.ideas[x]
            return Response(idea.kind)
        else:
            assert False


class AgentIn(ClauseMeaning):
    def __init__(self):
        self.purpose = Purpose.INFO
        self.lemmas = ['be']
        self.signatures = [
            [Relation.AGENT, Relation.IN],
        ]

    def handle(self, c, memory, (agent_xx, place_xx)):
        if len(agent_xx) != 1:
            return None

        if len(place_xx) != 1:
            return None

        agent = memory.ideas[agent_xx[0]]
        place_x, = place_xx
        if c.adverbs == ['no', 'longer']:
            loc = NotAt(place_x)
            agent.location_history.update_location(loc)
            return Response()

        if c.verb.polarity.tf:
            loc = At(place_x)
        else:
            loc = NotAt(place_x)
        agent.location_history.update_location(loc)
        return Response()


class AgentInQuestion(ClauseMeaning):
    def __init__(self):
        self.purpose = Purpose.TF_Q
        self.lemmas = ['be']
        self.signatures = [
            [Relation.AGENT, Relation.IN],
        ]

    def handle(self, c, memory, (agent_xx, place_xx)):
        if len(agent_xx) != 1:
            return None

        if len(place_xx) != 1:
            return None

        agent = memory.ideas[agent_xx[0]]
        place_x, = place_xx
        r = agent.location_history.is_at_location(place_x)
        if r is None:
            return Response('dunno')
        elif r:
            return Response('yes')
        else:
            return Response('no')
