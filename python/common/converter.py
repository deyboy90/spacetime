﻿'''
Created on Apr 19, 2016

@author: Rohan Achar
'''

from common.recursive_dictionary import RecursiveDictionary

import uuid

class _container(object):
    pass

def get_type(obj):
    # both iteratable/dictionary + object type is messed up. Won't work.
    try:
        if hasattr(obj, "__dependent_type__"):
            return "dependent"
        if dict in type(obj).mro():
            return "dictionary"
        if hasattr(obj, "__iter__"):
            #print obj
            return "collection"
        if len(set([float, int, str, unicode, type(None)]).intersection(set(type(obj).mro()))) > 0:
            return "primitive"
        if hasattr(obj, "__dict__"):
            return "object"
    except TypeError, e:
        return "unknown"
    return "unknown"

def create_jsondict(obj):
    obj_dict = RecursiveDictionary()
    if hasattr(obj.__class__, "__dimensions__"):
        for dimension in obj.__class__.__dimensions__:
            if dimension._primarykey:
                try:
                    getattr(obj, dimension._name)
                except AttributeError:
                    setattr(obj, dimension._name, str(uuid.uuid4()))
            obj_dict[dimension._name] = create_jsondict(getattr(obj, dimension._name))
        return obj_dict
    else:
        tp_marker = get_type(obj)
        if tp_marker == "primitive":
            return obj
        elif tp_marker == "dictionary":
            return RecursiveDictionary([(create_jsondict(k), create_jsondict(v)) for k, v in obj])
        elif tp_marker == "collection":
            return obj.__class__([create_jsondict(item) for item in obj])
        elif tp_marker == "object":
            return RecursiveDictionary(obj.__dict__)

def create_tracking_obj(tp, objjson, universemap, start_track_ref, extra = True):
    obj = create_complex_obj(tp, objjson, universemap, extra)
    if obj:
        obj.__start_tracking__ = start_track_ref
    return obj

def create_complex_obj(tp, objjson, universemap, extra = True):
    obj = _container()
    obj.__class__ = tp.Class()
    obj.__start_tracking__ = False
    if not objjson:
        return objjson
    all_attribs = set(objjson.keys())
    for dimension in tp.__dimensions__:
        if dimension._name in objjson:
            all_attribs.remove(dimension._name)
            if hasattr(dimension._type, "__dependent_type__"):
                primarykey = objjson[tp.__primarykey__._name]

                if dimension._type in universemap and primarykey in universemap[dimension._type]:
                    setattr(obj, dimension._name, universemap[dimension._type][primarykey])
                else:
                    setattr(obj, dimension._name, create_tracking_obj(dimension._type, objjson[dimension._name], universemap, True))
            else:
                setattr(obj, dimension._name, create_obj(dimension._type, objjson[dimension._name]))
    if extra:
        for extra_attrib in all_attribs:
            setattr(obj, extra_attrib, objjson[extra_attrib])
    return obj

def create_obj(tp, objjson):
    category = get_type(objjson)
    if category == "primitive":
        return objjson
    elif category == "collection":
        return objjson

    obj = _container()
    obj.__dict__ = objjson
    obj.__class__ = tp
    return obj
