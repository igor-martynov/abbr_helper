#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from dataclasses import dataclass, field
from typing import List

import os

# docx format support
import docx

from base_classes import *
from abbr import Abbr


class AbbrFinder(object):
	"""find abbrs in text"""
	
	def __init__(self,
		logger = None,
		abbr_manager = None,
		# group_manager = None,
		not_an_abbr_dict = {}):
		super(AbbrFinder, self).__init__()
		self._logger = logger
		
		self.WORD_DELIMETERS = ".,/\\!@?:;-+=\n()\"\'«»*"
		
		self.abbr_manager = abbr_manager
		# self.group_manager = group_manager
		self.not_an_abbr_dict = not_an_abbr_dict
		
		self.input_text = ""
		self.input_word_list = []
		
		self.all_found_abbrs = set()
		self.found_known_abbrs = set()
		pass
	
	@property
	def found_unknown_abbrs(self):
		return self.all_found_abbrs - self.found_known_abbrs
	
	
	def normalize_input_line(self, line):
		for c in self.WORD_DELIMETERS:
			line = line.replace(c, " ")
		return line
	
	
	def normalize_input_text(self):
		result = self.input_text
		for c in self.WORD_DELIMETERS:
			result = result.replace(c, " ")
		return result
	
	
	def format_abbrs(self, abbr_list):
		self._logger.debug(f"format_abbr: got input: abbr_list: {abbr_list}")
		if len(abbr_list) == 0:
			self._logger.error("format_abbrs: got emptu abbr_list")
			return ""
		result = ""
		for abbr in abbr_list:
			if isinstance(abbr, Abbr):
				result += abbr.name + " - " + abbr.descr + "\n"
			else:
				result += abbr + "\n"
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
		for naa in self.not_an_abbr_dict.values():
			if naa.name == not_an_abbr and not naa.disabled:
				return True
			else:
				return False
	
	
	def find_abbrs_in_input_text(self):
		self._logger.debug(f"find_abbrs_in_input_text: starting step 1")
		# step 1 - find all abbrs (either known and unknown) in input words
		self.all_found_abbrs = set()
		self.found_known_abbrs = set()
		for w in self.input_word_list:
			if is_abbr(w):
				self.all_found_abbrs.add(w)
		self._logger.debug(f"find_abbrs_in_input_text: found abbrs: {self.all_found_abbrs}")
		self._logger.debug(f"find_abbrs_in_input_text: step 1 complete. starting step 2")
		
		# step 2 - known or unknown
		for a in self.all_found_abbrs:
			if self.is_not_an_abbr(a):
				self._logger.debug(f"find_abbrs_in_input_text: word {a} is not_an_abbr, will be ignored")
				continue
			found = self.abbr_manager.get_abbrs_by_name(a)
			if len(found) != 0:
				self.found_known_abbrs.update(found)
				self._logger.debug(f"find_abbrs_in_input_text: added found abbrs {found} for word {a}")
			else:
				self._logger.debug(f"find_abbrs_in_input_text: word {a} is unknown abbr")
		
		pass
	
	
	def gen_report(self):
		self._logger.debug("gen_report: starting")
		
		self._report = ""
		
		# known
		self._report += "\n\nKNOWN ABBREVIATIONS: \n"
		self._report += self.format_abbrs(self.found_known_abbrs)
		
		# unknown
		self._report += "\n\n\nUNKNOWN ABBREVIATIONS: \n"
		self._report += self.format_abbrs(self.found_unknown_abbrs)
		
		self._logger.debug("gen_report: complete")
		
		return self._report
		# raise NotImplemented
	
	
	@property
	def report(self):
		return self.gen_report()