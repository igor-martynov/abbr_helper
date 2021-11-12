#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 2021-11-12

__version__ = "0.9.5"
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
from db import *
from abbr import *
from group import *
from not_an_abbr import *
from abbr_finder import *
from db_importer import *



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
		# group_manager
		self.group_manager = GroupManager(db = self._db, logger = self._logger.getChild("GroupManager"))
		
		# abbr_manager
		self.abbr_manager = AbbrManager(db = self._db, logger = self._logger.getChild("AbbrManager"))
		
		# not_an_abbr_manager
		
		
		# interconnects
		self.abbr_manager.set_group_manager(self.group_manager)
		self.group_manager.set_abbr_manager(self.abbr_manager)
		
		# abbr_finder
		self.abbr_finder = AbbrFinder(abbr_manager = self.abbr_manager, not_an_abbr_dict = {}, logger = self._logger.getChild("AbbrFinder"))
		
		# db_manager
		self.db_manager = DBManager(db = self._db, logger = self._logger.getChild("DBManager"))
		self._logger.debug("init_all: complete")
		pass
	
	
	def load_all(self):
		# group
		self.group_manager.load_all()
		
		# abbr
		self.abbr_manager.load_all()
		
		# notanabbr
		
		self._logger.info("load_all: all loaded")
	
	
	def import_from_csv_db(self, filename):
		COMMENT_FOR_IMPORTED = f"Imported from file {filename}"
		self._logger.debug(f"import_from_csv_db: starting with filename {filename}")
		db_importer = DBImporter(logger = self._logger.getChild("DBImporter"))
		db_importer.load_db_from_file(filename)
		for a, d in db_importer.new_abbr_dict.items():
			self._logger.debug(f"import_from_csv_db: importing item {a}, {d}")
			if self.abbr_manager.already_exist(a, d[0]):
				self._logger.info(f"import_from_csv_db: will not add abbr {a} and descr {d[0]}. Reason: already exist.")
				continue
			else:
				self._logger.debug(f"import_from_csv_db: will add abbr {a} and descr {d[0]}.")
				self.abbr_manager.create(name = a, descr = d[0], comment = COMMENT_FOR_IMPORTED)



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
		
		# initialize
		self.check_upload_dir()
		self.init_main_app()
	
	
	def init_main_app(self):
		db = DBQueryExecutor(db_file = self.DB_FILE)
		self._logger.debug("init_main_app: will init main app...")
		self.main_app = AbbrHelperApp(db = db, logger = self._logger.getChild("main_app"))
		self.main_app.load_all()
		self._logger.debug("init_main_app: complete")
		
	
	def check_upload_dir(self):
		if not os.path.isdir(self.UPLOAD_DIR):
			os.makedirs(self.UPLOAD_DIR)
			self._logger.info(f"check_upload_dir: UPLOAD_DIR created because it was absent: {self.UPLOAD_DIR}")
		
	
	def run_web_interface(self):
		self._logger.info(f"==== STARTING AbbrHelper v{__version__} ====")
		
		self.web_app = Flask(__name__)
		self.web_app.secret_key = "qwxnmkqempemjabefwbdirbvdfcwkh"
		self.web_app.config["UPLOAD_FOLDER"] = self.UPLOAD_DIR
		self.web_app.config["MAX_CONTENT_LENGTH"] = self.MAX_FILE_SIZE
		
		
		def create_edit_abbr_from_request(abbr = None):
			"""
			arguments: abbr: if it's None then it is create mode, otherwise edit mode"""
			try:
				abbr_name = request.form["abbreviation"]
				descr = request.form["description"]
				comment = request.form["comment"]
				disabled = True if request.form.get("disabled") is not None else False
				group_name_list = request.form["group_list"]
				groups = []
				for _id, g in self.main_app.group_manager.dict.items():
					if request.form.get(f"group_{_id}") is not None:
						groups.append(g)
				self._logger.debug(f"create_edit_abbr_from_request: got groups: {groups}")
			except Exception as e:
				self._logger.error("create_edit_abbr_from_request: error: " + str(e) + ", traceback: " + traceback.format_exc())
			if len(abbr_name) < 2:
				self._logger.info(f"create_edit_abbr_from_request: did not added abbr. Reason: abbr {abbr_name} did not passed the check, too short")
			elif len(descr) < 3:
				self._logger.info(f"create_edit_abbr_from_request: did not added abbr. Reason: description {descr} did not passed the check, too short")
			else:
				if abbr is None: # create mode
					new_abbr = self.main_app.abbr_manager.create(name = abbr_name, descr = descr, comment = comment, disabled = disabled, groups = groups)	
					return new_abbr
				else: # edit mode
					abbr.name = abbr_name
					abbr.descr = descr
					abbr.comment = comment
					abbr.disabled = disabled
					abbr.groups = groups
					self.main_app.abbr_manager.save(abbr)
		
		
		def create_edit_group_from_request(group = None):
			name = request.form["name"]
			comment = request.form["comment"]
			disabled = True if request.form.get("disabled") is not None else False
			abbrs = []
			for _id, a in self.main_app.abbr_manager.dict.items():
				if request.form.get(f"abbr_{_id}") is not None:
					abbrs.append(a)
			self._logger.debug(f"create_edit_group_from_request: got abbrs {abbrs} for group {group}")
			if group is None:
				new_group = self.main_app.group_manager.create(name = name, comment = comment, disabled = disabled)
				for a in abbrs:
					if new_group not in a.groups:
						a.groups.append(new_group)
						self.main_app.abbr_manager.save(a)
				return new_group
			else:
				group.name = name
				group.comment = comment
				group.disabled = disabled
				self.main_app.group_manager.save(group)
			self._logger.debug(f"create_edit_group_from_request: complete")
		
		
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
				
				return render_template("show_result.html", found_abbrs = self.main_app.abbr_finder.all_found_abbrs, report = report.html)
		
		
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
					full_path_to_file = os.path.join(self.web_app.config["UPLOAD_FOLDER"], filename)
					f.save(full_path_to_file) # currently only with temp file
					self._logger.info(f"upload_db_file: uploaded file {full_path_to_file}")
					
					# read input file
					self.main_app.import_from_csv_db(full_path_to_file)
					
					# finally delete temp file
					os.remove(full_path_to_file)
				
				return render_template("blank.html", page_text = f"Abbrs imported from file {filename}.")
		
		
		@self.web_app.route("/show-db", methods = ["GET"])
		def show_db():
			if request.method == "GET":
				return render_template("show_db.html", db = self.main_app.db_manager.abbr_db_as_list)
		
		# ok
		@self.web_app.route("/create-abbr", methods = ["GET", "POST"])
		def create_abbr():
			if request.method == "GET":
				return render_template("create_edit_abbr.html", abbr = {}, all_groups = self.main_app.group_manager.dict.values())
			if request.method == "POST":
				new_abbr = create_edit_abbr_from_request()
				# return render_template("create_edit_abbr.html", abbr = new_abbr, all_groups = self.main_app.group_manager.dict.values())
				return redirect(f"/edit-abbr/{new_abbr}")
		
		
		@self.web_app.route("/edit-abbr/<int:abbr_id>", methods = ["GET", "POST"])
		def edit_abbr(abbr_id):
			abbr = self.main_app.abbr_manager.get_abbr_by_id(abbr_id)
			if abbr is None:
				return render_template("blank.html", page_text = f"<br>ERRROR: abbr with id {abbr_id} not found!")
			if request.method == "GET":
				return render_template("create_edit_abbr.html", abbr = abbr, all_groups = self.main_app.group_manager.dict.values())
			if request.method == "POST":
				self._logger.debug("edit_abbr: will edit abbr " + str(abbr_id))
				create_edit_abbr_from_request(abbr = abbr)
				self._logger.debug("returning page create_edit_abbr.html")
				return render_template("create_edit_abbr.html", abbr = abbr, all_groups = self.main_app.group_manager.dict.values())
		
		
		# ok
		@self.web_app.route("/delete-abbr/<int:abbr_id>", methods = ["GET", "POST"])
		def delete_abbr(abbr_id):
			found_abbr = self.main_app.abbr_manager.get_abbr_by_id(abbr_id)
			if request.method == "GET":
				return render_template("delete_abbr.html", abbr = found_abbr)
			if request.method == "POST":
				self.main_app.abbr_manager.delete(found_abbr)
				return render_template("main_page.html")
		
		# ok
		@self.web_app.route("/show-all-abbrs", methods = ["GET"])
		def show_all_abbrs():
			# self._logger.debug(f"show_all_abbrs: will display self.main_app.abbr_manager.dict: {self.main_app.abbr_manager.dict}")
			return render_template("show_all_abbrs.html", abbrs = self.main_app.abbr_manager.dict)
	
		# ok
		@self.web_app.route("/show-all-groups", methods = ["GET"])
		def show_all_groups():
			# self._logger.debug(f"show_all_groups: will display self.main_app.group_manager.dict")
			return render_template("show_all_groups.html", groups = self.main_app.group_manager.dict)
		
		
		@self.web_app.route("/edit-group/<int:group_id>", methods = ["GET", "POST"])
		def edit_group(group_id):
			found_group = self.main_app.group_manager.get_group_by_id(group_id)
			if found_group is None:
				return render_template("blank.html", page_text = f"<br>ERRROR: group with id {group_id} not found!")
			if request.method == "GET":
				return render_template("create_edit_group.html", group = found_group, all_abbrs = self.main_app.abbr_manager.dict.values())
			if request.method == "POST":
				create_edit_group_from_request(group = found_group)
				return render_template("create_edit_group.html", group = found_group, all_abbrs = self.main_app.abbr_manager.dict.values())
		
		
		@self.web_app.route("/create-group", methods = ["GET", "POST"])
		def create_group():
			if request.method == "GET":
				return render_template("create_edit_group.html", group = None, all_abbrs = self.main_app.abbr_manager.dict.values())
			if request.method == "POST":
				self._logger.debug("create_group: got POST, will create group according to form")
				new_group = create_edit_group_from_request(group = None)
				return redirect(f"/edit-group/{new_group._id}")
				# return render_template("create_edit_group.html", group = new_group, all_abbrs = self.main_app.abbr_manager.dict.values())
		
		
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
	print(f"    {os.path.abspath(__file__)}: Manage abbreviations in web interface.")
	print("    Web interface will be launced on all network interfaces.")
	print("    Use --db-file to specify DB file.")


if __name__ == "__main__":
	args = sys.argv[1:]
	
	if "--db-file" in args:
		DB_FILE == args[args.index("--db-file") + 1]
	else:
		DB_FILE = db_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), "abbr_helper.db")
	
	
	
	
	ahwapp = AbbrHelperWebApp(db_file = DB_FILE)
	ahwapp.run_web_interface()
	sys.exit(0)
