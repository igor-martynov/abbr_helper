#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 2021-11-05

__version__ = "0.9.0"
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

# from dataclasses import dataclass, field
# from typing import List



# flask web interface
from flask import Flask, flash, request, redirect, url_for, Response, render_template
from werkzeug.utils import secure_filename

# logging
import logging
import logging.handlers

# base classes
from base_classes import *
from abbr import *
from group import *
from abbr_finder import *




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



class AbbrHelperApp(object):
	"""docstring for AbbrHelperApp"""
	
	def __init__(self, logger = None, db = None):
		super(AbbrHelperApp, self).__init__()
		
		# self.DB_FILE = db_file
		self._db = db
		self.DB_DIR = "./DBs"
		self.db = {}
		self.DB_DIVIDER = ";"
		# self.WORD_DELIMETERS = ".,/\\!@?:;-+=\n()\"\'«»*"
		
		self.input_word_list = []
		self.input_text = ""
		self.result_abbrs = set()
		
		self.db_manager = None
		self.abbr_manager = None
		self.group_manager = None
		self.not_an_abbr_manager = None
		self.abbr_finder = None
		
		self._logger = logger
		self.report = ""
		
		self.init_all()
		pass
	
	
	def init_all(self):
		# abbr_manager
		self.abbr_manager = AbbrManager(db = self._db, logger = self._logger.getChild("AbbrManager"))
		
		# group_manager
		self.group_manager = GroupManager(db = self._db, logger = self._logger.getChild("GroupManager"))\
		
		# not_an_abbr_manager
		
		
		# abbr_finder
		self.abbr_finder = AbbrFinder(abbr_manager = self.abbr_manager, not_an_abbr_dict = {}, logger = self._logger.getChild("AbbrFinder"))
		
		
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
					# print("ERROR invalid DB line " + str(line))
					continue
				
				line_fields = line.replace("\n", "").split(self.DB_DIVIDER)
				abbr_name = line_fields[0]
				abbr_decoding = line_fields[1:]
				if abbr_name not in self.db.keys():
					self.db[abbr_name] = []
				self.db[abbr_name].extend(abbr_decoding)
	
	
	# def format_abbr(self, abbr, descr_list):
	# 	self._logger.debug("format_abbr: got input: abbr: " + str(abbr) + ", descr_list: " + str(descr_list))
	# 	if abbr == "" or abbr is None or len(abbr) == 0:
	# 		return "\n"
		
	# 	try:
	# 		result = ""
	# 		for d in descr_list:
	# 			result += abbr + " - " + d + "\n"
	# 		return result
			
	# 	except Exception as e:
	# 		self._logger.error("ERROR: format_abbr: " + str(e) + " while parsing abbr: " + str(abbr) + ", descriptions: " + str(descr_list))
	# 		return ""
	
	
	# def normalize_input_line(self, line):
	# 	for c in self.WORD_DELIMETERS:
	# 		line = line.replace(c, " ")
	# 	return line
	
	
	# def load_input_file(self, path_to_file):
	# 	if not os.path.isfile(path_to_file):
	# 		print("E this is not a file - " + str(path_to_file))
	# 		return False
			
	# 	if path_to_file.endswith(".txt") or path_to_file.endswith(".TXT"):
	# 		self._logger.info("load_input_file: detected TXT file")
	# 		self.load_input_txt_file(path_to_file)
	# 	elif path_to_file.endswith(".docx") or path_to_file.endswith(".DOCX"):
	# 		self._logger.info("load_input_file: detected DOCX file")
	# 		self.load_input_docx_file(path_to_file)
	# 	else:
	# 		self._logger.error("load_input_file: unsupported file format???")
		
	
	# def load_input_txt_file(self, path_to_file):
	# 	self.input_word_list = []
	# 	self.input_text = ""
	# 	with open(path_to_file, "r") as f:
	# 		input_lines = f.readlines()
	# 		for iline in input_lines:
	# 			self.input_text += iline
	# 			iline = self.normalize_input_line(iline)
	# 			self.input_word_list.extend(iline.split())
	
	
	# def load_input_docx_file(self, path_to_file):
	# 	self.input_word_list = []
	# 	self.input_text = ""
	# 	try:
	# 		docfile = docx.Document(path_to_file)
	# 		for par in docfile.paragraphs:
	# 			self.input_text += par.text + "\n"
	# 	except Exception as e:
	# 		print("E error while reading DOCX file: " + str(e))
	# 	self.input_word_list = self.normalize_input_text().split()
	# 	# print("D got text " + str(self.input_text))
	# 	print("D len of input_text: " + str(len(self.input_text)))
	
	
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
		
	
	# def check_db(self):
	# 	""""""
	# 	valid_lines = []
	# 	with open(self.DB_FILE, "r") as f:
	# 		lines = f.readlines()
	# 		for l in lines:
	# 			if l not in valid_lines:
	# 				valid_lines.append(l)
		
		
	# 	with open(self.DB_FILE, "w") as f:
	# 		f.writelines(valid_lines)
	
	
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
		self._logger.info(f"==== STARTING AbbrHelper v{__version__} ====")
		
		self.web_app = Flask(__name__)
		self.web_app.secret_key = "qwxnmkqempemjabefwbdirbvdfcwkh"
		self.web_app.config["UPLOAD_FOLDER"] = self.UPLOAD_DIR
		self.web_app.config["MAX_CONTENT_LENGTH"] = self.MAX_FILE_SIZE
		
		
		@self.web_app.route("/", methods = ["GET", "POST"])
		def main_page():
			if request.method == "GET":
				return render_template("main_page.html", app_version = __version__)
		
		
		@self.web_app.route("/upload-input-file", methods = ["GET", "POST"])
		def upload_input_file():
			if request.method == "GET":
				return render_template("upload_file.html")
				
			if request.method == "POST":
				if "file" not in request.files:
					self._logger.error("upload_input_file: no file part found in request!")
					return redirect(request.url)
				f = request.files["file"]
				if f.filename == "":
					self._logger.error("upload_input_file: no file selected in form")
					return redirect(request.url)
				if f:
					# try\except here
					try:
						filename = secure_filename(f.filename)
						f.save(os.path.join(self.web_app.config["UPLOAD_FOLDER"], filename)) # currently only with temp file
						self._logger.info("upload_input_file: uploaded file " + str(os.path.join(self.web_app.config["UPLOAD_FOLDER"], filename)))
					except Exception as e:
						self._logger.error(f"upload_input_file: could not save uploaded file as {filename}")
					# read input file
					self.main_app.abbr_finder.find_abbrs_in_file(os.path.join(self.web_app.config["UPLOAD_FOLDER"], filename))
					# self.main_app.abbr_finder.find_all_abbrs()
					# report = self.main_app.abbr_finder.gen_report()
					report = self.main_app.abbr_finder.report
					
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
				return render_template("blank.html", page_text = f"<br>ERRROR: abbr with id {abbr_id} not found!")
			if request.method == "GET":
				return render_template("create_edit_abbr.html", abbr = abbr)
			if request.method == "POST":
				self._logger.debug("edit_abbr: will edit abbr " + str(abbr_id))
				try:
					abbr.name = request.form["abbreviation"]
					abbr.descr = request.form["description"]
					abbr.comment = request.form["comment"]
					group_name_list = request.form["group_list"]
					# group_id_list = self.main_app.group_manager.get_id_list_by_name_list(group_name_list.replace(", ", ",").split(","))
					# self._logger.debug(f"edit_abbr: got list of group names: {group_name_list}, list of ids of groups: {group_id_list}")
					# abbr.group_list = group_id_list
					groups_str = request.form["group_list"]
					# abbr.groups = self.main_app.groups_from_str(groups_str)
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
		
		# ok
		@self.web_app.route("/show-all-abbrs", methods = ["GET"])
		def show_all_abbrs():
			self._logger.debug(f"show_all_abbrs: will display self.main_app.abbr_manager.dict: {self.main_app.abbr_manager.dict}")
			return render_template("show_all_abbrs.html", abbrs = self.main_app.abbr_manager.dict)
	
		# ok
		@self.web_app.route("/show-all-groups", methods = ["GET"])
		def show_all_groups():
			self._logger.debug(f"show_all_groups: will display self.main_app.group_manager.dict")
			return render_template("show_all_groups.html", groups = self.main_app.group_manager.dict)
		
		
		@self.web_app.route("/edit-group/<int:group_id>", methods = ["GET", "POST"])
		def edit_group(group_id):
			found_group = self.main_app.group_manager.get_group_by_id(group_id)
			if found_group is None:
				return render_template("blank.html", page_text = f"<br>ERRROR: group with id {group_id} not found!")
			if request.method == "GET":
				return render_template("create_edit_group.html", group = found_group)
			if request.method == "POST":
				name = request.form["name"]
				comment = request.form["comment"]
				disabled = True if request.form.get("disabled") is not None else False
				return render_template("create_edit_group.html", group = found_group)
		
		
		@self.web_app.route("/create-group", methods = ["GET", "POST"])
		def create_group():
			if request.method == "GET":
				return render_template("create_edit_group.html", group = None)
			if request.method == "POST":
				self._logger.debug("create_group: got POST, will create group according to form")
				name = request.form["name"]
				comment = request.form["comment"]
				disabled = True if request.form.get("disabled") is not None else False
				self._logger.debug(f"create_group: got from form: name: {name}, comment: {comment}, disabled: {disabled}")
				new_obj = self.main_app.group_manager.create(name = name, comment = comment, disabled = disabled)		
				return redirect(f"/edit-group/{new_obj._id}")
		
		
		@self.web_app.route("/delete-group/<int:group_id>", methods = ["GET", "POST"])
		def delete_group(group_id):
			found_group = self.main_app.group_manager.get_group_by_id(group_id)
			if found_group is None:
				return render_template("blank.html", page_text = f"<br>ERRROR: group with id {group_id} not found!")
			if request.method == "GET":
				return render_template("delete_group.html", group = found_group)
			if request.method == "POST":
				self.main_app.group_manager.delete(found_group)
				return render_template("main_page.html")
		
		
				
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