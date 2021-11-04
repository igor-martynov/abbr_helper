#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from dataclasses import dataclass, field
from typing import List

import os
from base_classes import *



class AbbrFinder(object):
	"""find abbrs in text"""
	
	def __init__(self, logger = None, abbr_dict = None, not_an_abbr_dict = None):
		super(AbbrFinder, self).__init__()
		self._logger = logger
		
		self.abbr_dict = abbr_dict
		self.not_an_abbr_dict = not_an_abbr_dict
		
		self.input_text = ""
		self.input_word_list = []
		pass
	
	
	def normalize_input_line(self, line):
		for c in self.WORD_DELIMETERS:
			line = line.replace(c, " ")
		return line
	
	
	def format_abbrs(self, abbr_list):
		self._logger.debug(f"format_abbr: got input: abbr_list: {abbr_list}")
		if len(abbr_list) == 0:
			self._logger.error("format_abbrs: got emptu abbr_list")
			return ""
		result = ""
		for a in abbr_list:
			result += abbr.name + " - " + abbr.descr + "\n"
		return result
	
	
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
		self._logger.debug(f"load_input_txt_file: got {len(self.input_word_list)} words from file {path_to_file}")
	
	
	def load_input_docx_file(self, path_to_file):
		self.input_word_list = []
		self.input_text = ""
		try:
			docfile = docx.Document(path_to_file)
			for par in docfile.paragraphs:
				self.input_text += par.text + "\n"
		except Exception as e:
			self._logger.error(f"load_input_docx_file: error while reading DOCX file: {e}")
		self.input_word_list = self.normalize_input_text().split()
		print("D len of input_text: " + str(len(self.input_text)))
		self._logger.debug(f"load_input_docx_file: got {len(self.input_word_list)} words from file {path_to_file}")
	
	
	def find_abbrs_in_file(self, path_to_file):
		self.load_input_file(path_to_file)
		self.find_abbrs_in_input_text()
		pass
	
	
	def is_not_an_abbr(self, not_an_abbr):
		for naa in self.not_an_abbr:
			if naa.name == not_an_abbr and not naa.disabled:
				return True
			else:
				return False
	
	
	def find_abbrs_in_input_text(self):
		# step 1 - find all abbrs in input words
		all_found_abbrs = set()
		for w in self.input_word_list:
			if is_abbr(w):
				all_found_abbrs.add(w)
		self._logger.debug(f"find_abbrs_in_input_text: found abbrs: {all_found_abbrs}")
		
		pass
	
	
	