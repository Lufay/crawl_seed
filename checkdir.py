import os
import trunk

BASE_PATH = 'H:/mo'
GLOBAL_LOG = '%s/work/index.log' % BASE_PATH
LOG_SP = '--+-+--'
output = '%s/diff_os_log.txt' % BASE_PATH

def hasTorrent(path):
	for name in os.listdir(path):
		if name.endswith('.torrent'):
			return True
	else:
		return False

def makeupLog(dir_name, wf):
	root_dir_name = dir_name[:3]
	if os.path.isdir(root_dir_name):
		dir_path = '%s/%s/%s' % (BASE_PATH, root_dir_name, dir_name)
	else:
		dir_path = '%s/%s' % (os.path.dirname(GLOBAL_LOG), dir_name)
	with open('%s/index.log' % dir_path) as f:
		gl = trunk.GetFileLine(f, 200)
		firstline, secondline = gl.get_first(2)
		lastline = gl.get_last()[0]
		if lastline == 'Success' and hasTorrent(dir_path):
			wf.write(LOG_SP.join([firstline, secondline, dir_name]) + '\n')
		elif lastline.startswith('Error: not find dowload path in URL'):
			wf.write(LOG_SP.join(['No Download Link', firstline, secondline, dir_name]) + '\n')
		elif lastline.startswith('No such file'):
			wf.write(LOG_SP.join(['Not Found', firstline, secondline, dir_name]) + '\n')
		elif lastline == 'Caght a unknown except!':
			wf.write(LOG_SP.join(['Download Retry Failed', firstline, secondline, dir_name]) + '\n')
		else:
			wf.write(LOG_SP.join(['Unknown', firstline, secondline, dir_name]) + '\n')

def getDirs(start = '1492873198.72'):
	dirList = []
	dir_name = int(start[:3])
	while True:
		dir_path = '%s/%d' % (BASE_PATH, dir_name)
		if os.path.isdir(dir_path):
			dirList.extend([d for d in os.listdir(dir_path)
				if os.path.isdir('%s/%s' % (dir_path, d))
					and d >= start])
		else:
			work_dir = os.path.dirname(GLOBAL_LOG)
			dirList.extend([d for d in os.listdir(work_dir)
				if os.path.isdir('%s/%s' % (work_dir, d))
					and d >= start])
			break
		dir_name += 1
	return dirList

def getDirsFromLog(wf):
	dirList = []
	dirSet = set()
	with open(GLOBAL_LOG) as f:
		for line in f:
			line_tuple = line.split(LOG_SP)
			if len(line_tuple) < 3:
				wf.write('Invalid line:\n%s\n' % line)
				continue
			try:
				dir_t = float(line_tuple[-1])
			except ValueError:
				wf.write('No dir:\n%s\n' % line)
				continue
			else:
				dir_name = str(dir_t)
				if dir_name in dirSet:
					wf.write('%s has logged\n' % dir_name)
				else:
					dirList.append(dir_name)
					dirSet.add(dir_name)
	return dirList

def diffOSLog(wf):
	os_dirs = getDirs()
	log_dirs = getDirsFromLog(wf)
	oi = li = 0
	lenOs = len(os_dirs)
	lenLog = len(log_dirs)
	while oi < lenOs and li < lenLog:
		os_dir = os_dirs[oi]
		log_dir = log_dirs[li]
		if os_dir > log_dir:
			wf.write('%s not in os\n' % log_dir)
			li += 1
		elif os_dir < log_dir:
			wf.write('%s not in log\n' % os_dir)
			oi += 1
		else:
			li += 1
			oi += 1
	for i in range(oi, lenOs):
		os_dir = os_dirs[i]
		#wf.write('%s not in log\n' % os_dir)
		makeupLog(os_dir, wf)
	for i in range(li, lenLog):
		wf.write('%s not in os\n' % log_dirs[i])

if __name__ == "__main__":
	with open(output, 'w') as wf:
		diffOSLog(wf)
