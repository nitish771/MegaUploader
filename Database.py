import sqlite3 as sql



class DB:
	def __init__(self, username, password, db_name="accounts.db"):
		self.con = sql.connect(db_name)
		self.cur = self.con.cursor()
		self.username = username
		self.password = password

	def commit(self):
		self.con.commit()

	def create(self, *fields):
		cmd = "CREATE TABLE Content(username, password, content)"
		self.cur.execute(cmd)
		for field in fields:
			print(field)
		self.commit()

	def insert(self, *contents):
		cmd = f'INSERT INTO Content VALUES '
		for content in contents[:-1]:
			cmd += f'("{self.username}", "{self.password}", "{content}"), '
		cmd += f'("{self.username}", "{self.password}", "{contents[-1]}") '
		# print(cmd)
		self.cur.execute(cmd)
		self.commit()

	def get(self):
		cmd = "SELECT * FROM Content"
		return self.cur.execute(cmd).fetchall()

	def reset(self):
		self.cur.execute('drop table Content')
		self.create()
		self.commit()

	def delete_dup(self):
		cmd = '''delete from Content where rowid not in
         		( select  min(rowid) from Content group by username, content)
				 '''
		self.cur.execute(cmd)
		self.commit()

	def schema(self):
		cmd = "pragma table_info(Content)"
		return self.cur.execute(cmd).fetchall()
