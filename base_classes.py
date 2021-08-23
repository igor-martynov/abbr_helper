import sqlite3



def empty_on_None(ivar):
	return ivar if ivar is not None else ""


def is_abbr(word):
	""""""
	
	# more then 2 chars in word are uppercase 
	num_of_uppers = sum(map(str.isupper, word))
	num_of_lowers = sum(map(str.islower, word))
	# max_cons_uppers = 
	
	if num_of_uppers >= 2 and (num_of_uppers / len(word) >= 0.5):
		return True


class MetaSingleton(type):
	"""metaclass that creates Singleton class"""
	
	_instances = {}
	
	def __call__(cls, *args, **kwargs):
		if cls not in cls._instances:
			cls._instances[cls] = super(MetaSingleton, cls).__call__(*args, **kwargs)
			# print("D new instance of class created - " + str(cls._instances[cls]))
			# print("D total instances:")
			# for i in cls._instances:
			# 	print("  -  " + str(i))
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
		if table exist, it will not be updated
		"""
		
		self.execute_db_query("""CREATE TABLE IF NOT EXISTS abbrs(id INTEGER PRIMARY KEY AUTOINCREMENT,
			name TEXT,
			descr TEXT,
			group_id INTEGER,
			comment TEXT,
			disabled INTEGER default 0)""")
		
		self.execute_db_query("""CREATE TABLE IF NOT EXISTS groups(id INTEGER PRIMARY KEY AUTOINCREMENT,
			name TEXT,
			comment TEXT,
			disabled INTEGER  default 0)""")
		
		self.execute_db_query("""CREATE TABLE IF NOT EXISTS not_an_abbr(id INTEGER PRIMARY KEY AUTOINCREMENT,
			name TEXT,
			comment TEXT,
			disabled INTEGER default 0)""")
		
	
	def execute_db_query(self, query, *argv):
		"""execute DB query. DB connection will be created, query executed, then DB connection is destroyed.
		
		arguments: same as in sqlite.cursor.execute()
				query: string of query
				argv[0] - dictionary of arguments
				other args are ignored
				
		returns: list of rows, exactly as sqlite3.connection.cursor().execute().fetchall()
		"""
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



# TODO: uncertain if this needed
class Abbreviation(object):
	"""docstring for Abbreviation"""
	def __init__(self):
		super(Abbreviation, self).__init__()
		
		pass
		