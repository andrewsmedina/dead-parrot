#!/usr/bin/env python
# -*- coding: utf-8; -*-
#
# Copyright (C) 2009 Gabriel Falcão <gabriel@nacaolivre.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with this program; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

import simplejson

from deadparrot.serialization import Registry
from deadparrot.models.attributes import Attribute
from deadparrot.models.managers import *
from deadparrot.models.fields import *

# for model registration that is important to the "model registry"
# stay separated of base.py, to avoid circular dependency between
# deadparrot's modules
from deadparrot.models.registry import _REGISTRY
from deadparrot.models.registry import _MODULE_REGISTRY
from deadparrot.models.registry import _APP_REGISTRY
from deadparrot.models.registry import ModelRegistry

VALIDATE_NONE = "The model won't validate any fields"
VALIDATE_ALL = """
    The model will validate all fields, unless
    those which have the validate parameter set
    to False
"""

def build_metadata(klass, params):
    verbose_name = klass.__name__
    verbose_name_plural = "%ss" % verbose_name
    klass_meta =  type('Meta', tuple(), params)

    module_name = klass.__module__
    if "." in module_name:
        module_name = module_name.split(".")[-1]

    klass_meta.app_label = module_name

    if not params.has_key('verbose_name'):
        klass_meta.verbose_name = verbose_name

    if not params.has_key('verbose_name_plural'):
        klass_meta.verbose_name_plural = verbose_name_plural

    if not params.has_key('fields_validation_policy'):
        klass_meta.fields_validation_policy = VALIDATE_ALL

    metaobj = klass_meta()
    if hasattr(metaobj, '_fields'):
        for k, v in metaobj._fields.items():
            v.name = k

    return metaobj

class ModelMeta(type):
    def __init__(cls, name, bases, attrs):
        if name not in ('ModelMeta', 'Model'):
            # handling fields
            fields =  dict([(k, v) for k, v in attrs.items() \
                            if isinstance(v, Field)])
            relationships =  dict([(k, v) for k, v in attrs.items() \
                                   if isinstance(v, RelationShip)])
            
            metadata_params = hasattr(cls, 'Meta') and \
                              vars(cls.Meta) or {}
            
            metadata_params['_fields'] = fields
            metadata_params['_relationships'] = relationships            

            cls._meta = build_metadata(cls, metadata_params)
            cls._data = {}
            cls._meta.has_pk = False
            
            for k, v in fields.items():
                cls._data[k] = v
                
                if v.primary_key:
                    cls._meta.has_pk = True
                    
                setattr(cls, k, None)

            for k, v in relationships.items():
                if not v.model._meta.has_pk:
                    raise InvalidRelationShipError, \
                          "A model need to have at least " \
                          "one primary_key for creating a relationship"

                cls._data[k] = v
                v.set_from_model(cls)
                setattr(cls, k, None)

            # registering the class in my dicts
            if not _APP_REGISTRY.get(cls._meta.app_label):
                _APP_REGISTRY[cls._meta.app_label] = {}
            _APP_REGISTRY[cls._meta.app_label][cls.__name__] = cls
            if not _MODULE_REGISTRY.get(cls.__module__):
                _MODULE_REGISTRY[cls.__module__] = {}
            _MODULE_REGISTRY[cls.__module__][cls.__name__] = cls

            if not _REGISTRY.get(cls.__module__):
                _REGISTRY[cls.__module__] = {}

            if not _REGISTRY[cls.__module__].get(cls._meta.app_label):
                _REGISTRY[cls.__module__][cls._meta.app_label] = {}

            gdict = _REGISTRY[cls.__module__][cls._meta.app_label]
            gdict[cls.__name__] = cls

            # handling managers
            manager_classes = dict([(k, v) for k, v in attrs.items() \
                                    if isinstance(v, tuple) and \
                                    len(v) == 3 and \
                                    issubclass(v[0], ModelManagerBuilder)])
            for k, manager_tup in manager_classes.items():
                manager_klass, args, kw = manager_tup
                setattr(cls, k, manager_klass(model=cls, *args, **kw))
                
        super(ModelMeta, cls).__init__(name, bases, attrs)

class ModelSet(object):
    __model_class__ = None
    def __init__(self, *items):
        for i in items:
            if not isinstance(i, self.__model_class__):
                raise TypeError, \
                      "%s can only handle %s types, got %r" % \
                      (self.__class__.__name__,
                       self.__model_class__.__name__,
                       type(i))
        self.items = items

    def __getitem__(self, *a, **kw):
        return self.items.__getitem__(*a, **kw)
    def __setitem__(self, *a, **kw):
        return self.items.__setitem__(*a, **kw)
    def __getslice__(self, *a, **kw):
        return self.items.__getslice__(*a, **kw)
    def __setslice__(self, *a, **kw):
        return self.items.__setslice__(*a, **kw)
    def __nonzero__(self):
        return bool(self.items)
    def __len__(self):
        return len(self.items)

    def __repr__(self):
        return "%s.Set(%r)" % (self.__model_class__.__name__, list(self))

    def to_dict(self):
        dicts = [m.to_dict() for m in self.items]
        ret = {self.__model_class__._meta.verbose_name_plural.title(): dicts}
        return ret

    @classmethod
    def from_dict(cls, edict):
        if not isinstance(edict, dict):
            raise TypeError, "%s.from_dict takes a dict as parameter. " \
                  "Got %r" % (cls.__name__, type(edict))

        items = edict[cls.__model_class__._meta.verbose_name_plural]
        return cls(*[cls.__model_class__.from_dict(i) for i in items])

    def serialize(self, to):
        serializer = Registry.get(to)
        return serializer(self.to_dict()).serialize()

    @classmethod
    def deserialize(cls, data, format):
        serializer = Registry.get(format)
        my_dict = serializer.deserialize(data)
        return cls.from_dict(my_dict)

class Model(object):
    __metaclass__ = ModelMeta
    __dead_parrot__ = __module__
    
    def __init__(self, **kw):
        for k, v in kw.items():
            if k not in self._meta._fields.keys() and \
               k not in self._meta._relationships.keys():
                raise AttributeError, \
            "%s has no attribute %s" % (self.__class__.__name__, k)
            setattr(self, k, v)

    def __repr__(self):
        if hasattr(self, '__unicode__'):
            return self.__unicode__()
        pks = ", ".join(["%s=%s" % (k, getattr(self, k)) for k, f in self._meta._fields.items() if f.primary_key])
        return "<%s%s object>" % (self.__class__.__name__, pks and "(%s)" % pks or "")

    def _get_data(self):
        fields = []

        for k in self._data.keys():
            value = getattr(self, k)            
            field = None
            for x in '_fields', '_relationships':
                if field is None:
                    fdict = getattr(self._meta, x)
                    field = fdict.get(k, None)
            tup = (k, field.serialize(value))
            fields.append(tup)
        return dict(fields)

    def to_dict(self):
        return {self._meta.verbose_name: self._get_data()}

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            raise TypeError, "%s can be compared only with %s or its subclasses instances." \
                  " Got %r" % (self.__class__.__name__, self.__class__.__name__, other)

        # ok, "other" is the same type than self, gonna iterate through its attributes and compare them                
        if not self._meta.has_pk:
            mine = [getattr(self, field_name) for field_name in self._meta._fields.keys()]
            from_other = [getattr(other, field_name) for field_name in self._meta._fields.keys()]
        # unless "self" has at least one primary_key, only pk values will be used
        else:
            mine = [getattr(self, field_name) for field_name, field in self._meta._fields.items() if field.primary_key]
            from_other = [getattr(other, field_name) for field_name, field in self._meta._fields.items() if field.primary_key]
        
        return mine == from_other
    
    @property
    def _is_valid(self):
        """Check if all non-blank fields are filled"""
        non_blank_fields = [k for k, v in self._meta._fields.items() if not v.blank]
        return None not in [getattr(self, k) for k in non_blank_fields]

    def __setattr__(self, attr, val):
        if attr in self._data.keys():
            klassname = self.__class__.__name__
            if attr in self._meta._fields.keys():
                field = self._meta._fields[attr]
            elif attr in self._meta._relationships.keys():
                field = self._meta._relationships[attr]
                setattr(val, '_from_model', field.from_model)
                setattr(val, '_to_model', field.to_model)                
            if isinstance(field, Field):
                if self._meta.fields_validation_policy != VALIDATE_NONE:
                    # raising the field-specific exceptions
                    field.validate(val)
                val = field.convert_type(val)
                
            self._data[attr] = val
            
        super(Model, self).__setattr__(attr, val)

    @classmethod
    def from_dict(cls, data_dict):
        if not isinstance(data_dict, dict):
            raise TypeError, "%s.from_dict takes a dict as parameter. " \
                  "Got %r:%r" % (cls.__name__,
                                 type(data_dict),
                                 data_dict)
        try:
            d = data_dict[cls._meta.verbose_name].copy()
        except KeyError, e:
            raise TypeError, "%s.from_dict got an mismatched dict structure." \
                  "Expected {'%s': {... data ...}} like structure, got %s" % (cls,
                                                                              cls._meta.verbose_name,
                                                                              unicode(data_dict))
        keys = cls._meta._fields.keys()
        obj = cls()
        for k, v in d.items():
            if k in keys:
                setattr(obj, k, v)

        return obj

    @classmethod
    def Set(cls):
        klass = type('%sSet' % cls.__name__, (ModelSet, ), {'__model_class__': cls })
        return klass

    def serialize(self, to):
        serializer = Registry.get(to)
        return serializer(self.to_dict()).serialize()

    @classmethod
    def deserialize(cls, data, format):
        serializer = Registry.get(format)
        my_dict = serializer.deserialize(data)
        return cls.from_dict(my_dict)