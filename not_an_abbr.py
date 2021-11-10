#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from dataclasses import dataclass, field
from typing import List

from base_classes import *
from group import Group

@dataclass
class NotAnAbbr(object):
	"""docstring for NotAnAbbr"""
	name: str
	comment: str
	disabled: bool
	_id: int = -1 # this should be overwritten upon first save
	groups: List[Group] = field(default_factory = list)	
	

# new
class NotAnAbbrManager(BaseManager):
	"""docstring for NotAnAbbrManager"""
	def __init__(self, db = None, logger = None):
		super(NotAnAbbrManager, self).__init__(db = db, logger = logger)
		pass