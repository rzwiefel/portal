from uuid import uuid4

from transit.transit_types import Keyword as kw

import variables as v


class ObjectValueHandler(object):
    @staticmethod
    def tag(obj):
        return "portal.transit/object"

    @staticmethod
    def rep(obj):
        id = uuid4()
        v.instance_cache[id] = obj
        return {kw("id"):     id,
                kw("type"):   str(type(obj)),
                kw("string"): str(obj)}

    @staticmethod
    def string_rep(_):
        return None
