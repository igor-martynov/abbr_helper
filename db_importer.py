#!/usr/bin/env python3
# -*- coding: utf-8 -*-



class DBImporter(object):
	"""handler import from CSV files"""
	
	def __init__(self):
		super(DBImporter, self).__init__()
		self.DB_DIVIDER = ";"
		pass
	
	
	def validate_db_line(self, line):
		if self.DB_DIVIDER not in line:
			return False
		if line.startswith("#"):
			return None
		if len(line) <= 1:
			return False
		fields = line.split(self.DB_DIVIDER)
		# if fields[0].islower():
		# 	return False
		# TODO: проверка всех полей
		return True
	
	
	def load_db_from_file(self, file = None):
		if file is None:
			file = self.DB_FILE
		
		self._logger.info("loading DB from file " + str(file))
		with open(file, "r") as f:
			all_lines = f.readlines()
			for line in all_lines:
				if not self.validate_db_line(line):
					# print("ERROR invalid DB line " + str(line))
					continue
				
				line_fields = line.replace("\n", "").split(self.DB_DIVIDER)
				abbr_name = line_fields[0]
				abbr_decoding = line_fields[1:]
				if abbr_name not in self.db.keys():
					self.db[abbr_name] = []
				self.db[abbr_name].extend(abbr_decoding)