#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from dataclasses import dataclass, field
from typing import List

from base_classes import *


@dataclass
class Abbr(object):
	"""docstring for Abbr"""
	name: str
	descr: str
	comment: str
	disabled: bool
	_id: int = -1 # this should be overwritten upon first save
	group_list: List[int] = field(default_factory = list)
	
	
	


	

class AbbrFactory(BaseFactory):
	"""docstring for AbbrFactory"""
	def __init__(self, logger = None):
		super(AbbrFactory, self).__init__()
		self._logger = logger
		pass
	
	
	def create_from_db_row(self, row1, row2):
		self._logger.debug(f"create_from_db_row: will create new abbr from row1: {row1}, and row2: {row2}")
		new_obj = Abbr(_id = row1[0], name = row1[1], descr = row1[2], comment = row1[3], disabled = True if row1[4] == 1 else False)
		for group_id in row2:
			new_obj.group_list.append(group_id)
		self._logger.debug(f"create_from_db_row: created abbr: {new_obj}")
		return new_obj
	
	
	def create(self, _id = None, name = "", descr = "", group_list = [], comment = "", disabled = False):
		new_abbr = Abbr(_id = _id if _id is not None else -1, name = name, descr = descr, group_list = group_list, comment = comment, disabled = disabled)
		return new_abbr



# new
class AbbrDAO(BaseDAO):
	"""docstring for AbbrDAO"""
	def __init__(self, db = None, logger = None, factory = None):
		super(AbbrDAO, self).__init__(db = db, logger = logger, factory = factory)
		
		# self._db_manager = db_manager
		# self._logger = logger
		
		pass
	
	
	def create(self, obj):
		self._db.execute_db_query("""INSERT INTO abbrs(name, descr, comment, disabled) VALUES(:name, :descr, :comment, :disabled)""", {"name": obj.name, "descr": obj.descr, "comment": obj.comment, "disabled": 1 if obj.disabled else 0})
		row = self._db.execute_db_query("""SELECT id FROM abbrs WHERE name == :name AND descr == :descr AND comment == :comment""", {"name": obj.name, "descr": obj.descr, "comment": obj.comment})
		obj._id = row[0][0]
		self._logger.debug(f"create: set back _id of newly created abbr: {obj._id}")
		for group_id in obj.group_list:
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
		for group_id in obj.group_list:
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
	def __init__(self, db = None, logger = None):
		super(AbbrManager, self).__init__(db = db, logger = logger)
		
		# self.abbr_list = []
		# self.abbr_dict = {}
		self.dict = {}
		# self._db_manager = db_manager
		# self._logger = logger
		self._factory = None
		self._DAO = None
		
		self.init_all()
		pass
	
	
	def init_all(self):
		# abbr_factory
		self._factory = AbbrFactory(logger = self._logger.getChild("AbbrFactory"))
		# abbrDAO
		self._DAO = AbbrDAO(db = self._db, logger = self._logger.getChild("AbbrDAO"), factory = self._factory.create_from_db_row)
		self._logger.debug("init_all: complete")
	
	
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
	
	
	def already_exist(self, name, desc):
		candidates = self.get_abbrs_by_name(name)
		for c in candidates:
			if c.descr == descr:
				return True
		return False
	
	
	def create_abbr(self, name = None, group_list = [], descr = None, comment = None, disabled = False):
		if name is None:
			self._logger.error("create_abbr: name is None, so can't create new abbr")
			return
		if self.already_exist(name, descr):
			self._logger.debug(f"create_abbr: abbr {name} - {descr} already exist, will not create")
			return None
		new_abbr = self._factory.create(name = name,
			descr = descr,
			group_list = group_list,
			comment = comment,
			disabled = disabled)
		self._DAO.create(new_abbr)
		self._logger.debug(f"create_abbr: created abbr {new_abbr}")
		return new_abbr
	
	
	def delete_abbr(self, abbr):
		abbr_id = abbr._id
		self._DAO.delete(abbr)
		del(self.dict[abbr._id])
		# del(abbr)
		self._logger.info(f"delete_abbr: abbr with id {abbr_id} deleted both from dict and DB")


	def save(self, abbr):
		self._DAO.update(abbr)


