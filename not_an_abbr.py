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

	
	@property
	def is_disabled(self):
		"""not_an_abbr is disabled if either self.disabled, or all of it's groups are disabled"""
		if self.disabled: 
			return True
		else:
			if len(self.groups) == 0:
				return False
			for g in self.groups:
				if not g.disabled:
					return False
			return True
	
	
	@property
	def group_id_list(self):
		result = []
		for g in self.groups:
			result.append(g._id)
		return result
	
	
	def __hash__(self):
		return hash((self.name))
	
	

class NotAnAbbrDAO(BaseDAO):
	"""docstring for NotAnAbbrDAO"""
	def __init__(self, db = None, logger = None, factory = None):
		super(NotAnAbbrDAO, self).__init__(db = db, logger = logger, factory = factory)
		pass
	
	
	def create(self, obj):
		self._db.execute_db_query("""INSERT INTO not_an_abbrs(name, comment, disabled) VALUES(:name, :comment, :disabled)""", {"name": obj.name, "comment": obj.comment, "disabled": 1 if obj.disabled else 0})
		row = self._db.execute_db_query("""SELECT id FROM not_an_abbrs WHERE name == :name""", {"name": obj.name})
		obj._id = row[0][0]
		self._logger.debug(f"create: set back _id of newly created not_an_abbr: {obj._id}")
		self.dict[obj._id] = obj
		self._logger.debug(f"create: created and saved not_an_abbr: {obj}")
	
	
	def read(self, _id):
		self._logger.debug(f"read: will read not_an_abbr with id {_id}")
		row1 = self._db.execute_db_query("""SELECT id, name, comment, disabled FROM not_an_abbrs WHERE id == :id""", {"id": _id})
		row2 = self._db.execute_db_query("""SELECT group_id FROM not_an_abbr_group WHERE not_an_abbr_id == :not_an_abbr_id""", {"not_an_abbr_id": _id})
		new_not_an_abbr = self._factory(row1[0], row2)
		self.dict[new_not_an_abbr._id] = new_not_an_abbr
		return new_not_an_abbr
	
	
	def update(self, obj):
		self._logger.debug(f"update: will save not_an_abbr {obj}")
		self._db.execute_db_query("""UPDATE not_an_abbrs SET name = :name, comment = :comment, disabled = :disabled WHERE id = :id""", {"id": obj._id,
			"name": obj.name,
			"comment": obj.comment,
			"disabled": 1 if obj.disabled is True else 0})
		# update groups
		self._db.execute_db_query("""DELETE FROM not_an_abbr_group WHERE not_an_abbr_id == :not_an_abbr_id""", {"not_an_abbr_id": obj._id})
		self._logger.debug(f"update: interconnects resetted for {obj}")
		for group_id in obj.group_id_list:
			self._logger.debug(f"update: will save interconnect between not_an_abbr {obj} group_id {group_id}")
			self._db.execute_db_query("""INSERT INTO not_an_abbr_group(not_an_abbr_id, group_id) VALUES(:not_an_abbr_id, :group_id)""", {"not_an_abbr_id": obj._id, "group_id": group_id})
		self._logger.info(f"update: saved not_an_abbr as: {obj}")
	
	
	def delete(self, obj):
		self._logger.debug(f"delete: will delete not_an_abbr {obj} and it's interconnects")
		self._db.execute_db_query("""DELETE FROM not_an_abbrs where id == :not_an_abbr_id""", {"not_an_abbr_id": obj._id})
		self._db.execute_db_query("""DELETE FROM not_an_abbr_group where not_an_abbr_id == :not_an_abbr_id""", {"not_an_abbr_id": obj._id})
		self._logger.info(f"delete: deleted not_an_abbr {obj}")
	
	
	def load_all(self):
		self._logger.debug("load_all: will load all")
		self.dict = {}
		row = self._db.execute_db_query("""SELECT id FROM not_an_abbrs""")
		if len(row) == 0:
			self._logger.info("load_all: DB seems to be empty?..")
			return
		id_list = row
		self._logger.debug(f"load_all: got initial list of IDs: {id_list}, row is: {row}")
		for i in id_list:
			self.dict[i[0]] = self.read(i[0])
		self._logger.debug(f"load_all: finally loaded these not_an_abbrs: {self.dict}")
	
	

class NotAnAbbrFactory(BaseFactory):
	"""docstring for NotAnAbbrFactory"""
	def __init__(self, logger = None, group_manager = None):
		super(NotAnAbbrFactory, self).__init__()
		self._logger = logger
		self.group_manager = group_manager
	
	
	def set_group_manager(self, group_manager):
		self.group_manager = group_manager
		self._logger.debug(f"set_group_manager: set to {self.group_manager}")
	
	
	def create_from_db_row(self, row1, row2):
		self._logger.debug(f"create_from_db_row: will create new not_an_abbr from row1: {row1}, and row2: {row2}")
		new_obj = NotAnAbbr(_id = row1[0], name = row1[1], comment = row1[2], disabled = True if row1[3] == 1 else False)
		for group_id in row2:
			group_to_add = self.group_manager.get_group_by_id(group_id[0])
			new_obj.groups.append(group_to_add)
			self._logger.debug(f"create_from_db_row: added group {group_to_add} to not_an_abbr {new_obj}")
		self._logger.debug(f"create_from_db_row: created not_an_abbr: {new_obj}")
		return new_obj
	
	
	def create(self, _id = None, name = "", groups = [], comment = "", disabled = False):
		new_abbr = NotAnAbbr(_id = _id if _id is not None else -1, name = name, groups = groups, comment = comment, disabled = disabled)
		return new_abbr
	


class NotAnAbbrManager(BaseManager):
	"""docstring for NotAnAbbrManager"""
	def __init__(self, db = None, logger = None, group_manager = None):
		super(NotAnAbbrManager, self).__init__(db = db, logger = logger)
		self.group_manager = group_manager
		self.init_all()
	
	
	def init_all(self):
		self._factory = NotAnAbbrFactory(logger = self._logger.getChild("NotAnAbbrFactory"), group_manager = self.group_manager)
		self._DAO = NotAnAbbrDAO(db = self._db, logger = self._logger.getChild("NotAnAbbrDAO"), factory = self._factory.create_from_db_row)
		self._logger.debug("init_all: complete")
	
	
	def set_group_manager(self, group_manager):
		self.group_manager = group_manager
		self._factory.set_group_manager(group_manager)
		self._logger.debug(f"set_group_manager: self.group_manager and self._factory.group_manager both set to {self.group_manager}")
	
	
	@property
	def all_names(self):
		result = []
		for naa in self.dict.values():
			if not naa.is_disabled:
				result.append(naa.name)
		return result
	
	
	def load_all(self):
		self._DAO.load_all()
		self.dict = self._DAO.dict
		self._logger.debug(f"load_all: complete, loaded {len(self.dict)} not_an_abbrs")
		
	
	def save(self, obj):
		self._DAO.update(obj)
	
	
	def create(self, name = None, groups = [], comment = None, disabled = False):
		if name is None:
			self._logger.error("create: name is None, so can't create new not_an_abbr")
			return
		if type(name) != type(str()):
			self._logger.error("create: name is not str, so can't create new not_an_abbr")
			return
		name_orig = name
		name = normalize_abbr(name)
		if name != name_orig:
			self._logger.debug(f"create: not_an_abbr {name_orig} was normalized to {name}")
		if self.already_exist(name):
			self._logger.debug(f"create: not_an_abbr {name} already exist, will not create")
			return None
		new_not_an_abbr = self._factory.create(name = name,
			groups = groups,
			comment = comment,
			disabled = disabled)
		self._DAO.create(new_not_an_abbr)
		self._logger.debug(f"create: created not_an_abbr {new_not_an_abbr}")
		return new_not_an_abbr
	
	
	def delete(self, not_an_abbr):
		not_an_abbr_id = not_an_abbr._id
		self._DAO.delete(not_an_abbr)
		del(self.dict[not_an_abbr._id])
		self._logger.info(f"delete: not_an_abbr with id {not_an_abbr_id} deleted both from dict and DB")
	
	
	def _get_id_by_name(self, _name):
		_id = None
		row = self._db.execute_db_query("""SELECT id FROM not_an_abbrs WHERE name == :name""", {"name": _name})
		self._logger.debug(f"_get_id_by_name: got line from DB: {row}")
		if len(row) == 0:
			return _id
		_id = row[0][0]
		return _id
	
	
	def get_not_an_abbr_by_name(self, name):
		_id = self._get_id_by_name(name)
		if _id is not None:
			return self.dict[_id]
		else:
			return None
	
	
	def get_not_an_abbr_by_id(self, _id):
		"""
		arguments: _id: int
		returns: object of abbr"""
		try:
			result = self.dict[_id]
			return result
		except KeyError as e:
			self._logger.debug(f"get_not_an_abbr_by_id: not_an_abbr with id {_id} does not exist!")
			return None
	
	
	def already_exist(self, name):
		if self.get_not_an_abbr_by_name(name) is None:
			return False
		else:
			return True


