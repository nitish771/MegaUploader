import subprocess as sp
import os
import sys
import re

from Database import DB


class Mega:
	def __init__(self, data_folder, copy_folder, email, password):
		self.main_folder = data_folder.split('/')[-1]
		print(self.main_folder, '\n')
		self.folder = data_folder
		self.copy_folder = copy_folder+'/'+self.main_folder
		self.email = email
		self.password = password
		self.accounts_file = 'mega_accounts.txt'
		self.db = DB(self.email, self.password, 'accounts.db')
		self.dirs = []
		self.files = []

	def start(self, register=False, show_size=True):
		if register:
			self.register_verify(self.email)

		self.create_dirs()

		if show_size:
			self.folder_size(self.folder)

		## Upload files
		if not show_size:
			self.get_remote_content(self.folder)

		for file in self.files:
			self.upload_file(file)	

		# write in db
		self.to_db(self.main_folder)
		self.db.delete_dup()

	def save_account(self, username, pass_, file="mega_accounts.txt"):
		with open(file, 'a+') as f:
			f.write(username+":"+pass_+'\n')

	def register_verify(self):
		# Register
		try:
			cmd = 'megareg --register -n nitish -e ' + self.email + ' -p ' + self.password
			output = sp.check_output(cmd.split(' '))
			print("registration email sent to " + self.email)
		except:
			print("Error while registrating email " + self.email)

		# Verify
		try:
			link = input("Enter link : ")
			verify_cmd = re.search('megareg --verify [\S]* ', str(output)).group(0) + link
			result = sp.check_output(verify_cmd.split(' '))
			print(str(result))
		except:
			print("Error while verifying link " + link)
		self.save_account(self.email, self.password)

	def readable_size(self, size):
		size /= 1024
		if size < 1024:
			return f'{size:.2f} KB'
		size /= 1024
		if size < 1024:
			return f'{size:.2f} MB'
		size /= 1024
		return f'{size:.2f} GB'

	def folder_size(self, folder):
		size = 0
		if os.path.isfile(folder):
			return os.stat(folder).st_size
		for root, dirs, files in os.walk(folder):
			for file in files:
				# print(root, file)
				size += os.stat(root+'/'+file).st_size
		return size

	def get_size(self, folder):
		# self.get_remote_content(folder)
		return self.readable_size(self.folder_size(folder))

	def get_remote_content(self, folder):
		for root, dirs, files in os.walk(folder):
			for file in files:
				self.files.append(root+'/'+file)
				# print(file)
			for dir_ in dirs:
				self.dirs.append(root+'/'+dir_)

	def create_dirs(self):
		self.create_parent_dirs()
		self.get_remote_content(self.folder)
		for fold in self.dirs:
			self.create_dir(fold)

	def create_dir(self, dir):
		cmd = 'megamkdir -u ' + self.email + ' -p ' + self.password

		#### Uncomment it 
		new_dir = self.to_mega_path(dir.replace(self.folder, self.copy_folder))
		output = os.system(cmd + ' ' + new_dir)
		print("Created " + self.to_mega_path(dir))

	def create_parent_dirs(self):
		new_path = ''
		for part in self.copy_folder.split('/'):
			new_path =  os.path.join(new_path, part)
			try:
				self.create_dir(new_path)
				print('Creating parent path', new_path)
			except Exception as e:
				print(e)

	def to_mega_path(self, path):
		return '"/Root/'+path.replace(self.folder, self.copy_folder) + '"'

	def upload_file(self, path):
		cmd = f'megaput -u {self.email} -p {self.password}'
		new_path = self.to_mega_path(path.replace(self.folder, self.folder.split('/')[-1]))
		print("Upload : " + new_path)

		#### Uncomment it 
		os.system(cmd + ' --path ' + self.to_mega_path(path) + ' "' + path + '"') 
		# print(cmd + ' --path ' + self.to_mega_path(path) + ' "' + path + '"') 

	def find_folders_lte_20gb(self):
		# https://www.codingninjas.com/codestudio/library/count-number-of-subarrays-with-sum-k
		pass

	def account_details(self, email=None, password=None):
		if email is None:
			email = self.email
		if password is None:
			password = self.password
		
		cmd = f'megadf -u {email} -p {password}'
		output = str(sp.check_output(cmd.split(' ')))
		total = int(re.search('Total:\s*(\d+)', output).group(1))
		used = int(re.search('Used:\s*(\d+)', output).group(1))
		free = int(re.search('Free:\s*(\d+)', output).group(1))
		output = email + " -> Total : " + self.readable_size(total) + \
					" | Used  : " + self.readable_size(used) + \
					" | Free  : " + self.readable_size(free)
		print(output)

	def check_all_accounts_details(self, accounts=None, account_file=None):
		if accounts:
			for email, password in accounts.items():
				self.account_details(email, password)

		if account_file:
			with open(account_file, 'r') as f:
				for line in f.readlines():
					email, password = line.split(":")
					self.account_details(email, password.strip())

	def to_db(self, content):
		try:
			self.db.create()
		except:
			pass
		self.db.insert(content)
	


def upload(folds, mega_folder, email, password, first=False):
    for folder in folds:
        mega = Mega(folder, mega_folder, email, password)
        print(mega.get_size(folder), '\n')

        if first:
          mega.register_verify()
          first = False
        mega.start()


if __name__ == '__main__':
	folds = []

	while 1:
		fold = input("Enter folder path[empty to get out] : ")
		if fold == '':
			break
		folds.append(fold)

	mega_path = input("Mega path to put folder[empty to root] : ")
	email = input("Enter Email : ")
	password = input("Enter Password : ")
	register = True if input("Wanna register first[y|n] : ") == 'y' else False;

	upload(folds, mega_path, email, password, register)
