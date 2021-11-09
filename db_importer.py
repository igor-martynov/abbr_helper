#!/usr/bin/env python3
# -*- coding: utf-8 -*-



class DBImporter(object):
	"""handler import from CSV files"""
	
	def __init__(self, logger = None):
		super(DBImporter, self).__init__()
		self.DB_DIVIDER = ";"
		self._logger = logger
		self.new_abbr_dict = {}
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
	
	
	def load_db_from_file(self, filename):
		self.new_abbr_dict = {}
		self._logger.info(f"load_db_from_file: loading DB from file {filename}")
		with open(filename, "r") as f:
			all_lines = f.readlines()
			for line in all_lines:
				if self.validate_db_line(line) is False:
					self._logger.error(f"load_db_from_file: line of file '{line}' is invalid")
					continue
				elif self.validate_db_line(line) is None:
					self._logger.info(f"load_db_from_file: line of file '{line}' is commented out")
					continue
				else:
					self._logger.info(f"load_db_from_file: line of file '{line}' is OK")
				line_fields = line.replace("\n", "").split(self.DB_DIVIDER)
				abbr_name = line_fields[0]
				abbr_decoding = line_fields[1:]
				if abbr_name not in self.new_abbr_dict.keys():
					self.new_abbr_dict[abbr_name] = []
				self.new_abbr_dict[abbr_name].extend(abbr_decoding)
		self._logger.info(f"load_db_from_file: result dict is: {self.new_abbr_dict}")
		
		pass

