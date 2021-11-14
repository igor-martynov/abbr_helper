import sqlite3



def empty_on_None(ivar):
	return ivar if ivar is not None else ""


def empty_filter(ivar):
	"""return empty str if ivar is None or [] or {}"""
	return ivar if (ivar is not None and len(ivar) != 0) else ""


def is_abbr(word):
	"""return True if word is abbr, False otherwise"""
	# more then 2 chars in word are uppercase 
	num_of_uppers = sum(map(str.isupper, word))
	num_of_lowers = sum(map(str.islower, word))
	if num_of_uppers >= 2 and (num_of_uppers / len(word) >= 0.5):
		return True


def normalize_abbr(abbr_str):
	if abbr_str.startswith(" "):
		abbr_str = abbr_str[1:]
	if abbr_str.endswith(" "):
		abbr_str = abbr_str[:-1]
	return abbr_str
	

class MetaSingleton(type):
	"""metaclass that creates Singleton class"""
	
	_instances = {}
	
	def __call__(cls, *args, **kwargs):
		if cls not in cls._instances:
			cls._instances[cls] = super(MetaSingleton, cls).__call__(*args, **kwargs)
		return cls._instances[cls]
		


class DBQueryExecutor(object, metaclass = MetaSingleton):
	"""provides db query functions"""
	
	def __init__(self, db_file = ""):
		super(DBQueryExecutor, self).__init__()
		
		self.DB_FILE = db_file
		self.create_new_db()
		self.cursor_last_row_id = None
		self.lastrowid = None
	
	
	def create_new_db(self):
		"""create schema for new db.
		if some tables dont exist, they will be created.
		if table exist, it will not be updated"""
		
		self.execute_db_query("""CREATE TABLE IF NOT EXISTS abbrs(id INTEGER PRIMARY KEY AUTOINCREMENT,
			name TEXT,
			descr TEXT,
			comment TEXT,
			disabled INTEGER default 0)""")
		
		self.execute_db_query("""CREATE TABLE IF NOT EXISTS groups(id INTEGER PRIMARY KEY AUTOINCREMENT,
			name TEXT,
			comment TEXT,
			disabled INTEGER  default 0)""")
		
		self.execute_db_query("""CREATE TABLE IF NOT EXISTS abbr_group(id INTEGER PRIMARY KEY AUTOINCREMENT,
			abbr_id INTEGER,
			group_id INTEGER)""")
		
		self.execute_db_query("""CREATE TABLE IF NOT EXISTS not_an_abbrs(id INTEGER PRIMARY KEY AUTOINCREMENT,
			name TEXT,
			comment TEXT,
			disabled INTEGER default 0)""")
		
		self.execute_db_query("""CREATE TABLE IF NOT EXISTS not_an_abbr_group(id INTEGER PRIMARY KEY AUTOINCREMENT,
			not_an_abbr_id INTEGER,
			group_id INTEGER)""")
	
	
	def execute_db_query(self, query, *argv):
		"""execute DB query. DB connection will be created, query executed, then DB connection is destroyed.
		
		arguments: same as in sqlite.cursor.execute()
				query: string of query
				argv[0] - dictionary of arguments
				other args are ignored
				
		returns: list of rows, exactly as sqlite3.connection.cursor().execute().fetchall()"""
		if self.DB_FILE == "":
			return None
		
		db_conn = sqlite3.connect(self.DB_FILE, detect_types = sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
		with db_conn:
			if len(argv) > 0:
				cursor = db_conn.execute(query, argv[0])
			else:
				cursor = db_conn.execute(query)
			
			result = cursor.fetchall()
		self.lastrowid = cursor.lastrowid
		db_conn.commit()
		db_conn.close()
		return result



class BaseDAO(object):
	"""Base class of all DAOs"""
	def __init__(self, db = None, logger = None, factory = None):
		super(BaseDAO, self).__init__()
		self._db = db
		self._logger = logger
		self._factory = factory
		self.dict = {}
	
	
	def create(self, obj):
		raise NotImplemented
	
	def read(self, _id):
		raise NotImplemented
	
	def update(self, obj):
		raise NotImplemented
	
	def delete(self, obj):
		raise NotImplemented



class BaseFactory(object):
	"""Base class of all factories"""
	def __init__(self):
		super(BaseFactory, self).__init__()
		
		pass
	
	
	def create(self):
		raise NotImplemented
	
	
	def create_from_db_row(self):
		raise NotImplemented
	


class BaseManager(object):
	"""docstring for BaseManager"""
	def __init__(self, db = None, logger = None):
		super(BaseManager, self).__init__()
		self.dict = {}
		self._db = db
		self._DAO = None
		self._factory = None
		self._logger = logger
	
	
	def save(self):
		raise NotImplemented
	
	
	def delete(self):
		raise NotImplemented
		
	
	def create(self):
		raise NotImplemented
	
	
