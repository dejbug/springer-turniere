import os

import __main__

def root(top, __file = __main__.__file__):
	"""
	>>> root("user", __file="/home/user/folder/subfolder/script.py")
	'/home/user/'
	"""
	top = "/%s/" % top
	i = __file.rfind(top)
	if i < 0: return
	i += len(top)
	root = __file[:i]
	tail = __file[i:]
	return root

def path(top, rel, __file = __main__.__file__):
	"""
	>>> path("user", "run.py", __file="/home/user/folder1/subfolder/script.py")
	'/home/user/run.py'
	"""
	if not rel.startswith("/"): rel = "/" + rel
	r = root(top, __file)
	if r: return os.path.abspath(r + rel)

def walk(top, rel=None, __file = __main__.__file__):
	cwd = path(top, rel, __file)
	for t,dd,nn in os.walk(cwd):
		for n in nn:
			yield os.path.join(t, n)
