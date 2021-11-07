#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# from dataclasses import dataclass, field
# from typing import List

from base_classes import *


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

