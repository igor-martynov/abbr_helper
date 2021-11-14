#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from dataclasses import dataclass, field
from typing import List

from base_classes import *
from group import Group



@dataclass
class Abbr(object):
	"""docstring for Abbr"""
	name: str
	descr: str
	comment: str
	disabled: bool
	_id: int = -1 # this should be overwritten upon first save
	groups: List[Group] = field(default_factory = list)
	

	@property
	def is_disabled(self):
		"""abbr is disabled if either self.disabled, or all of it's groups are disabled"""
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
		return hash((self.name, self.descr))
	
	

class AbbrFactory(BaseFactory):
	"""factory for Abbr"""
	def __init__(self, logger = None, group_manager = None):
		super(AbbrFactory, self).__init__()
		self._logger = logger
		self.group_manager = group_manager
	
	
	def set_group_manager(self, group_manager):
		self.group_manager = group_manager
		self._logger.debug("set_group_manager: set")
	
	
	def create_from_db_row(self, row1, row2):
		"""create new Abbr object from DB row
		
		arguments: row1 - tuple of (id: int, name: str, descr: str, comment: str, disabled: int)
			row2: list like [(group_id1,), (group_id2,), ...]
		returns: new Abbr object
		"""
		self._logger.debug(f"create_from_db_row: will create new abbr from row1: {row1}, and row2: {row2}")
		new_obj = Abbr(_id = row1[0], name = row1[1], descr = row1[2], comment = row1[3], disabled = True if row1[4] == 1 else False)
		for group_id in row2:
			group_to_add = self.group_manager.get_group_by_id(group_id[0])
			new_obj.groups.append(group_to_add)
			self._logger.debug(f"create_from_db_row: added group {group_to_add} to abbr {new_obj}")
		self._logger.debug(f"create_from_db_row: created abbr: {new_obj}")
		return new_obj
	
	
	def create(self, _id = None, name = "", descr = "", groups = [], comment = "", disabled = False):
		new_abbr = Abbr(_id = _id if _id is not None else -1, name = name, descr = descr, groups = groups, comment = comment, disabled = disabled)
		return new_abbr



class AbbrDAO(BaseDAO):
	"""docstring for AbbrDAO"""
	def __init__(self, db = None, logger = None, factory = None):
		super(AbbrDAO, self).__init__(db = db, logger = logger, factory = factory)
		
		pass
	
	
	def create(self, obj):
		self._db.execute_db_query("""INSERT INTO abbrs(name, descr, comment, disabled) VALUES(:name, :descr, :comment, :disabled)""", {"name": obj.name, "descr": obj.descr, "comment": obj.comment, "disabled": 1 if obj.disabled else 0})
		row = self._db.execute_db_query("""SELECT id FROM abbrs WHERE name == :name AND descr == :descr AND comment == :comment""", {"name": obj.name, "descr": obj.descr, "comment": obj.comment})
		obj._id = row[0][0]
		self._logger.debug(f"create: set back _id of newly created abbr: {obj._id}")
		for group_id in obj.group_id_list:
			self._db.execute_db_query("""INSERT INTO abbr_group(abbr_id, group_id) VALUES(:abbr_id, :group_id)""", {"abbr_id": obj._id, "group_id": group_id})
		self.dict[obj._id] = obj
		self._logger.debug(f"create: created and saved abbr: {obj}")
	
	
	def read(self, _id):
		self._logger.debug(f"read: will read abbr with id {_id}")
		row1 = self._db.execute_db_query("""SELECT id, name, descr, comment, disabled FROM abbrs WHERE id == :id""", {"id": _id})
		row2 = self._db.execute_db_query("""SELECT group_id FROM abbr_group WHERE abbr_id == :abbr_id""", {"abbr_id": _id})
		new_abbr = self._factory(row1[0], row2)
		self.dict[new_abbr._id] = new_abbr
		return new_abbr
		
	
	def update(self, obj):
		self._logger.debug(f"update: will save abbr {obj}")
		self._db.execute_db_query("""UPDATE abbrs SET name = :name, descr = :descr, comment = :comment, disabled = :disabled WHERE id = :id""", {"id": obj._id,
			"name": obj.name,
			"descr": obj.descr,
			"comment": obj.comment,
			"disabled": 1 if obj.disabled is True else 0})
		# update groups
		self._db.execute_db_query("""DELETE FROM abbr_group WHERE abbr_id == :abbr_id""", {"abbr_id": obj._id})
		self._logger.debug(f"update: interconnects resetted for {obj}")
		for group_id in obj.group_id_list:
			self._logger.debug(f"update: will save interconnect between abbr {obj} group_id {group_id}")
			self._db.execute_db_query("""INSERT INTO abbr_group(abbr_id, group_id) VALUES(:abbr_id, :group_id)""", {"abbr_id": obj._id, "group_id": group_id})
		self._logger.info(f"update: saved abbr as: {obj}")
	
	
	def delete(self, obj):
		self._logger.debug(f"delete: will delete abbr {obj} and it's interconnects")
		self._db.execute_db_query("""DELETE FROM abbrs where id == :abbr_id""", {"abbr_id": obj._id})
		self._db.execute_db_query("""DELETE FROM abbr_group where abbr_id == :abbr_id""", {"abbr_id": obj._id})
		self._logger.info(f"delete: deleted abbr {obj}")
	
	
	def load_all(self):
		self._logger.debug("load_all: will load all")
		self.dict = {}
		row = self._db.execute_db_query("""SELECT id FROM abbrs""")
		if len(row) == 0:
			self._logger.info("load_all: DB seems to be empty?..")
			return
		id_list = row
		self._logger.debug(f"load_all: got initial list of IDs: {id_list}, row is: {row}")
		for i in id_list:
			self.dict[i[0]] = self.read(i[0])
		self._logger.debug(f"load_all: finally loaded these abbrs: {self.dict}")
	


class AbbrManager(BaseManager):
	"""NEW AbbrManager
	
	responsibility:
	load all abbrs
	get abbr by name
	CRUD abbr
	
	"""
	def __init__(self, db = None, logger = None, group_manager = None):
		super(AbbrManager, self).__init__(db = db, logger = logger)
		# self.dict = {}
		self._factory = None
		# self._DAO = None
		self.group_manager = group_manager
		
		self.init_all()
		pass
	
	
	def init_all(self):
		# abbr_factory
		self._factory = AbbrFactory(logger = self._logger.getChild("AbbrFactory"), group_manager = self.group_manager)
		# abbrDAO
		self._DAO = AbbrDAO(db = self._db, logger = self._logger.getChild("AbbrDAO"), factory = self._factory.create_from_db_row)
		self._logger.debug("init_all: complete")
	
	
	def set_group_manager(self, group_manager):
		self.group_manager = group_manager
		self._factory.set_group_manager(group_manager)
		self._logger.debug(f"set_group_manager: self.group_manager and self._factory.group_manager both set to {self.group_manager}")
	
	
	def _get_ids_by_name(self, _name):
		"""_get_ids_by_name
		
		arguments: _name - name of abbt as a str, i.e. "CPU"
		returns: list of IDs """
		id_list = []
		row = self._db.execute_db_query("""SELECT id FROM abbrs WHERE name == :name""", {"name": _name})
		self._logger.debug(f"_get_ids_by_name: got line from DB: {row}")
		if len(row) == 0:
			return id_list
		for l in row[0]:
			id_list.append(l)
		return id_list
	
	
	def get_abbrs_by_name(self, _name):
		"""
		arguments:
		returns: list of abbrs"""
		self._logger.debug(f"get_abbrs_by_name: will search for abbr {_name}")
		result = []
		id_list = self._get_ids_by_name(_name)
		for i in id_list:
			try:
				result.append(self.dict[i])
			except KeyError as e:
				self._logger.error(f"get_abbrs_by_name: could not find abbr with id {i}")
		self._logger.debug(f"get_abbrs_by_name: result is: {result}")
		return result
	
	
	def load_all(self):
		self._DAO.load_all()
		self.dict = self._DAO.dict
		self._logger.debug(f"load_all: complete, loaded {len(self.dict)} abbrs")
	
	
	def get_abbr_by_id(self, _id):
		"""
		arguments: _id: int
		returns: object of abbr"""
		try:
			result = self.dict[_id]
			return result
		except KeyError as e:
			self._logger.debug(f"get_abbr_by_id: abbr with id {_id} does not exist!")
			return None
	
	
	def already_exist(self, name, descr):
		candidates = self.get_abbrs_by_name(name)
		for c in candidates:
			if c.descr == descr:
				return True
		return False
	
	
	def create(self, name = None, groups = [], descr = None, comment = None, disabled = False):
		if name is None:
			self._logger.error("create: name is None, so can't create new abbr")
			return
		if type(name) != type(str()):
			self._logger.error("create: name is not str, so can't create new abbr")
			return
		name_orig = name
		name = normalize_abbr(name)
		if name != name_orig:
			self._logger.debug(f"create: abbr {name_orig} was normalized to {name}")
		if self.already_exist(name, descr):
			self._logger.debug(f"create: abbr {name} - {descr} already exist, will not create")
			return None
		new_abbr = self._factory.create(name = name,
			descr = descr,
			groups = groups,
			comment = comment,
			disabled = disabled)
		self._DAO.create(new_abbr)
		self._logger.debug(f"create: created abbr {new_abbr}")
		return new_abbr
	
	
	def delete(self, abbr):
		abbr_id = abbr._id
		self._DAO.delete(abbr)
		del(self.dict[abbr._id])
		self._logger.info(f"delete: abbr with id {abbr_id} deleted both from dict and DB")


	def save(self, abbr):
		self._DAO.update(abbr)


