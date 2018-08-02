# -*- coding: utf-8 -*-

from __future__ import print_function
from distutils import dir_util
import os, sys, platform, shutil, re, datetime, logging, tempfile, inspect, json, codecs

try:
	from PyQt5.QtCore import *
	from PyQt5.QtGui import *
	from PyQt5.QtWidgets import *
except ImportError:
	from tentaculo.Qt.QtGui import *
	from tentaculo.Qt.QtCore import *
	from tentaculo.Qt.QtWidgets import *

FCONFIG = 'tentaculo_install'

INST_STANDALONE = True
INST_NETWORK = False
SETUP_NETWORK = False

PLUGIN_EVAR = "CTENTACULO_LOCATION"

try:
	import cerebro
	INST_STANDALONE = False
except ImportError:
	pass

try:
	import net_install
	INST_NETWORK = True
except ImportError:
	pass

from ctentaculo.tentaculo import version

HOST_OS = platform.system().lower()

def home_dir():
	home = os.path.expanduser('~')
	if home is None or not os.path.exists(home):
		raise IOException("HOME directory does not exist: {0}".format(home))

	return home

def appdata_dir():
	appdata = None

	if HOST_OS == "windows":
		appdata = os.environ.get("APPDATA", None)
	elif HOST_OS == "linux" or HOST_OS == "darwin":
		appdata = home_dir()

	if appdata is None or not os.path.exists(appdata):
		raise IOException("APPDATA directory does not exist: {0}".format(appdata))

	return appdata

def config_dir():
	appdata = appdata_dir()

	folder = "cerebro"
	if HOST_OS == "linux":
		folder = ".cerebro"

	return os.path.normcase(os.path.join(appdata, folder))

def temp_dir():
	tmp = tempfile.gettempdir()
	tmp_cerebro = os.path.normpath(os.path.join(tmp, "tempCerebro"))
	return tmp_cerebro

def install_dir(path = None):
	global INST_NETWORK
	global PLUGIN_EVAR
	# getattr(net_install, PLUGIN_EVAR)
	if path is None:
		path = os.path.dirname(os.path.realpath(__file__)) if INST_NETWORK else config_dir()

	tail = os.path.split(os.path.dirname(os.path.realpath(__file__)))[-1]
	if not path.endswith(tail):
		path = os.path.join(path, tail)
	return os.path.normcase(path)
	
def source_dir():
	return os.path.dirname(os.path.realpath(__file__))

def cerebro_message(message):
	if message is None: return
	global INST_STANDALONE
	if INST_STANDALONE is False:
		cerebro.gui.information_box("Cerebro Tentaculo",  message)
	else:
		print(message)

# TODO: remove json?
def getConfigFile(jfile = None):
	result = None
	if jfile is None: return result
	jsondir = config_dir()	
	jsonfile = os.path.join(jsondir, jfile)
	ext = '.json'
	if not jsonfile.endswith(ext): jsonfile += ext
	return jsonfile

def jsonread(jfile = None):
	result = None
	jsonfile = getConfigFile(jfile)
	if jsonfile is None or not os.path.exists(jsonfile):
		return result
	lines = open(jsonfile).read()
	if len(lines) < 1: return result
	result = json.loads(lines)
	return result

def jsonwrite(jfile = None, d = None):
	jsonfile = getConfigFile(jfile)
	if jsonfile is None or d is None: return False
	outtext = json.dumps(d, indent=4, sort_keys=True)
	#with open(jsonfile, 'w') as of: json.dump(d, of)
	with open(jsonfile, 'w') as of: print(outtext, end = '', file = of)
	return True

def getPrevVersion():
	data = jsonread(FCONFIG)
	if data is None: return (-1, "-1")

	return (int(data.get("version", -1)), data.get("version_str", "-1"))

def installed_path():
	path = None

	data = jsonread(FCONFIG)
	if data is not None:
		path = data.get("path", None)
		if path is not None:
			path = os.path.normpath(path)

	return path

# HOST APPS
def host_apps():
	prefs = {}

	prefs["Autodesk Maya"] = host_maya()
	prefs["Autodesk 3ds Max"] = host_max()
	prefs["Nuke"] = host_nuke()
	prefs["Houdini"] = host_houdini()
	prefs["Cinema 4D"] = host_c4d()
	prefs["Blender"] = host_blender()

	return prefs

def host_maya():
	paths = []
	lookup_path = appdata_dir()

	if HOST_OS == 'windows':
		paths = [p for p in install_paths("autodesk maya") if "maya" in p.lower()]
		lookup_path = os.path.join(lookup_path, "autodesk", "maya")
	elif HOST_OS == 'linux':
		lookup_path = os.path.join(lookup_path, "maya")
	elif HOST_OS == 'darwin':
		lookup_path = os.path.join(lookup_path, "library", "preferences", "autodesk", "maya")

	if len(paths) == 0:
		paths = find_apps(lookup_path, "20")

	return paths

def host_max():
	paths = []
	lookup_path = appdata_dir()

	if HOST_OS == 'windows':
		paths = [p for p in install_paths("autodesk 3ds max") if "max" in p.lower()]
		lookup_path = os.path.join(lookup_path, "autodesk", "3dsmax")
	elif HOST_OS == 'linux':
		lookup_path = os.path.join(lookup_path, "3dsmax")
	elif HOST_OS == 'darwin':
		lookup_path = os.path.join(lookup_path, "library", "preferences", "autodesk", "3dsmax")

	if len(paths) == 0:
		paths = find_apps(lookup_path, "20")

	return paths

def host_nuke():
	paths = []

	if HOST_OS == 'windows':
		paths = install_paths("nuke")

	if len(paths) == 0:
		paths = find_apps(home_dir(), ".nuke")

	return paths

def host_houdini():
	paths = []
	lookup_path = home_dir()
	lookup_token = "houdini"

	if HOST_OS == 'windows':
		#paths = install_paths("houdini")
		lookup_path = os.path.join(lookup_path, "documents")
	elif HOST_OS == 'linux':
		pass
	elif HOST_OS == 'darwin':
		lookup_path = os.path.join(lookup_path, "library", "preferences", "houdini")
		lookup_token = '.'

	if len(paths) == 0:
		paths = find_apps(lookup_path, lookup_token)

	return paths

def host_c4d():
	paths = []
	lookup_path = appdata_dir()

	if HOST_OS == 'windows':
		paths = install_paths("cinema 4d")
		lookup_path = os.path.join(lookup_path, "maxon")
	elif HOST_OS == 'linux':
		pass
	elif HOST_OS == 'darwin':
		lookup_path = os.path.join(lookup_path, "library", "preferences", "maxon")

	if len(paths) == 0:
		paths = find_apps(lookup_path, "cinema 4d")

	return paths

def host_blender():
	paths = []
	lookup_path = appdata_dir()

	if HOST_OS == 'windows':
		dirs = install_paths("blender")
		for p in dirs:
			folders = [os.path.join(p, d) for d in os.listdir(p) if os.path.isdir(os.path.join(p, d)) and '.' in d]
			paths.extend(folders)
		lookup_path = os.path.join(lookup_path, "blender foundation", "blender")
	elif HOST_OS == 'linux':
		pass
	elif HOST_OS == 'darwin':
		lookup_path = os.path.normpath("/Applications/Blender/blender.app/Contents/Resources")

	if len(paths) == 0:
		paths = find_apps(lookup_path, ".")

	return paths

# PATHS LOOKUP
def install_paths(appname):
	appname = appname.lower()
	app_paths = []

	if HOST_OS == 'windows':
		try:
			import winreg
		except:
			raise Exception("Failed to access Windows registry")

		base_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", 0, (winreg.KEY_WOW64_64KEY + winreg.KEY_READ))
		size = winreg.QueryInfoKey(base_key)[0]

		for i in range(size):
			name = winreg.EnumKey(base_key, i)
			app_key = winreg.OpenKey(base_key, name, 0, (winreg.KEY_WOW64_64KEY + winreg.KEY_READ))
			try:
				display_name = winreg.QueryValueEx(app_key, "DisplayName")[0]
				if appname in display_name.lower():
					try:
						path = os.path.normpath(winreg.QueryValueEx(app_key, "InstallLocation")[0])
						if not path in app_paths:
							app_paths.append(path)
					except:
						pass
			except:
				pass

	return app_paths

def find_apps(folder, token):
	app_paths = []
	if not os.path.exists(folder): return app_paths

	for f in os.listdir(folder):
		path = os.path.normpath(os.path.join(folder, f))
		if os.path.isdir(path) and token in f.lower():
			app_paths.append(os.path.normcase(path))

	return app_paths

def copy_tree(src, dst, clean = False, exclude_list = []):
	if src is None or dst is None or not os.path.isdir(src):
		raise Exception("Invalid arguments for copy_tree(): {0} : {1}".format(src, dst))
		
	try:
		if os.path.exists(dst):
			if clean:
				shutil.rmtree(dst)
				os.makedirs(dst)
		else:
			os.makedirs(dst)
	except Exception as err:
		raise Exception("Error creating folder tree: {0}".format(str(err)))
		
	for rec in os.listdir(src):
		if rec in exclude_list: continue
		
		path_src = os.path.join(src, rec)
		path_dst = os.path.join(dst, rec)
		
		try:
			shutil.copy(path_src, path_dst) if os.path.isfile(path_src) else dir_util.copy_tree(path_src, path_dst)
		except Exception as err:
			raise Exception("Error copying files: {0}".format(str(err)))

# ENVIRONMENT CLEAR
def evar_clear_win(token):
	token = os.path.normpath(token).lower()
	sep = os.path.pathsep
	vars = ["PYTHONPATH", "NUKE_PATH", "PATH", "MAYA_MODULE_PATH", "MAYA_SCRIPT_PATH", "HOUDINI_MENU_PATH"]
	for var in vars:
		path_string = ""

		try:
			import winreg
		except:
			raise Exception("Failed to access Windows registry")

		try:
			key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, (winreg.KEY_WOW64_64KEY + winreg.KEY_READ))
			path_string = winreg.QueryValueEx(key, var)[0]
			key.Close()
		except:
			pass

		if path_string is None or len(path_string) == 0: continue

		paths = [p for p in path_string.split(sep) if len(p) > 0 and not token in os.path.normpath(p).lower()]
		if len(paths) > 0:
			path_string = os.path.normpath(re.sub("[;]+", ';', sep.join(paths)))
			cmd = r'setx {0} "{1}"'.format(var, path_string)
			os.system(cmd)
		else:
			cmd = r'SETX {0} "" & REG delete HKCU\Environment /F /V {0}'.format(var)
			os.system(cmd)


class w_installer(QWidget):
	NAME = "TENTACULO_INSTALLER"
	TITLE = "Cerebro Tentaculo v{0} Installer".format(version.APP_VERSION)
	parent = None

	def __init__(self, parent = None):
		self.parent = parent
		super(self.__class__, self).__init__(parent = self.parent)
		self.setAttribute(Qt.WA_DeleteOnClose)
		self.initLogging()
		self.initStyle()
		self.initUI()
		self.initData()

	def initLogging(self):
		self.log = logging.getLogger("ctentaculo_install")
		self.log.setLevel(logging.DEBUG)

		self.logformatter = logging.Formatter("%(asctime)s: %(levelname)s,  %(funcName)s, %(message)s")

		logpath = os.path.join(temp_dir(), "ctentaculo_install.log.txt")
		self.flog = logging.FileHandler(logpath)
		self.flog.setLevel(logging.DEBUG)
		self.flog.setFormatter(self.logformatter)

		self.log.addHandler(self.flog)
		self.log.info("\n\n--=== session started ===---")

	def initStyle(self):
		#styler = style.Styler()
		#styler.initStyle(self)
		pass

	def initData(self):
		self.dir_home = home_dir()
		self.dir_source = source_dir()
		self.dir_install = install_dir()
		self.dir_cfg = config_dir()
		self.apps = host_apps()
		self.register_apps(self.apps)
		self.prevversion = getPrevVersion()
		if self.prevversion[0] > 0:
			self.lb_prev.setText(self.prevversion[1])
		self.inst_line.setText(self.dir_install)

		self.log.debug('host: ' + HOST_OS)
		self.log.debug('home: ' + self.dir_home)
		self.log.debug('config dir: ' + self.dir_cfg)
		self.log.debug('srcdir: ' + self.dir_source)
		self.log.debug('dstdir: ' + self.dir_install)
		self.log.debug('prev version: ' + self.prevversion[1])
		self.log.debug("apps:\t")
		self.log.debug(self.apps)

	# UTILITY
	def status(self, message):
		if message is None: return
		self.log.debug(message)
		self.statusbar.showMessage(message)

	def progress(self, value = 0.0):
		if value == 0.0:
			self.progressbar.reset()
		else:
			self.progressbar.setValue(value)

	def w_install_dir(self):
		global SETUP_NETWORK
		dir = QFileDialog.getExistingDirectory(self, '', self.dir_install)
		if dir is not None and len(dir) > 0:
			SETUP_NETWORK = True
			self.dir_install = install_dir(dir)
			self.inst_line.setText(self.dir_install)
		return self.dir_install

	def w_confirm_install(self, update = False):
		
		mb_confirm = QMessageBox()
		mb_confirm.setWindowTitle("{0} v{1}".format("Update Cerebro Tentaculo" if update else "Confirm installation", version.APP_VERSION))
		mb_confirm.setText("Install to: {0} ?".format(self.dir_install))

		b_install = mb_confirm.addButton("Update" if update else "Install", QMessageBox.ApplyRole)
		b_cancel = mb_confirm.addButton("Cancel", QMessageBox.RejectRole)
		mb_confirm.setDefaultButton(b_install)
		mb_confirm.setEscapeButton(b_cancel)
		
		ret = mb_confirm.exec_()
		
		return True if ret == 0 else False

	def install(self, update = False):
		global SETUP_NETWORK
		global INST_NETWORK
		global PLUGIN_EVAR
		result = False
		
		if self.w_confirm_install(update):
			try:
				self.progress()
				if INST_NETWORK:
					evar_clear_win(PLUGIN_EVAR)
				else:
					self.install_files()
				self.progress(10)
				if not SETUP_NETWORK:
					self.install_cerebro()
					self.progress(20)
					self.install_system()
					self.progress(60)
					self.install_maya()
					self.progress(70)
					self.install_max()
					self.progress(75)
					self.install_houdini()
					self.progress(80)
					self.install_nuke()
					self.progress(90)
					self.install_c4d()
					self.install_blender()

				self.progress(100)
				result = True
				self.status("Installation complete, exiting")
				cerebro_message("Installation complete!")
				self.stop()
			except Exception as err:
				cerebro_message("An error occured during installation {0}".format(str(err)))
		else:
			self.status("Installation was cancelled")

		return result

	def install_system(self):
		global PLUGIN_EVAR
		self.status("Setting base system variables")
		
		if HOST_OS == "windows":
			# Screen scale factor
			varstr = os.environ.get("QT_AUTO_SCREEN_SCALE_FACTOR", None)
			if varstr is None or varstr != "1":
				os.system('setx QT_AUTO_SCREEN_SCALE_FACTOR "1"')

			# CTENTACULO_LOCATION
			self.evar_set_win(PLUGIN_EVAR, [self.dir_install], True)
			# PYTHONPATH
			adds = [r'', r'tentaculo']
			paths = [ os.path.normpath(os.path.join("%{0}%".format(PLUGIN_EVAR), p)) for p in adds ]
			#paths = [os.path.abspath(os.path.join(self.dir_install, p)) for p in adds]
			#paths.append(os.path.abspath(os.path.join(self.dir_install, os.pardir)))

			self.evar_set_win("PYTHONPATH", paths)
		elif HOST_OS == "linux":
			self.evar_setup_linux()
		elif HOST_OS == "darwin":
			self.evar_setup_mac()

	def install_cerebro(self):
		# target dir
		if self.dir_cfg == '':
			return False
		if not os.path.exists(self.dir_cfg):
			os.makedirs(self.dir_cfg)

		files = []
		#files.append('cargador.personal.conf')
		files.append('path_config.json')
		for f in files:
			fullpath = os.path.join(self.dir_source, f)
			if os.path.isfile(fullpath):
				shutil.copy(fullpath, self.dir_cfg)
		self.status('Cerebro config files have been updated')

	def install_files(self):
		global SETUP_NETWORK
		global INST_STANDALONE
		global PLUGIN_EVAR
		result = False
		exit_host_msg = 'please exit all the host applications before install'

		if self.dir_install is None or len(self.dir_install) == 0:
			return False

		self.status("Copying files")
		try:
			exclude_list = ["__pycache__"] if SETUP_NETWORK else ["__pycache__", "libs3", "install.py", "client", "browse.py", "logon.py"]
			copy_tree(self.dir_source, self.dir_install, True, exclude_list)
			if not SETUP_NETWORK:
				copy_tree(os.path.join(self.dir_source, "libs3", "crossplatform"), os.path.join(self.dir_install, "libs3", "crossplatform"))
				copy_tree(os.path.join(self.dir_source, "libs3", HOST_OS), os.path.join(self.dir_install, "libs3", HOST_OS))

			result = True
		except Exception as err:
			self.status(inspect.stack()[0][3]+' failed, ' + exit_host_msg)
			raise Exception("Install files copy failed")	

		self.status('Files copied successfully')
		data = dict()
		data['date'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
		data['path'] = self.dir_install
		data['version'] = version.APP_VERSION_INT
		data['version_str'] = version.APP_VERSION
		if INST_STANDALONE is not True:
			data['cerebro_path'] = os.path.normpath(cerebro.core.application_dir())
		jsonwrite(FCONFIG, data)
		self.status('Installer config file has been written')
		# Net install
		if SETUP_NETWORK:
			with codecs.open(os.path.join(self.dir_install, "net_install.py"), "w", "utf-8") as fh:
				path_vars = {
					"MAYA_MODULE_PATH": [os.path.normpath(os.path.join("%{0}%".format(PLUGIN_EVAR), r"tentaculo/api/imaya"))],
					"MAYA_SCRIPT_PATH": [os.path.normpath(os.path.join("%{0}%".format(PLUGIN_EVAR), r"tentaculo/api/imaya"))],
					"PATH": [os.path.normpath(os.path.join("%{0}%".format(PLUGIN_EVAR), r"tentaculo/api/imax"))],
					"NUKE_PATH": [os.path.normpath(os.path.join("%{0}%".format(PLUGIN_EVAR), r"tentaculo/api/inuke"))],
					"HOUDINI_MENU_PATH": [os.path.normpath(os.path.join("%{0}%".format(PLUGIN_EVAR), r"tentaculo/api/ihoudini"))],
					"PYTHONPATH": [
						os.path.normpath(os.path.join("%{0}%".format(PLUGIN_EVAR), r"tentaculo/api/imaya")),
						os.path.normpath(os.path.join("%{0}%".format(PLUGIN_EVAR), r"tentaculo/api/imax")),
						os.path.normpath(os.path.join("%{0}%".format(PLUGIN_EVAR), r"tentaculo/api/inuke")),
						os.path.normpath(os.path.join("%{0}%".format(PLUGIN_EVAR), r"tentaculo/api/ihoudini")),
						os.path.normpath(os.path.join("%{0}%".format(PLUGIN_EVAR), r"tentaculo/api/iblender")),
						os.path.normpath(os.path.join("%{0}%".format(PLUGIN_EVAR), r"tentaculo/")),
						os.path.normpath(self.dir_install),
					]
				}
				fh.write("# -*- coding: utf-8 -*-\n")
				fh.write("{0} = r'{1}'\n\n\n'''\n".format(PLUGIN_EVAR, os.path.normpath(self.dir_install)))
				for name, values in path_vars.items():
					fh.write("{0} = r'{1}'\n".format(name, os.path.pathsep.join(values)))
				fh.write("'''\n")

		return result

	def install_maya(self):
		global PLUGIN_EVAR
		if len(self.apps["Autodesk Maya"]) == 0 : return False

		if HOST_OS == "windows":
			#dir = os.path.abspath(os.path.join(self.dir_install, r"tentaculo/api/imaya"))
			dir = os.path.normpath(os.path.join("%{0}%".format(PLUGIN_EVAR), r"tentaculo/api/imaya"))
			self.evar_set_win("MAYA_MODULE_PATH", [dir])
			self.evar_set_win("MAYA_SCRIPT_PATH", [dir])
			self.evar_set_win("PYTHONPATH", [dir])

	def install_max(self):
		global PLUGIN_EVAR
		if len(self.apps["Autodesk 3ds Max"]) == 0 : return False

		if HOST_OS == "windows":
			#dir = os.path.abspath(os.path.join(self.dir_install, r"tentaculo/api/imax"))
			dir = os.path.normpath(os.path.join("%{0}%".format(PLUGIN_EVAR), r"tentaculo/api/imax"))
			self.evar_set_win("PATH", [dir])
			#self.evar_set_win("PYTHONPATH", [dir])

	def install_nuke(self):
		global PLUGIN_EVAR
		if len(self.apps["Nuke"]) == 0 : return False

		if HOST_OS == "windows":
			#dir = os.path.abspath(os.path.join(self.dir_install, r"tentaculo/api/inuke"))
			dir = os.path.normpath(os.path.join("%{0}%".format(PLUGIN_EVAR), r"tentaculo/api/inuke"))
			self.evar_set_win("NUKE_PATH", [dir])
			self.evar_set_win("PYTHONPATH", [dir])

	def install_houdini(self):
		global PLUGIN_EVAR
		if len(self.apps["Houdini"]) == 0 : return False

		if HOST_OS == "windows":
			#dir = os.path.abspath(os.path.join(self.dir_install, r"tentaculo/api/ihoudini"))
			dir = os.path.normpath(os.path.join("%{0}%".format(PLUGIN_EVAR), r"tentaculo/api/ihoudini"))
			self.evar_set_win("HOUDINI_MENU_PATH", [dir, '&'])

	def install_c4d(self):
		if len(self.apps["Cinema 4D"]) == 0 : return False

		plugin_dir = os.path.join(self.dir_source, r"tentaculo/api/ic4d/cerebro")
		for dir in self.apps["Cinema 4D"]:
			copy_dir = os.path.join(dir, r"plugins/cerebro")
			try:
				copy_tree(plugin_dir, copy_dir)
			except:
				self.log.error("Unable to copy {0} to {1}".format(plugin_dir, copy_dir))
				cerebro_message("Manual copy required! {0} to {1}".format(plugin_dir, copy_dir))

	def install_blender(self):
		global PLUGIN_EVAR
		if len(self.apps["Blender"]) == 0 : return False

		if HOST_OS == "windows":
			#dir = os.path.abspath(os.path.join(self.dir_install, r"tentaculo/api/iblender"))
			dir = os.path.normpath(os.path.join("%{0}%".format(PLUGIN_EVAR), r"tentaculo/api/iblender"))
			self.evar_set_win("PYTHONPATH", [dir])

		src_file = os.path.join(self.dir_source, r"tentaculo/api/iblender/cerebroBlender.py")
		for dir in self.apps["Blender"]:
			copy_dir = os.path.join(dir, r"scripts/startup")
			if os.path.exists(copy_dir):
				try:
					shutil.copy(src_file, copy_dir)
				except:
					self.log.error("Unable to copy {0} to {1}".format(src_file, copy_dir))
					cerebro_message("Manual copy required! {0} to {1}".format(src_file, copy_dir))

	# ENVIRONMENT
	def evar_set_win(self, evar, values, replace = False):
		sep = os.path.pathsep
		path_string = ""

		if not replace:
			try:
				import winreg
			except:
				raise Exception("Failed to access Windows registry")

			try:
				key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, (winreg.KEY_WOW64_64KEY + winreg.KEY_READ))
				path_string = winreg.QueryValueEx(key, evar)[0]
				key.Close()
			except:
				pass

		if path_string is None or len(path_string) == 0 or replace:
			paths = [ os.path.normpath(v) for v in values ]
			path_string = sep.join(paths)
		else:
			#paths = [ p[0] + p if p.startswith(("\\", "//")) and not p.startswith(("\\\\", "////")) else p for p in path_string.split(sep) if len(p) > 0 ]
			paths = [ p for p in path_string.split(sep) if len(p) > 0 ]
			for val in values:
				if not val in paths:
					paths.append(os.path.normpath(val))

			path_string = re.sub("[;]+", ';', sep.join(paths))

		cmd = r'setx {0} "{1}"'.format(evar, path_string)
		os.system(cmd)

	def evar_setup_mac(self):
		plist = 'com.cerebro.tentaculo.plist'
		fullpath = os.path.join(self.dir_source, plist)
		destpath = os.path.join(self.dir_home, 'Library/LaunchAgents', plist)
		if not os.path.exists(os.path.dirname(destpath)):
			os.makedirs(os.path.dirname(destpath))
		elif os.path.exists(destpath):
			cmd = 'chmod u+w "{0}"'.format(destpath)
			os.system(cmd)

		shutil.copy(fullpath, destpath)
		cmd = 'chmod ugo-w "{0}"'.format(destpath)
		os.system(cmd)
		try:
			cmd = 'launchctl unload "{0}"'.format(destpath)
			os.system(cmd)
		except Exception as err:
			self.log.error(str(err))

		cmd = 'launchctl load "{0}"'.format(destpath)
		os.system(cmd)

	def evar_setup_linux(self):
		plist = '.cerebro.tentaculo.lx'
		fullpath = os.path.join(self.dir_source, plist)
		destpath = os.path.join(self.dir_cfg, plist)
		shutil.copy(fullpath, destpath)
		cmd = 'chmod u+x "{0}"'.format(destpath)
		os.system(cmd)

		exist = False
		execline = '. "{0}"'.format(destpath)
		bashrcpath = os.path.join(self.dir_home, '.profile') #bashrc
		if os.path.exists(bashrcpath):
			#shutil.copy(bashrcpath, bashrcpath + ".bak")
			bashrc = open(bashrcpath)
			exist = execline in bashrc.read()
			bashrc.close()
		
		if not exist:
			bashrc = open(bashrcpath, 'a+')
			bashrc.write('\n' + execline + '\n')
			bashrc.close()

		os.system(destpath)

	# UI
	def register_apps(self, apps):
		# Clear layout
		for i in reversed(range(self.vLayout_hosts.count())):
			widget = layout.takeAt(i).widget()
			if widget is not None:
				self.vLayout_hosts.removeWidget(widget)
				widget.deleteLater()
				widget.setParent(None)

		# Setup apps
		located = 0
		for name, paths in apps.items():
			for p in paths:
				located +=1
				self.vLayout_hosts.addWidget(self.app_widget(name, p))

		self.vLayout_hosts.addItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))
		self.status("{0} host applications found".format(located))

	def app_widget(self, name, path):
		ui_gb = QGroupBox(self.gb_hosts)
		ui_gb.setFlat(True)
		ui_hlayout = QHBoxLayout(ui_gb)

		#ui_check = QCheckBox(ui_gb)
		#ui_check.setEnabled(True)
		#ui_check.setCheckState(Qt.Checked)
		#ui_check.clicked.connect(self.checkboxToggle)
		ui_label = QLabel(ui_gb)
		ui_label.setText(name)
		ui_label.setFixedWidth(90)
		ui_instpath = QLineEdit(ui_gb)
		ui_instpath.setText(path)
		ui_instpath.setReadOnly(True)

		#ui_hlayout.addWidget(ui_check)
		ui_hlayout.addWidget(ui_label)
		ui_hlayout.addWidget(ui_instpath)

		return ui_gb

	def initUI(self):
		global INST_NETWORK
		self.setWindowFlags(Qt.Window)
		self.setObjectName(self.NAME)
		self.setWindowTitle(self.TITLE)
		self.resize(550, 600)
		self.setMinimumSize(550, 600)

		self.centralwidget = QWidget(self)
		self.vLayout = QVBoxLayout(self.centralwidget)

		# installation path gb
		self.gb_inst = QGroupBox(self.centralwidget)
		self.hLayout_inst = QHBoxLayout(self.gb_inst)

		self.inst_label = QLabel(self.gb_inst)
		self.inst_label.setText('Install path: ')

		self.inst_line = QLineEdit(self.gb_inst)
		self.inst_line.setReadOnly(True)

		self.inst_choose_pb = QPushButton(self.gb_inst)
		self.inst_choose_pb.setText('Network install')
		self.inst_choose_pb.clicked.connect(self.w_install_dir)
		self.inst_choose_pb.setVisible(not INST_NETWORK)

		self.hLayout_inst.addWidget(self.inst_label)
		self.hLayout_inst.addWidget(self.inst_line)
		self.hLayout_inst.addWidget(self.inst_choose_pb)

		# hosts found gb
		hosts_sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)
		self.gb_hosts = QGroupBox(self.centralwidget)
		self.gb_hosts.setTitle('Host applications found:')
		self.gb_hosts.setSizePolicy(hosts_sizePolicy)
		self.vLayout_hosts = QVBoxLayout(self.gb_hosts)
		self.vLayout_hosts.setContentsMargins(10, 10, 10, 10)
		self.vLayout_hosts.setSpacing(5)

		# prev version gb
		prev_sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
		self.gb_prev = QGroupBox(self.centralwidget)
		self.gb_prev.setTitle('Previous version:')
		self.gb_prev.setSizePolicy(prev_sizePolicy)
		self.vLayout_prev = QVBoxLayout(self.gb_prev)
		self.lb_prev = QLabel(self.gb_prev)
		self.lb_prev.setText('None')
		self.vLayout_prev.addWidget(self.lb_prev)

		# lower buttons gb
		self.gb_btns = QGroupBox(self.centralwidget)
		self.hLayout_btns = QHBoxLayout(self.gb_btns)

		self.pb_install = QPushButton(self.gb_btns)
		self.pb_install.setText('Install')
		self.pb_install.setAutoDefault(True)
		self.pb_install.setFocus()
		self.pb_install.clicked.connect(self.install)

		self.pb_cancel = QPushButton(self.gb_btns)
		self.pb_cancel.setText('Cancel')
		self.pb_cancel.clicked.connect(self.stop)

		self.hLayout_btns.addWidget(self.pb_cancel)
		self.hLayout_btns.addWidget(self.pb_install)

		# status
		self.statusbar = QStatusBar(self)
		self.progressbar = QProgressBar(self)
		self.progressbar.setGeometry(30, 40, 150, 25)
		self.progressbar.setMinimum(0)
		self.progressbar.setMaximum(100)
		self.statusbar.addPermanentWidget(self.progressbar)
		self.status("Ready")

		self.vLayout.addWidget(self.gb_inst)
		self.vLayout.addWidget(self.gb_prev)
		self.vLayout.addWidget(self.gb_hosts)
		self.vLayout.addWidget(self.gb_btns)
		self.vLayout.addWidget(self.statusbar)

		self.setLayout(self.vLayout)

	# WINDOW
	def run(self):
		self.show()

	def stop(self):
		self.close()

	def closeEvent(self, event):
		self.close()

class w_uninstaller(QWidget):
	NAME = "TENTACULO_UNINSTALLER"
	TITLE = "Cerebro Tentaculo uninstaller"
	parent = None
	path = None
	installed = False

	def __init__(self, parent = None):
		self.parent = parent
		super(self.__class__, self).__init__(parent = self.parent)
		self.setAttribute(Qt.WA_DeleteOnClose)
		self.initLogging()
		self.initData()
		self.initUI()

	def initData(self):
		self.path = installed_path()
		self.apps = host_apps()
		self.installed = self.path is not None and os.path.exists(self.path)
		self.TITLE = "Cerebro Tentaculo v{0} uninstaller".format(getPrevVersion()[1])

	def initLogging(self):
		self.log = logging.getLogger("ctentaculo_install")
		self.log.setLevel(logging.DEBUG)

		self.logformatter = logging.Formatter("%(asctime)s: %(levelname)s,  %(funcName)s, %(message)s")

		logpath = os.path.join(temp_dir(), "ctentaculo_install.log.txt")
		self.flog = logging.FileHandler(logpath)
		self.flog.setLevel(logging.DEBUG)
		self.flog.setFormatter(self.logformatter)

		self.log.addHandler(self.flog)
		self.log.info("\n\n--=== session started ===---")
		self.log.info("Uninstaller started")

	def initUI(self):
		self.setWindowFlags(Qt.Window)
		self.setObjectName(self.NAME)
		self.setWindowTitle(self.TITLE)
		self.resize(400, 100)
		self.setFixedSize(400, 100)

		self.vlayout = QVBoxLayout(self)

		self.gb_btns = QGroupBox(self)
		self.gb_btns.setTitle("Do you want to uninstall?")
		self.hLayout_btns = QHBoxLayout(self.gb_btns)

		self.pb_uninstall = QPushButton(self.gb_btns)
		self.pb_uninstall.setText('Uninstall')
		self.pb_uninstall.setAutoDefault(True)
		self.pb_uninstall.setFocus()
		self.pb_uninstall.setEnabled(self.installed)
		self.pb_uninstall.clicked.connect(self.uninstall)

		self.pb_cancel = QPushButton(self.gb_btns)
		self.pb_cancel.setText('Cancel')
		self.pb_cancel.clicked.connect(self.stop)

		self.hLayout_btns.addWidget(self.pb_cancel)
		self.hLayout_btns.addWidget(self.pb_uninstall)

		self.vlayout.addWidget(self.gb_btns)

	# ENVIRONMENT CLEAR
	def evar_clear_linux(self):
		destpath = os.path.join(home_dir(), "Library/LaunchAgents/com.cerebro.tentaculo.plist")
		execline = '. "{0}"'.format(destpath)
		bashrcpath = os.path.join(home_dir(), ".profile")
		if os.path.exists(destpath) and os.path.exists(bashrcpath):
			lines = [l for l in open(bashrcpath).read().splitlines() if not execline in l]
			with open(bashrcpath, "w") as f:
				for l in lines:
					f.write("{0}\n".format(l))

			cmd = 'chmod u+x "{0}"'.format(destpath)
			os.system(cmd)
			os.remove(destpath)

	def evar_clear_mac(self):
		destpath = os.path.join(config_dir(), ".cerebro.tentaculo.lx")
		if os.path.exists(destpath):
			try:
				cmd = 'launchctl unload "{0}"'.format(destpath)
				os.system(cmd)
			except Exception as err:
				self.log.error(str(err))

			cmd = 'chmod u+w "{0}"'.format(destpath)
			os.system(cmd)
			os.remove(destpath)

	# Uninstall apps
	def uninstall_c4d(self):
		for dir in self.apps["Cinema 4D"]:
			plugin_dir = os.path.join(dir, r"plugins/cerebro")
			if os.path.exists(plugin_dir):
				shutil.rmtree(plugin_dir)

	def uninstall_blender(self):
		for dir in self.apps["Blender"]:
			src_file = os.path.join(dir, r"scripts/startup/cerebroBlender.py")
			if os.path.exists(src_file):
				os.remove(src_file)

	def uninstall(self):
		global PLUGIN_EVAR
		if self.installed:
			install_cfg = getConfigFile(FCONFIG)
			self.log.info("Begin uninstall of %s", self.path)
			try:
				if HOST_OS == "windows":
					evar_clear_win(PLUGIN_EVAR)
				elif HOST_OS == "darwin":
					self.evar_clear_mac()
				elif HOST_OS == "linux":
					self.evar_clear_linux()
				self.log.info("System variables unset.")

				self.uninstall_c4d()
				self.uninstall_blender()
				self.log.info("Applications uninstalled.")

				shutil.rmtree(self.path)
				os.remove(install_cfg)
				self.log.info("Plugin folder and config removed.")
				cerebro_message("Cerebro Tentaculo uninstalled!")
			except Exception as err:
				self.log.error(str(err))
				cerebro_message("Error occured!")

	# WINDOW
	def run(self):
		self.show()

	def stop(self):
		self.close()

	def closeEvent(self, event):
		self.close()

def install():
	global INSTALLER
	global INST_STANDALONE
	global APP
	if INST_STANDALONE is True:
		APP = QApplication([])
	INSTALLER = w_installer()
	INSTALLER.run()
	if INST_STANDALONE is True:
		APP.exec_()

def update():
	global INSTALLER
	global INST_STANDALONE
	global APP
	if INST_STANDALONE is True:
		APP = QApplication([])
	INSTALLER = w_installer()
	INSTALLER.install(update=True)
	if INST_STANDALONE is True:
		APP.exec_()

def uninstall():
	global INSTALLER
	global INST_STANDALONE
	global APP
	if INST_STANDALONE is True:
		APP = QApplication([])
	INSTALLER = w_uninstaller()
	INSTALLER.run()
	if INST_STANDALONE is True:
		APP.exec_()

#Startup hook
if __name__ == "__main__":
	install()
