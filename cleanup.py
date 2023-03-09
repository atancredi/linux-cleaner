import subprocess
import getpass

class DiskInfo:
	filesystem:str
	size:str
	used:str
	avail:str
	percent_used:int
	mounted_on:str

	def __init__(self,raw_disk_data):
		self.filesystem = raw_disk_data[0]
		
		if 'G' in raw_disk_data[1]:
			self.size = 1024 * int(raw_disk_data[1].replace('G',''))
		if 'B' in raw_disk_data[1]:
			self.size = int(raw_disk_data[1].replace('B','')) / 1024
		
		if 'G' in raw_disk_data[1]:
			self.used = 1024 * int(raw_disk_data[2].replace('G',''))
		if 'B' in raw_disk_data[1]:
			self.used = int(raw_disk_data[2].replace('B','')) / 1024
		
		if 'G' in raw_disk_data[3]:
			self.avail = 1024 * int(raw_disk_data[2].replace('G',''))
		if 'B' in raw_disk_data[3]:
			self.avail = int(raw_disk_data[2].replace('B','')) / 1024
		
		self.percent_used = int(raw_disk_data[4].replace('%',''))
		self.mounted_on = raw_disk_data[5].replace('\n','')

# Run cmd
def run_cmd(cmd, sudo = False, sudo_pwd = ""):
	if sudo or sudo_pwd != "":
		if sudo_pwd == "":
			sudo_pwd = getpass.getpass('password:')
		ss = subprocess.Popen(['echo',sudo_pwd], stdout=subprocess.PIPE)
		result = subprocess.Popen(['sudo','-S'] + cmd, stdin=ss.stdout, stdout=subprocess.PIPE)
	else:
		result = subprocess.Popen(cmd, stdout=subprocess.PIPE)
	while True:
		line = result.stdout.readline().decode("utf-8")
		print(line)
		if not line: break
	return sudo_pwd

# Get remaining space
def get_available_space():
	ps = subprocess.Popen(["df","-h"], stdout=subprocess.PIPE)
	result = subprocess.check_output(['grep','-w','/'], stdin=ps.stdout)
	ps.wait()
	raw_disk_data = [i for i in result.decode("utf-8").split(' ') if i != '']
	disk_data = DiskInfo(raw_disk_data)
	return disk_data

def snap_cleanup(sudopwd):
	ps = subprocess.Popen(["snap","list"], stdout=subprocess.PIPE)
	result = subprocess.check_output(['awk',"{print $1}"], stdin=ps.stdout)
	ps.wait()
	pkgs = result.decode("utf-8").splitlines()[1:]
	for p in pkgs:
		run_cmd(["pkill", p],sudo_pwd=sudopwd)
	run_cmd(["./snap-cleaner.sh"],sudo_pwd=sudopwd)

# Execute cleanup
def cleanup():
	print()
	
	# APT Autoremove
	pwd = run_cmd(['apt-get','autoremove','-y'],True)
	
	# APT Cache Autoclean
	run_cmd(['apt-get','autoclean','-y'],sudo_pwd=pwd)
	
	# APT Cache clean
	# sudo du -sh /var/cache/apt 
	run_cmd(['apt-get','clean','-y'],sudo_pwd=pwd)
	
	# Clear systemd journal logs
	# journalctl --disk-usage
	run_cmd(['journalctl','--vacuum-time=3d'],sudo_pwd=pwd)
	
	# Remove older versions of Snap applications 
	# du -h /var/lib/snapd/snaps
	snap_cleanup(pwd)

	# clean thumbnail cache
	# du -sh ~/.cache/thumbnails
	run_cmd(['rm','-rf','.cache/thumbnails'],sudo_pwd=pwd)
	
	# Flatpak cleanup
	run_cmd(['flatpak', 'uninstall', '--unused', '--delete-data', '-y'])
	
if __name__ == '__main__':
	data_pre = get_available_space()
	print(data_pre.__dict__)
	cleanup()
	data_post = get_available_space()
	print(data_post.__dict__)
	cleaned2 = data_pre.used - data_post.used
	
	print('Freed space: ', cleaned2)
