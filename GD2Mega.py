import subprocess as sp
import os
import sys
import re
from math import ceil
from pprint import pprint
from collections import defaultdict as Dict

from Database import DB


class Mega:
	def __init__(self, data_folder='', copy_folder='', email='', password=''):
		self.main_folder = data_folder.split('/')[-1]
		if data_folder:
			print('\n\n' 'Uploading Folder ', self.main_folder)
		self.folder = data_folder
		self.copy_folder = copy_folder+'/'+self.main_folder
		self.email = email
		self.password = password
		self.accounts_file = 'mega_accounts.txt'
		self.db = DB(self.email, self.password, 'accounts.db')
		self.dirs = []
		self.files = []
		self.folds_index_20gb = []
		self.folds_groups = []
		self.groups = []

	def start(self, register=False, show_size=True):
		if register:
			self.register_verify(self.email)

		self.create_dirs()

		if show_size:
			self.get_size(self.folder)

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
		new_dir = self.to_mega_path(dir.replace(self.folder, self.copy_folder))
		output = os.system(cmd + ' ' + new_dir)
		
	def create_parent_dirs(self):
		new_path = ''
		for part in self.copy_folder.split('/'):
			new_path =  os.path.join(new_path, part)
			try:
				self.create_dir(new_path)
			except Exception as e:
				print(e)

	def to_mega_path(self, path):
		return '"/Root/'+path.replace(self.folder, self.copy_folder) + '"'

	def upload_file(self, path):
		cmd = f'megaput -u {self.email} -p {self.password}'
		new_path = self.to_mega_path(path.replace(self.folder, self.folder.split('/')[-1]))
		print("Upload : " + new_path)
		# print(cmd + ' --path ' + new_path + ' "' + path + '"') 
		os.system(cmd + ' --path ' + new_path + ' "' + path + '"') 

	def knapSack(self, sizes_list, W, n):
		sizes = [int(ceil(i*10)) for i in sizes_list]
		W = W*10

		K = [[0 for w in range(W + 1)] for i in range(n + 1)]
				
		for i in range(n + 1):
			for w in range(W + 1):
				if i == 0 or w == 0:
					K[i][w] = 0
				elif sizes[i - 1] <= w:
					K[i][w] = max(sizes[i - 1]
					+ K[i - 1][w - sizes[i - 1]],
								K[i - 1][w])
				else:
					K[i][w] = K[i - 1][w]

		res = K[n][W]
		copy_res = res
		w = W		

		for i in range(n, 0, -1):
			if res <= 0:
				break
			if res == K[i - 1][w]:
				continue
			else:
				self.folds_index_20gb.append(i-1)
				res = res - sizes[i - 1]
				w = w - sizes[i - 1]
		return copy_res/10

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
	
	def get_size(self, folder=None):
		if folder == None:
			folder = self.folder
		return self.readable_size(self.folder_size(folder))

	def find_folders_lte(self, folds, size=20, sizes=None):
		if sizes is None:
			sizes = [self.size_in_gb(fold) for fold in folds]

		self.folds_index_20gb = []

		total_size = self.knapSack(sizes, size, len(folds))
		local_group = [total_size]
		
		for i in self.folds_index_20gb:
			local_group.append(folds[i])
			folds.pop(i)
			sizes.pop(i)
		self.folds_groups.append(local_group)

		if folds:
			if not self.all_size_zeros(sizes):
				# self.find_folders_lte(folds, size, sizes)
				# print(folds, sizes)
				pass
			else:
				folds.insert(0, 0)
				self.folds_groups.append(folds)
		self.groups = self.final_grouping(self.folds_groups)
		return self.groups

	@staticmethod
	def final_grouping(groups):
		final_groups = []
		local_group = []
		cur_size = 0

		for item in groups:
			cur_size += item[0]
			if cur_size  >= 18 and cur_size <= 20:
				local_group.extend(item[1:])
				cur_size = 0
			else:
				local_group.extend(item[1:])
			if cur_size == 0:
				final_groups.append(local_group)
				local_group = []
		final_groups.append(local_group)

		return final_groups

	@staticmethod
	def all_size_zeros(sizes):
		return all([1 if i == 0 else 0 for i in sizes])

	@staticmethod
	def size_in_gb(fold):
		byts = Mega.folder_size(fold)
		return round(byts/pow(1024, 3), 2)

	@staticmethod
	def size_in_mb(fold):
		byts = Mega.folder_size(fold)
		return round(byts/pow(1024, 2), 2)

	@staticmethod
	def folder_size(folder):
		size = 0
		if os.path.isfile(folder):
			return os.stat(folder).st_size
		for root, dirs, files in os.walk(folder):
			for file in files:
				size += os.stat(root+'/'+file).st_size
		return size


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
	accounts = []

	while 1:
		fold = input("Enter folder path : ")
		if fold == '':
			break
		folds.append(fold)

	while 1:
		user = input("Enter username : ")
		if user == '':
			break
		accounts.append(user)

	mega = Mega()
	groups = mega.find_folders_lte(folds, 20)

	mega_path = input("Mega path to put folder : ")
	password = input("Enter Password : ")
	register = True if input("Wanna register first[y|n] : ") == 'y' else False;

	mega.find_folders_lte(folds, 20)

	print('\n\n' 'Grouping')
	print(mega.folds_groups)

	for group, email in zip(mega.groups, accounts):
		if group:
			print(email, group)
			upload(group, mega_path, email, password, register)
		print()
