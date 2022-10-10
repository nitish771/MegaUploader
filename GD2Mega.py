class Mega:
	def __init__(self, data_folder, copy_folder, email, password="97055@yOu"):
		print("Uploading " + data_folder.split('/')[-1])
		self.folder = data_folder
		self.copy_folder = copy_folder+'/'+data_folder.split('/')[-1]
		self.email = email
		self.password = password
		self.accounts_file = 'mega_accounts.txt'
		self.dirs = []
		self.files = []

	def start(self, register=False, show_size=True):
		if register:
			self.register_verify()

		self.create_dirs()

		if show_size:
			self.folder_size(self.folder)

		if not show_size:
			self.get_remote_content(self.folder)

		## Upload files
		for file in self.files:
			self.upload_file(file)		

	def save_account(self, username, pass_, file="mega_accounts.txt"):
		with open(file, 'a+') as f:
			f.write(username+":"+pass_+'\n')

	def register_verify(self):
		# Register
		try:
			print("Trying to register " + self.email)
			cmd = 'megareg --register -n nitish -e ' + self.email + ' -p ' + self.password
			output = sp.check_output(cmd.split(' '))
			print("registration link sent to " + self.email)
		except:
			print("Error. Email maybe already registered : " + self.email)

		# Verify
		try:
			link = input("Enter link : ")
			verify_cmd = re.search('megareg --verify [\S]* ', str(output)).group(0) + link
			result = sp.check_output(verify_cmd.split(' '))
			print(str(result))
		except:
			print("Error. Check link again : " + link)
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

	def get_size(self, folder=None):
		if folder:
			self.get_remote_content(folder)
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
		output = sp.check_output(cmd.split(' ') + ['/Root/'+dir])
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
		print("Upload : " + path.replace(self.folder, self.folder.split('/')[-1]))

		#### Uncomment it 
		os.system(cmd + ' --path ' + self.to_mega_path(path) + ' "' + path + '"') 
		# print(cmd + ' --path ' + self.to_mega_path(path) + ' "' + path + '"') 


if __name__ == '__main__':
	drive_folder = input("Enter Drive path to upload to Mega : ")
	mega_path = input("Mega path to put folder : ")
	email = input("Enter Email : ")
	password = input("Enter Password : ")
	register = input("Want to register first[y|n] : ")
	register = True if register == 'y' else False

	mega = Mega(drive_folder, mega_path, email, password)
	mega.start(register=register)
