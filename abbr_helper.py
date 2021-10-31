#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 2021-10-31

__version__ = "0.8.5"
__author__ = "Igor Martynov (phx.planewalker@gmail.com)"


"""
This app finds abbreviations and describes them from inner DB.


"""

# basic imports
import os
import datetime
import sys
import glob
import traceback

from dataclasses import dataclass, field
from typing import List

# docx format support
import docx

# flask web interface
from flask import Flask, flash, request, redirect, url_for, Response, render_template
from werkzeug.utils import secure_filename

# logging
import logging
import logging.handlers

# base classes
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


	
@dataclass
class Group(object):
	"""docstring for Group"""
	def __init__(self):
		super(Group, self).__init__()
		name: str
		comment: str
		disabled: bool
		_id: int = -1 #
		


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
			Abbr.group_list.append(group_id)
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
		obj._id = row[0]
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
		self._db.execute_db_query("""UPDATE abbrs SET name = :name, descr = :descr, comment = :comment, disabled = :disabled WHERE id = :id""", {"id": abbr._id,
			"name": obj.name,
			"descr": obj.descr,
			"comment": obj.comment,
			"disabled": 1 if obj.disabled is True else 0})
		# update groups
		self._db.execute_db_query("""DELETE FROM abbr_group WHERE abbr_id == :abbr_id""", {"abbr_id": obj._id})
		for group_id in obj.group_list:
			self._db.execute_db_query("""INSERT INTO abbr_group(abbr_id, group_id) VALUES(:abbr_id, :group_id)""", {"abbr_id": abbr._id, "group_id": group_id})
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
		self._abbr_factory = None
		self._abbrDAO = None
		
		self.init_all()
		pass
	
	
	def init_all(self):
		# abbr_factory
		self._abbr_factory = AbbrFactory(logger = self._logger.getChild("AbbrFactory"))
		# abbrDAO
		self._abbrDAO = AbbrDAO(db = self._db, logger = self._logger.getChild("AbbrDAO"), factory = self._abbr_factory.create_from_db_row)
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
		self._abbrDAO.load_all()
		self.dict = self._abbrDAO.dict
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
		new_abbr = self._abbr_factory.create(name = name, descr = descr, group_list = group_list, comment = comment, disabled = disabled)
		self._abbrDAO.create(new_abbr)
		self._logger.debug(f"create_abbr: created abbr {new_abbr}")
		return new_abbr
	
	
	def delete_abbr(self, abbr):
		abbr_id = abbr._id
		self._abbrDAO.delete(abbr)
		del(self.dict[abbr._id])
		# del(abbr)
		self._logger.info(f"delete_abbr: abbr with id {abbr_id} deleted both from dict and DB")
	
	

# new
class GroupFactory(BaseFactory):
	"""docstring for GroupFactory"""
	def __init__(self, logger = None):
		super(GroupFactory, self).__init__()
		self._logger = logger
	
	
	def create_from_db_row(self, row):
		"""create new group from db row
		row is: (id, name, comment, disabled)"""
		new_obj = Group(name = row[1], comment = row[2], disabled = True if row[3] == 1 else False, _id = roq[0])
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
		obj._id = row[0]
		self.dict[obj._id] = obj
		self._logger.debug(f"create: created and saved group: {obj}")
	
	
	def read(self, _id):
		row = self._db.execute_db_query("""SELECT id, name, comment, disabled FROM groups WHERE id == :_id""", {"_id": _id})
		new_obj = self.factory(row)
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
			self.dict[i[0]] = self.read(i[0])
		self._logger.debug(f"load_all: finally loaded these abbrs: {self.dict}")



# new
class GroupManager(BaseManager):
	"""docstring for GroupManager"""
	def __init__(self, db = None, logger = None):
		super(GroupManager, self).__init__(db = db, logger = logger)
		self._group_factory = None
		self._groupDAO = None
		self.init_all()
		pass
	
	
	def init_all(self):
		# group_factory
		self._group_factory = GroupFactory(logger = self._logger.getChild("GroupFactory"))
		# groupDAO
		self._groupDAO = GroupDAO(db = self._db, logger = self._logger.getChild("GroupDAO"), factory = self._group_factory.create_from_db_row)
		self._logger.debug("init_all: complete")
		
	
	def load_all(self):
		self._logger.debug("load_all: will load all")
		self._groupDAO.load_all()
		self.dict = self._groupDAO.dict
		self._logger.debug(f"load_all: complete, loaded {len(self.dict)} groups")
	
	
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



# new
class NotAnAbbrManager(BaseManager):
	"""docstring for NotAnAbbrManager"""
	def __init__(self, db = None, logger = None):
		super(NotAnAbbrManager, self).__init__(db = db, logger = logger)
		pass
		


# new
class DBManager(BaseManager):
	"""docstring for DBManager"""
	def __init__(self, db = None, logger = None):
		super(DBManager, self).__init__(db = db, logger = logger)
		pass
	
	
	@property
	def abbr_db_as_list(self):
		"""
		arguments:
		returns: list"""
		rows = self._db.execute_db_query("""SELECT * FROM abbrs""")
		result_list = []
		for row in rows:
			result_list.append(str(row))
		self._logger.debug(f"abbr_db_as_list: will return list of db: {result_list}")
		return result_list
		


class AbbrManager_old(object):
	"""Manage abbreviations itself - create abbrs, create groups, save, edit, etc"""
	
	
	def __init__(self, db_file = "", logger = None):
		super(AbbrManager_old, self).__init__()
		
		self.db = None
		self.db = DBQueryExecutor(db_file = db_file)
		
		self._logger = logger
		pass
	
	
	
	def get_abbrs_by_name(self, abbr_name):
		"""find all descriptions of one abbr
		
		arguments: name of the abbreviation
		returns: list of descriptions if abbr exist, None otherwise
		"""
		self._logger.debug("get_abbrs_by_name: got input: " + str(abbr_name))
		abbr_rows = self.db.execute_db_query("""SELECT descr FROM abbrs WHERE name == :abbr_name and disabled == 0""", {"abbr_name": abbr_name})
		naa_row = self.db.execute_db_query("""SELECT id FROM not_an_abbr WHERE name == :abbr_name""", {"abbr_name": abbr_name})
		if len(naa_row) != 0:
			self._logger.debug("get_abbrs_by_name: detected exception with id(s): " + str(naa_row) + ". will return None")
			return None
		result = []
		self._logger.debug("get_abbrs_by_name: got raw row: " + str(abbr_rows))
		for a in abbr_rows:
			result.append(a[0])
		self._logger.debug("get_abbrs_by_name: will return descriptions: " + str(result))
		return result
	
	
	# def save_abbr(self, abbr):
	# 	"""
	# 	arguments: abbr - dict of abbr
	# 	"""
	# 	self._logger.debug("save_abbr: will save abbr " + str(abbr))
	# 	self.db.execute_db_query("""UPDATE abbrs SET name = :name, descr = :descr, group_id = :group_id, comment = :comment, disabled = :disabled WHERE id = :id""", {"id": abbr["id"],
	# 		"name": abbr["abbr"],
	# 		"descr": abbr["descr"],
	# 		"group_id": abbr["group_id"],
	# 		"comment": abbr["comment"],
	# 		"disabled": 1 if abbr["disabled"] is True else 0})
	# 	self._logger.info("save_abbr: saved abbr as: " + str(abbr))
	
	
	def delete_abbr_by_id(self, abbr_id):
		self.db.execute_db_query("""DELETE FROM abbrs WHERE id = :id""", {"id": abbr_id})
		self._logger.info("delete_abbr_by_id: deleted abbr with id " + str(abbr_id))
		
	
	def get_group_id_by_name(self, group_name):
		if group_name == None or group_name == "":
			return None
		group_id_row = self.db.execute_db_query("""SELECT id FROM groups WHERE name = :group_name""", {"group_name": group_name})
		if len(group_id_row) == 0:
			self._logger.debug("get_group_id_by_name: not found group with name: " + str(group_name))
			return None
		else:
			self._logger.debug("get_group_id_by_name: found group_ids: " + str(group_id_row) + ", will return: " + str(group_id_row[0]))
			return group_id_row[0]
	
	
	def get_group_name_by_id(self, group_id):
		group_name_row = self.db.execute_db_query("""SELECT name FROM groups WHERE id = :group_id""", {"group_id": group_id})
		if len(group_name_row) == 0:
			self._logger.debug("get_group_name_by_id: not found group with id: " + str(group_id))
			return None
		else:
			self._logger.debug("get_group_name_by_id: found group_names: " + str(group_name_row) + ", will return: " + str(group_name_row[0]))
			return group_name_row[0]
	
	
	# def delete_group(self, group_name):
	# 	self.db.execute_db_query("""DELETE FROM groups WHERE name = :group_name""", {"group_name": group_name})
	# 	self._logger.info("delete_group: deleted all groups with name: " + str(group_name))
	
	
	# def edit_group(self, group_name):
		
	# 	pass
		
		
	# def create_group(self, group_name, comment = "", disabled = False):
	# 	self.db.execute_db_query("""INSERT INTO groups(name, comment, disabled) VALUES(:group_name, :comment, :disabled)""", {"group_name": group_name, "comment": comment, "disabled": 1 if disabled else 0})
	# 	self._logger.info("create_group: group " + str(group_name) + " created")	
	
	
	# def disable_abbr(self, abbr_id):
	# 	try:
	# 		self.db.execute_db_query("""UPDATE abbrs SET disabled = 1 WHERE id = :abbr_id""", {"abbr_id": abbr_id})
	# 		self._logger.info("disable_abbr: group disabled: " + str(abbr_id))
	# 	except Exception as e:
	# 		print("ERROR " + str(e))
	
	
	# def enable_abbr(self, abbr_id):
	# 	try:
	# 		self.db.execute_db_query("""UPDATE abbrs SET disabled = 0 WHERE id = :abbr_id""", {"abbr_id": abbr_id})
	# 		self._logger.info("enable_abbr: group enabled: " + str(abbr_id))
	# 	except Exception as e:
	# 		print("ERROR " + str(e))

	
	# def disable_group(self, group_id):
	# 	try:
	# 		self.db.execute_db_query("""UPDATE abbrs SET disabled = 1 WHERE id = :abbr_id""", {"abbr_id": abbr_id})
	# 	except Exception as e:
	# 		print("ERROR " + str(e))
	
	
	# def enable_group(self, group_id):
	# 	try:
	# 		self.db.execute_db_query("""UPDATE abbrs SET disabled = 0 WHERE id = :abbr_id""", {"abbr_id": abbr_id})
	# 	except Exception as e:
	# 		print("ERROR " + str(e))
	
	
	# def abbr_already_exist(self, abbr, descr):
	# 	"""returns True if abbr already exist, otherwise False"""
	# 	row = self.db.execute_db_query("""SELECT id FROM abbrs WHERE name = :name AND descr = :descr""", {"name": abbr, "descr": descr})
	# 	if len(row) != 0:
	# 		self._logger.debug("if_abbr_exist: abbr already exist: " + str(abbr) + " - " + str(descr))
	# 		return True
	# 	else:
	# 		return False
		
		
	# def create_abbr(self, abbr_name, descr = "", group_name = "", comment = "", disabled = False):
	# 	""""""
	# 	# firstly, check if abbreviantion already exist
	# 	if self.abbr_already_exist(abbr_name, descr):
	# 		self._logger.debug("create_abbr: will not create abbr " + str(abbr_name) + " - it already exist")
	# 		return None
		
	# 	# check if group already exist
	# 	target_group_id = self.get_group_id_by_name(group_name)
	# 	if target_group_id is None and group_name is not None:
	# 		# создаем группу
	# 		self._logger.debug("")
	# 		self.create_group(group_name)
	# 		target_group_id = self.get_group_id_by_name(group_name)
		
	# 	# creating abbr
	# 	self.db.execute_db_query("""INSERT INTO abbrs(name, descr, group_id, comment, disabled) VALUES(:name, :descr, :group_id, :comment, :disabled)""", {"name": abbr_name, "descr": descr, "group_id": target_group_id, "comment": comment, "disabled": 1 if disabled else 0})
	# 	self._logger.info("create_abbr: created abbr: " + str(abbr_name) + ", descr: " + str(descr) + ", comment: " + str(comment) + ", disabled: " + str(disabled))
		
	
	# def import_from_dict(self, abbr_db_dict):
	# 	self._logger.info("import_from_dict: starting import from dict...")
	# 	for k in abbr_db_dict.keys():
	# 		for descr in abbr_db_dict[k]:
	# 			self._logger.debug("import_from_dict: importing key " + str(k) + ", value " + str(descr))
	# 			self.create_abbr(k, descr = descr, comment = "added from import")
	# 	self._logger.debug("import_from_dict: import complete.")
	
	
	def is_not_an_abbr(self, not_an_abbr):
		row = self.db.execute_db_query("""SELECT id FROM not_an_abbr WHERE name = :not_an_abbr""", {"not_an_abbr": not_an_abbr})
		if len(row) == 0:
			return False
		else:
			return True
	
	
	def create_not_an_abbr(self, not_an_abbr, comment = "", disabled = False):
		if not self.is_not_an_abbr(not_an_abbr):
			# create if not exist
			self.db.execute_db_query("""INSERT INTO not_an_abbr(name, comment, disabled) VALUES(:name, :comment, :disabled)""", {"name": not_an_abbr, "comment": comment, "disabled": 1 if disabled else 0})
		pass

	
	def print_db(self):
		result = []
		row = self.db.execute_db_query("""SELECT * FROM abbrs""")
		for r in row:
			result.append(str(r) + "\n")
		
		return result
	
	
	def abbr_line_to_dict(self, line):
		abbr = {}
		abbr["id"] = line[0]
		abbr["abbr"] = line[1]
		abbr["descr"] = line[2]
		abbr["group_id"] = line[3]
		abbr["group_name"] = line[3]
		abbr["comment"] = line[4]
		abbr["disabled"] = True if line[5] == 1 else False
		return abbr
	
	
	# @property
	# def abbr_db_as_list(self):
	# 	"""export all abbrs from DB as list of dicts
	# 	arguments:
	# 	returns: list"""
	# 	rows = self.db.execute_db_query("""SELECT * FROM abbrs""")
	# 	result_list = []
	# 	for row in rows:
	# 		# abbr = {}
	# 		# abbr["id"] = row[0]
	# 		# abbr["abbr"] = row[1]
	# 		# abbr["descr"] = row[2]
	# 		# abbr["group_id"] = row[3]
	# 		# abbr["group_name"] = row[3]
	# 		# abbr["comment"] = row[4]
	# 		# abbr["disabled"] = row[5]
	# 		abbr = self.abbr_line_to_dict(row)
	# 		result_list.append(abbr)
	# 	return result_list
	
	
	# def get_abbr_by_id(self, abbr_id):
	# 	"""
		
	# 	arguments: abbr_id: int
	# 	returns: dict of abbr"""
	# 	row = self.db.execute_db_query("""SELECT * FROM abbrs WHERE id = :id""", {"id": abbr_id})
	# 	if len(row) == 0 or len(row[0]) == 0:
	# 		self._logger.error("get_abbr_by_id: abbr with id " + str(abbr_id) + " not found")
	# 		return None
	# 	abbr = self.abbr_line_to_dict(row[0])
	# 	self._logger.debug("get_abbr_by_id: returning " + str(abbr))
	# 	return abbr
	


class AbbrHelperApp(object):
	"""docstring for AbbrHelperApp"""
	
	def __init__(self, logger = None, db = None):
		super(AbbrHelperApp, self).__init__()
		
		# self.DB_FILE = db_file
		self._db = db
		self.DB_DIR = "./DBs"
		self.db = {}
		self.DB_DIVIDER = ";"
		self.WORD_DELIMETERS = ".,/\\!@?:;-+=\n()\"\'«»*"
		
		self.input_word_list = []
		self.input_text = ""
		self.result_abbrs = set()
		
		self.db_manager = None
		self.abbr_manager = None
		self.group_manager = None
		self.not_an_abbr_manager = None
		
		self._logger = logger
		# self.abbr_manager = AbbrManager(db_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), "abbr_helper.db"), logger = self._logger.getChild("AbbrDB"))
		# self.abbr_manager = AbbrManager(db_manager = self._db_manager, logger = self._logger.getChild("AbbrDB"))
	
		self._logger.debug("AbbrHelper: inited")
		self.report = ""
		
		self.init_all()
		pass
	
	
	def init_all(self):
		# abbr_manager
		self.abbr_manager = AbbrManager(db = self._db, logger = self._logger.getChild("AbbrManager"))
		
		# group_manager
		self.group_manager = GroupManager(db = self._db, logger = self._logger.getChild("GroupManager"))\
		
		# not_an_abbr_manager
		
		
		# db_manager
		self.db_manager = DBManager(db = self._db, logger = self._logger.getChild("DBManager"))
		self._logger.debug("init_all: complete")
		pass
	
	
	def load_all(self):
		# abbr
		self.abbr_manager.load_all()
		# group
		self.group_manager.load_all()
		# notanabbr
		self._logger.info("load_all: all loaded")
	
	
	# def load_db(self):
	# 	self.db = {}
	# 	self._logger.debug("will load db...")
	# 	self.load_db_from_file()
	# 	self.abbr_manager.import_from_dict(self.db)
			
	
	def load_db_from_file(self, file = None):
		if file is None:
			file = self.DB_FILE
		
		self._logger.info("loading DB from file " + str(file))
		with open(file, "r") as f:
			all_lines = f.readlines()
			for line in all_lines:
				if not self.validate_db_line(line):
					print("ERROR invalid DB line " + str(line))
					continue
				
				line_fields = line.replace("\n", "").split(self.DB_DIVIDER)
				abbr_name = line_fields[0]
				abbr_decoding = line_fields[1:]
				if abbr_name not in self.db.keys():
					self.db[abbr_name] = []
				self.db[abbr_name].extend(abbr_decoding)
	
	
	def format_abbr(self, abbr, descr_list):
		self._logger.debug("format_abbr: got input: abbr: " + str(abbr) + ", descr_list: " + str(descr_list))
		if abbr == "" or abbr is None or len(abbr) == 0:
			return "\n"
		
		try:
			result = ""
			for d in descr_list:
				result += abbr + " - " + d + "\n"
			return result
			
		except Exception as e:
			self._logger.error("ERROR: format_abbr: " + str(e) + " while parsing abbr: " + str(abbr) + ", descriptions: " + str(descr_list))
			return ""
	
	
	def normalize_input_line(self, line):
		for c in self.WORD_DELIMETERS:
			line = line.replace(c, " ")
		return line
	
	
	def load_input_file(self, path_to_file):
		if not os.path.isfile(path_to_file):
			print("E this is not a file - " + str(path_to_file))
			return False
			
		if path_to_file.endswith(".txt") or path_to_file.endswith(".TXT"):
			self._logger.info("load_input_file: detected TXT file")
			self.load_input_txt_file(path_to_file)
		elif path_to_file.endswith(".docx") or path_to_file.endswith(".DOCX"):
			self._logger.info("load_input_file: detected DOCX file")
			self.load_input_docx_file(path_to_file)
		else:
			self._logger.error("load_input_file: unsupported file format???")
		
	
	def load_input_txt_file(self, path_to_file):
		self.input_word_list = []
		self.input_text = ""
		with open(path_to_file, "r") as f:
			input_lines = f.readlines()
			for iline in input_lines:
				self.input_text += iline
				iline = self.normalize_input_line(iline)
				self.input_word_list.extend(iline.split())
	
	
	def load_input_docx_file(self, path_to_file):
		self.input_word_list = []
		self.input_text = ""
		try:
			docfile = docx.Document(path_to_file)
			for par in docfile.paragraphs:
				self.input_text += par.text + "\n"
		except Exception as e:
			print("E error while reading DOCX file: " + str(e))
		self.input_word_list = self.normalize_input_text().split()
		# print("D got text " + str(self.input_text))
		print("D len of input_text: " + str(len(self.input_text)))
	
	
	def validate_db_line(self, line):
		if self.DB_DIVIDER not in line:
			return False
		if line.startswith("#"):
			return False
		if len(line) <= 1:
			return False
		fields = line.split(self.DB_DIVIDER)
		# if fields[0].islower():
		# 	return False
		# TODO: проверка всех полей
		return True
	
	
	def normalize_input_text(self):
		result = self.input_text
		for c in self.WORD_DELIMETERS:
			result = result.replace(c, " ")
		return result
		
	
	def check_db(self):
		""""""
		valid_lines = []
		with open(self.DB_FILE, "r") as f:
			lines = f.readlines()
			for l in lines:
				if l not in valid_lines:
					valid_lines.append(l)
		
		
		with open(self.DB_FILE, "w") as f:
			f.writelines(valid_lines)
	
	
	# new version
	def find_all_abbrs(self):
		"""get all abbreviations from input text, either known or unknown"""
		self.result_abbrs = set()
		
		words = self.normalize_input_text().split()
		for w in words:
			if is_abbr(w):
				self._logger.debug("find_all_abbrs: found abbr " + str(w))
				self.result_abbrs.add(w)
		
		self._logger.debug("find_all_abbrs: total abbr set is: " + str(self.result_abbrs))
		
		
	def gen_report(self):
		found_abbrs = []
		not_found_abbrs = []
		result_abbrs_list = list(self.result_abbrs)
		result_abbrs_list.sort()
		self._logger.debug("gen_report: will work with " + str(len(result_abbrs_list)) + " abbrs")
		
		self.report = "==============================\nFound abbrs:\n==============================\n"
		for w in result_abbrs_list:
			descr_list = self.abbr_manager.get_abbrs_by_name(w)
			if len(descr_list) == 0:
				self._logger.debug("gen_report: abbr not found in db: " + str(w))
				self.report += str(w) + " - \n"
			else:
				self._logger.debug("gen_report: found abbr in db for: " + str(w) + " - " + str(descr_list))
				found_abbrs.extend(descr_list)
				self.report += self.format_abbr(w, descr_list)
				pass

		return self.report
	



class AbbrHelperWebApp(object):
	"""docstring for AbbrHelperWebApp"""
	
	def __init__(self, db_file = None, log_file = None):
		super(AbbrHelperWebApp, self).__init__()
		
		self.host = "0.0.0.0"
		self.port = 8080
		
		self.LOG_FILE = "/var/log/abbr_helper.log" if log_file is None else log_file
		self.DB_FILE = db_file
		
		self.main_app = None
		self.web_app = None
		
		# main app parameters
		self.ALLOWED_EXTENSIONS = ["txt", "TXT", "docx", "DOCX"]
		self.UPLOAD_DIR = "/tmp/abbrhelper"
		self.MAX_FILE_SIZE = 250 * 1024 * 1024 # in bytes
		
		# logger initialization
		self._logger = logging.getLogger("abbr_helper_web_app")
		self._logger.setLevel(logging.DEBUG)
		fh = logging.FileHandler(self.LOG_FILE)
		fh.setLevel(logging.DEBUG)
		formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
		fh.setFormatter(formatter)
		self._logger.addHandler(fh)
		self._logger.info("=========  AbbrHelperWebApp starting. Version " + str(__version__) + "  =========")
		
		# 
		self.check_upload_dir()
		self.init_main_app()
		pass
	
	
	def init_main_app(self):
		db = DBQueryExecutor(db_file = self.DB_FILE)
		self._logger.debug("init_main_app: will init main app...")
		self.main_app = AbbrHelperApp(db = db, logger = self._logger.getChild("main_app"))
		self.main_app.load_all()
		self._logger.debug("init_main_app: complete")
		
	
	def check_upload_dir(self):
		if not os.path.isdir(self.UPLOAD_DIR):
			os.makedirs(self.UPLOAD_DIR)
			self._logger.info("check_upload_dir: UPLOAD_DIR created because it was absent: " + str(self.UPLOAD_DIR))
		
	
	def run_web_interface(self):
		self.web_app = Flask(__name__)
		self.web_app.secret_key = "qwxnmkqempemjabefwbdirbvdfcwkh"
		self.web_app.config["UPLOAD_FOLDER"] = self.UPLOAD_DIR
		self.web_app.config["MAX_CONTENT_LENGTH"] = self.MAX_FILE_SIZE
		
		
		@self.web_app.route("/", methods = ["GET", "POST"])
		def main_page():
			if request.method == "GET":
				return render_template("main_page.html", app_version = __version__)
		
		
		@self.web_app.route("/upload-file", methods = ["GET", "POST"])
		def upload_file():
			if request.method == "GET":
				return render_template("upload_file.html")
				
			if request.method == "POST":
				if "file" not in request.files:
					self._logger.error("upload_file: no file part found in request!")
					return redirect(request.url)
				f = request.files["file"]
				if f.filename == "":
					self._logger.error("upload_file: no file selected in form")
					return redirect(request.url)
				if f:
					# try\except here
					filename = secure_filename(f.filename)
					f.save(os.path.join(self.web_app.config["UPLOAD_FOLDER"], filename)) # currently only with temp file
					self._logger.info("upload_file: uploaded file " + str(os.path.join(self.web_app.config["UPLOAD_FOLDER"], filename)))
					
					# read input file
					self.main_app.load_input_file(os.path.join(self.web_app.config["UPLOAD_FOLDER"], filename))
					self.main_app.find_all_abbrs()
					report = self.main_app.gen_report()
					
					os.remove(os.path.join(self.web_app.config["UPLOAD_FOLDER"], filename))
				
				return render_template("show_result.html", found_abbrs = self.main_app.result_abbrs, report = report.replace("\n", "<br>\n"))
		
		
		@self.web_app.route("/upload-db-file", methods = ["GET", "POST"])
		def upload_db_file():
			if request.method == "GET":
				return render_template("upload_db_file.html")
				
			if request.method == "POST":
				if "file" not in request.files:
					self._logger.error("upload_db_file: no file part found in request!")
					return redirect(request.url)
				
				f = request.files["file"]
				if f.filename == "":
					self._logger.error("upload_db_file: no file selected")
					return redirect(request.url)
				
				if f:
					# try\except here
					filename = secure_filename(f.filename)
					f.save(os.path.join(self.web_app.config["UPLOAD_FOLDER"], filename)) # currently only with temp file
					self._logger.info("upload_db_file: uploaded file " + str(os.path.join(self.web_app.config["UPLOAD_FOLDER"], filename)))
					
					# read input file
					
					# finally delet temp file
					os.remove(os.path.join(self.web_app.config["UPLOAD_FOLDER"], filename))
				
				return render_template("show_result.html", found_abbrs = self.main_app.result_abbrs, report = report.replace("\n", "<br>\n"))
		
		
		@self.web_app.route("/show-db", methods = ["GET"])
		def show_db():
			if request.method == "GET":
				return render_template("show_db.html", db = self.main_app.db_manager.abbr_db_as_list)
		
		
		@self.web_app.route("/create-abbr", methods = ["GET", "POST"])
		def create_abbr():
			if request.method == "GET":
				return render_template("create_edit_abbr.html", abbr = {})
			if request.method == "POST":
				abbr = {}
				abbr_name = request.form["abbreviation"]
				descr = request.form["description"]
				comment = request.form["comment"]
				disabled = True if request.form.get("disabled") is not None else False
				if len(abbr_name) < 2:
					self._logger.info(f"create_abbr: did not added abbr. Reason: abbr {abbr_name} did not passed the check, too short")
				elif len(descr) < 3:
					self._logger.info(f"create_abbr: did not added abbr. Reason: description {descr} did not passed the check, too short")
				else:
					self.main_app.abbr_manager.create_abbr(name = abbr_name, descr = descr, comment = comment, disabled = disabled)	
				return render_template("create_edit_abbr.html", abbr = {})
		
		
		@self.web_app.route("/edit-abbr/<int:abbr_id>", methods = ["GET", "POST"])
		def edit_abbr(abbr_id):
			abbr = self.main_app.abbr_manager.get_abbr_by_id(abbr_id)
			if abbr is None:
				return render_template("blanc.html", page_text = f"<br>ERRROR: abbr with id {abbr_id} not found!")
			if request.method == "GET":
				return render_template("create_edit_abbr.html", abbr = abbr)
			if request.method == "POST":
				self._logger.debug("edit_abbr: will edit abbr " + str(abbr_id))
				try:
					abbr.name = request.form["abbreviation"]
					abbr.descr = request.form["description"]
					abbr.comment = request.form["comment"]
					group_name_list = request.form["group_list"]
					group_id_list = self.main_abbr.group_manager.get_id_list_by_name_list(group_name_list.replace(", ", ",").split(","))
					self._logger.debug(f"edit_abbr: got list of group names: {group_name_list}, list of ids of groups: {group_id_list}")
					abbr.group_list = group_id_list
					abbr.disabled = True if request.form.get("disabled") is not None else False
					# abbr["group_id"] = None if (request.form["group_id"] == "None" or request.form["group_id"] == "") else int(request.form["group_id"])
					self.main_app.abbr_manager.save(abbr)
				except Exception as e:
					self._logger.error("edit_abbr: error: " + str(e) + ", traceback: " + traceback.format_exc())
				self._logger.debug("returning page ")
				return render_template("create_edit_abbr.html", abbr = abbr)
		
		
		# ok
		@self.web_app.route("/delete-abbr/<int:abbr_id>", methods = ["GET", "POST"])
		def delete_abbr(abbr_id):
			found_abbr = self.main_app.abbr_manager.get_abbr_by_id(abbr_id)
			if request.method == "GET":
				return render_template("delete_abbr.html", abbr = found_abbr)
			if request.method == "POST":
				self.main_app.abbr_manager.delete_abbr(found_abbr)
				return render_template("main_page.html")
		
		
		@self.web_app.route("/show-all-abbrs", methods = ["GET"])
		def show_all_abbrs():
			self._logger.debug(f"show_all_abbrs: will display self.main_app.abbr_manager.dict: {self.main_app.abbr_manager.dict}")
			return render_template("show_all_abbrs.html", abbrs = self.main_app.abbr_manager.dict)
	
		
		@self.web_app.route("/show-all-groups", methods = ["GET"])
		def show_all_groups():
			self._logger.debug(f"show_all_groups: will display self.main_app.group_manager.dict")
			return render_template("show_all_groups.html", groups = self.main_app.group_manager.dict)
		
		
		@self.web_app.route("/edit-group/<int:group_id>", methods = ["GET", "POST"])
		def edit_group(group_id):
			found_group = self.main_app.group_manager.get_group_by_id(group_id)
			if request.method == "GET":
				return render_template("create_edit_group.html", group = found_group)
			if request.method == "POST":
				
				# 
				
				return render_template("create_edit_group.html", group = found_group)
			pass
		
				
		# custom Jinja filters
		self.web_app.jinja_env.filters["empty_on_None"] = empty_on_None
		self.web_app.jinja_env.filters["empty_filter"] = empty_filter
		
		self._logger.debug("run_web_interface: launching web app interface...")
		self.web_app.run(host = self.host, port = self.port, use_reloader = False)
	


def print_help():
	print(f"    {os.path.abspath(__file__)}: Manage abbreviations.")
	print("    Use --web-app to lauch web interface.")
	print("    Use --db-file to specify DB file.")


if __name__ == "__main__":
	args = sys.argv[1:]
	
	if "--db-file" in args:
		DB_FILE == args[args.index("--db-file") + 1]
	else:
		DB_FILE = db_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), "abbr_helper.db")
	
	
	
	if "--web-app" in args:
		ahwapp = AbbrHelperWebApp(db_file = DB_FILE)
		ahwapp.run_web_interface()
		sys.exit(0)
	
	# print help and exit
	print_help()
	pass