#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from dataclasses import dataclass, field
from typing import List

from base_classes import *



@dataclass
class Group(object):
	"""docstring for Group"""
	name: str
	comment: str
	disabled: bool
	_id: int = -1 #

	

# new
class GroupFactory(BaseFactory):
	"""docstring for GroupFactory"""
	def __init__(self, logger = None):
		super(GroupFactory, self).__init__()
		self._logger = logger
	
	
	def create_from_db_row(self, row):
		"""create new group from db row
		row is: (id, name, comment, disabled)"""
		self._logger.debug(f"create_from_db_row: will create group from row: {row}")
		new_obj = Group(name = row[1], comment = row[2], disabled = True if row[3] == 1 else False, _id = row[0])
		return new_obj
	
	
	def create(self, _id = None, name = "", comment = "", disabled = False):
		new_obj = Group(_id =_id, name = name, comment = comment, disabled = disabled)
		return new_obj

	
	
# new
class GroupDAO(BaseDAO):
	"""docstring for GroupDAO"""
	def __init__(self, db = None, logger = None, factory = None):
		super(GroupDAO, self).__init__(db = db, logger = logger, factory = factory)
		
		pass
	
	
	def create(self, obj):
		self._db.execute_db_query("""INSERT INTO groups(name, comment, disabled) VALUES(:name, :comment, :disabled)""", {"name":obj.name, "comment": obj.comment, "disabled": 1 if obj.disabled else 0})
		row = self._db.execute_db_query("""SELECT id FROM groups WHERE name == :name""", {"name": obj.name})
		self._logger.debug(f"create: created record for object {obj}, will set id to {row[0]}")
		obj._id = row[0][0]
		self.dict[obj._id] = obj
		self._logger.debug(f"create: created and saved group: {obj}")
	
	
	def read(self, _id):
		row = self._db.execute_db_query("""SELECT id, name, comment, disabled FROM groups WHERE id == :_id""", {"_id": _id})
		new_obj = self._factory(row[0])
		self.dict[_id] = new_obj
		return new_obj
	
	
	def update(self, obj):
		"""will update group, but not it's interconnects"""
		self._logger.debug(f"""update: will save group {obj}""")
		self._db.execute_db_query("""UPDATE groups SET name = :name,
			comment = :comment,
			disabled = :disabled WHERE id == :_id""", {"_id": obj._id, "name": obj.name, "comment": obj.comment, "disabled": 1 if obj.disabled else 0})
		self._logger.debug(f"update: saved group {obj}")
	
	
	def delete(self, obj):
		"""will delete both group AND all its interconnects"""
		self._logger.debug(f"delete: will delete group {obj} and it's interconnects")
		# group
		self._db.execute_db_query("""DELETE FROM groups WHERE id == :_id""", {"_id": obj._id})
		# abbr - group - those intercoencts shoud be already deleted on upper level
		self._db.execute_db_query("""DELETE FROM abbr_group WHERE group_id == :group_id""", {"group_id": obj._id})
		self._logger.debug(f"delete: deleted group {obj}")
		
	
	
	def load_all(self):
		self.dict = {}
		id_list = self._db.execute_db_query("""SELECT id FROM groups""")
		if len(id_list) == 0:
			self._logger.debug("load_all: DB seems to be empty?..")
			return
		self._logger.debug(f"load_all: got initial list of IDs: {id_list}")
		for i in id_list:
			self._logger.debug(f"load_all: will load id {i}")
			self.dict[i[0]] = self.read(i[0])
		self._logger.debug(f"load_all: finally loaded these abbrs: {self.dict}")



# new
class GroupManager(BaseManager):
	"""docstring for GroupManager"""
	def __init__(self, db = None, logger = None):
		super(GroupManager, self).__init__(db = db, logger = logger)
		self._group_factory = None
		self._groupDAO = None
		self.abbr_manager = None
		self.init_all()
		pass
	
	
	def init_all(self):
		# group_factory
		self._factory = GroupFactory(logger = self._logger.getChild("GroupFactory"))
		# groupDAO
		self._DAO = GroupDAO(db = self._db, logger = self._logger.getChild("GroupDAO"), factory = self._factory.create_from_db_row)
		self._logger.debug("init_all: complete")
		
	
	def load_all(self):
		self._logger.debug("load_all: will load all")
		self._DAO.load_all()
		self.dict = self._DAO.dict
		self._logger.debug(f"load_all: complete, loaded {len(self.dict)} groups")
	
	
	def set_abbr_manager(self, abbr_manager):
		self.abbr_manager = abbr_manager
	
	
	def get_group_by_id(self, _id):
		try:
			return self.dict[_id]
		except KeyError as e:
			self._logger.error(f"get_group_by_id: group with id {_id} does not exist")
			return None
	
	
	def get_name_by_id(self, _id):
		result = self.get_group_by_id(_id)
		if result is None:
			return None
		return result.name
		
	
	def get_id_by_name(self, name):
		result = None
		for k, v in self.dict.items():
			if v.name == name:
				return k
	
	
	def get_id_list_by_name_list(self, name_list):
		result = []
		for n in name_list:
			result.append(self.get_id_by_name(n))
		return result
	
	
	def already_exist(self, name):
		for k, v in self.dict.items():
			if v.name == name:
				self._logger.debug(f"already_exist: group with name {name} already exist")
				return True
		return False
	
	
	def create(self, name = None, comment = None, disabled = False):
		if name is None:
			self._logger.error("create: name is None, so can't create new group")
			return
		if self.already_exist(name):
			self._logger.debug(f"create: group {name} already exist, will not create")
			return None
		new_obj = self._factory.create(name = name, comment = comment, disabled = disabled)
		self._DAO.create(new_obj)
		return new_obj
	
	
	def delete(self, obj):
		self._logger.debug(f"delete: will delete group {obj}")
		obj_id = obj._id
		self._DAO.delete(obj)
		for a in self.abbr_manager.dict.values():
			if obj in a.groups:
				a.groups.remove(obj)
				self._logger.debug(f"delete: deleted group {obj} from abbr {a}")
				self.abbr_manager.save(a)
		del(self.dict[obj._id])
		self._logger.info(f"delete: obj with id {obj_id} deleted both from dict and DB")
		pass
	
	
	def save(self, obj):
		self._DAO.update(obj)


