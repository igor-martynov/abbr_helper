#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from dataclasses import dataclass, field
from typing import List

import os

# docx format support
import docx

from base_classes import *
from abbr import Abbr
from not_an_abbr import NotAnAbbr



def is_temp_disabled(abbr, temp_disabled_groups):
	"""if abbr is temporarily disabled"""
	for g in abbr.groups:
		if g in temp_disabled_groups:
			return True
	return False
	


class AbbrFinder(object):
	"""find abbrs in text"""
	
	def __init__(self,
		logger = None,
		abbr_manager = None,
		group_manager = None,
		not_an_abbr_manager = None):
		super(AbbrFinder, self).__init__()
		self._logger = logger
		
		self.WORD_DELIMETERS = ".,/\\!@?:;-+=\n()\"\'«»*"
		
		self.abbr_manager = abbr_manager
		self.group_manager = group_manager
		self.not_an_abbr_manager = not_an_abbr_manager
		
		self.input_text = ""
		self.input_word_list = []
		
		self.temp_disabled_groups = []
		
		self.all_found_abbrs = set()
		self.found_known_abbrs = set()
		self.found_known_not_an_abbrs = set()
	
	
	@property
	def found_unknown_abbrs(self):
		result_set = set(self.all_found_abbrs)
		for a in self.found_known_abbrs:
			try:
				result_set.remove(a.name)
			except Exception as e:
				self._logger.error(f"found_unknown_abbrs: was trying to remove {a.name} from all_found_abbrs, but goot exception: {e}")
		return result_set
	
	
	def normalize_input_line(self, line):
		for c in self.WORD_DELIMETERS:
			line = line.replace(c, " ")
		return line
	
	
	def normalize_input_text(self):
		result = self.input_text
		for c in self.WORD_DELIMETERS:
			result = result.replace(c, " ")
		return result
	
	
	def set_temp_disabled_groups(self, group_list):
		self.temp_disabled_groups = group_list
		self._logger.info(f"set_temp_disabled_groups: these groups are set to be disabled: {self.temp_disabled_groups}")
	
	
	def unset_temp_disabled_groups(self):
		self.temp_disabled_groups = []
		self._logger.debug("unset_temp_disabled_groups: unset self.temp_disabled_groups")
	
	
	def load_input_file(self, path_to_file):
		if not os.path.isfile(path_to_file):
			self._logger.error(f"load_input_file: this is not a file - {path_to_file}")
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
		self._logger.debug(f"load_input_docx_file: len of input_text: {str(len(self.input_text))}")
		self._logger.debug(f"load_input_docx_file: got {len(self.input_word_list)} words from file {path_to_file}")
	
	
	def find_abbrs_in_file(self, path_to_file):
		self.load_input_file(path_to_file)
		self.find_abbrs_in_input_text()
		self.unset_temp_disabled_groups()
	
	
	def is_not_an_abbr(self, not_an_abbr):
		if not_an_abbr not in self.not_an_abbr_manager.all_names:
			return False
		else:
			return True
	
	
	def find_abbrs_in_input_text(self):
		self._logger.debug(f"find_abbrs_in_input_text: starting step 1")
		# step 1 - find all abbrs (either known and unknown) and abbr exceptions in input words
		self.all_found_abbrs = set()
		self.found_known_abbrs = set()
		self.found_known_not_an_abbrs = set()
		for w in self.input_word_list:
			if is_abbr(w) and not self.is_not_an_abbr(w):
				self.all_found_abbrs.add(w)
			if self.is_not_an_abbr(w):
				self.found_known_not_an_abbrs.add(self.not_an_abbr_manager.get_not_an_abbr_by_name(w))
		self._logger.debug(f"find_abbrs_in_input_text: found abbrs: {self.all_found_abbrs}, not_an_abbrs: {self.found_known_not_an_abbrs}")
		self._logger.debug(f"find_abbrs_in_input_text: step 1 complete. starting step 2")
		
		# step 2 - known or unknown
		for a in self.all_found_abbrs:
			if self.is_not_an_abbr(a):
				self._logger.debug(f"find_abbrs_in_input_text: word {a} is not_an_abbr, will be ignored")
				continue
			tmp_found = self.abbr_manager.get_abbrs_by_name(a)
			found = []
			for a in tmp_found:
				if not a.disabled and not is_temp_disabled(a, self.temp_disabled_groups):
					found.append(a)
				else:
					self._logger.debug(f"find_abbrs_in_input_text: abbr {a} will be ignored because it is disabled")
			if len(found) != 0:
				self.found_known_abbrs.update(found)
				a = found
				self._logger.debug(f"find_abbrs_in_input_text: added found abbrs {found} for word {a}")
			else:
				self._logger.debug(f"find_abbrs_in_input_text: word {a} is unknown abbr")
		self._logger.debug(f"find_abbrs_in_input_text: complete. all found: {len(self.all_found_abbrs)}, known: {len(self.found_known_abbrs)}")
	
	
	def gen_report(self):
		self._report = AbbrFinderReport(found_known_abbrs = self.found_known_abbrs,
			found_unknown_abbrs = self.found_unknown_abbrs,
			found_known_not_an_abbrs = self.found_known_not_an_abbrs)
		self._logger.debug("gen_report: complete")
		return self._report
	
	
	@property
	def report(self):
		return self.gen_report()



@dataclass
class AbbrFinderReport(object):
	"""create report for AbbrFinder"""
	found_known_abbrs: List[Abbr] = field(default_factory = list)
	found_unknown_abbrs: List[str] = field(default_factory = list)
	found_known_not_an_abbrs: List[NotAnAbbr] = field(default_factory = list)
	_report_text: str = ""
	
	@property
	def all_found_abbrs(self):	
		return self.found_known_abbrs.union(self.found_unknown_abbrs)
	
	
	@property
	def text(self):
		self._report_text = ""
		# known
		self._report_text += "\n\nKNOWN ABBREVIATIONS: \n" + f"(total: {len(self.found_known_abbrs)})" + "\n\n"
		self._report_text += self.format_abbrs(self.found_known_abbrs)
		
		# unknown
		self._report_text += "\n\n\n\nUNKNOWN ABBREVIATIONS: \n" + f"(total: {len(self.found_unknown_abbrs)})" + "\n\n"
		self._report_text += self.format_abbrs(self.found_unknown_abbrs)
		
		# not_an_abbrs
		self._report_text += "\n\n\n\nKNOWN EXCEPTIONS: \n" + f"(total: {len(self.found_known_not_an_abbrs)})" + "\n\n"
		for n in [naa.name for naa in self.found_known_not_an_abbrs]:
			self._report_text += str(n) + "\n"
		
		# all
		self._report_text += "\n\n\n\nALL ABBREVIATIONS: \n" + f"(total: {len(self.all_found_abbrs)})" + "\n\n"
		self._report_text += self.format_abbrs(self.all_found_abbrs)
		return self._report_text

	
	
	@property
	def html(self):
		return self.text.replace("\n", "<br>\n")
	
	
	def format_abbrs(self, abbr_list):
		"""format abbrs to printable form, for further use in text report
		
		arguments: abbr_list: list of Abbr or list of str
		returns: formatted result as str"""
		result = ""
		sorted_list = list(abbr_list)
		sorted_list.sort(key = lambda abbr: abbr.name if isinstance(abbr, Abbr) else abbr)
		for abbr in sorted_list:
			if isinstance(abbr, Abbr):
				result += abbr.name + " - " + abbr.descr + "\n"
			else:
				try:
					result += abbr + " - \n"
				except Exception as e:
					pass
		return result
	
	