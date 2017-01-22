import os, sys, re, string, argparse
import trunk

# fill failed list from checked_log
failed_dict = {}
clf = ''
default_timestamp_start = 1000000000.0
default_timestamp_end = 9999999999.99

url_head_pattern = re.compile(ur'http://.*$')
hash_pattern = re.compile(ur'=([0-9a-f]{42,})(&z)?$')

def check_res(res):
	'''res is download result, res[0] is bool whether download is successful,
	if succ: add success to logfile return True,
	else: if fail info is Not Found return False,
		else: report error and exit.
	'''
	if res[0]:
		f = open('index.log', 'a')
		f.write('\nSuccess\n')
		f.close()
		return True
	else:
		if res[1] == 'Not Found':
			return False
		else:
			print "\nEncount a error:\n"
			print '%s\n' % res[1]
			sys.exit(1)

def hash_download(url_head, lines, logfile=sys.stdout):
	for line in lines:
		match = hash_pattern.search(line)
		if match:
			hash_code = match.group(1)
			url = url_head + hash_code
			print 'hash is %s, while length is %d' % (hash_code, len(hash_code))
			print 'Download seed from url:\n%s' % url
			res = trunk.download_seed(url, logfile, 10)
			if not check_res(res):
				logfile.write("\nOld_hash is %s, while length is %d\n" % (hash_code, len(hash_code)))
				if len(hash_code) == 42:
					ret = False
					for c in string.hexdigits[:16]:
						print 'add %s to url and retry' % c
						url = '%s%s%s' % (url_head, hash_code, c)
						logfile.write('Download seed from url:\n%s\n' % url)
						res = trunk.download_seed(url, logfile, 10)
						ret = check_res(res) or ret
					if ret:
						return ret
					else:
						print 'hash_code add char retry failed'
						sys.exit(1)
				elif len(hash_code) == 44:
					ret = False
					for i in range(43, -1, -1):
						print 'remove pos%d:%s from url and retry' % (i+1, hash_code[i])
						url = '%s%s%s' % (url_head, hash_code[:i], hash_code[i+1:])
						logfile.write('Download seed from url:\n%s\n' % url)
						res = trunk.download_seed(url, logfile, 10)
						ret = check_res(res) or ret
					if ret:
						return ret
					else:
						print 'hash_code remove char retry failed'
						sys.exit(1)
				else:
					print 'hash_code error'
					sys.exit(1)
	else:
		print 'Not find hash of last %d' % len(lines)
		return False

def retry_hash_download(gfl, max_num_retry_lines=500, logfile=sys.stdout):
	url_head = 'http://www.rmdown.com/link.php?hash='
	for n_lastline in range(30, max_num_retry_lines, 20):
		lastlines = gfl.get_last(n_lastline)[1:]
		if hash_download(url_head, lastlines, logfile):
			return
		else:
			if len(lastlines)+1 < n_lastline:
				sys.exit(1)
	else:
		print "The num of lines is more than %d" % max_num_retry_lines
		sys.exit(1)

def fill_failed_dict(checked_log, log_sp='--+-+--'):
	if os.path.isfile(checked_log):
		with open(checked_log) as f:
			for line in f:
				line_tuple = line.split(log_sp)
				if len(line_tuple) == 4:
					fail_info, url, title, dirname = line_tuple
					failed_dict[dirname.strip()] = fail_info

def check_dir(dir_name, logfile_name):
	os.chdir(dir_name)
	try:
		f = open('index.log')
	except IOError:
		print "can't open index.log in %s\n" % dir_name
		sys.exit(1)
	ret = True
	gl = trunk.GetFileLine(f, 200)
	firstline, secondline = gl.get_first(2)
	lastlines = gl.get_last(10)
	if lastlines[0] == 'Success':
		print "%s success" % dir_name
		if clf and not clf.has_download(firstline):
			clf.write([firstline, secondline, dir_name])
			clf.write("\n")
	else:
		print "last line of index.log in %s is:" % dir_name
		print `lastlines[0]`
		logfile = sys.stdout
		if logfile_name:
			logfile = open(logfile_name, 'w+')
		if lastlines[0].startswith('Refresh this page'):
			url_head = url_head_pattern.search(lastlines[0]).group()
			ret = hash_download(url_head, lastlines[1:], logfile)
		elif lastlines[0] == 'Checked fail: Refresh this page' or \
			 lastlines[0] == "Download retry Failed" or \
			 lastlines[0].startswith('No such file'):
			retry_hash_download(gl, logfile=logfile)
		elif lastlines[0].startswith('Error: open page '):
			ret = check_res(trunk.crawl_subject(firstline, logfile=logfile))
		elif lastlines[0].startswith('Error: not find dowload path in'):
			ret = check_res(trunk.crawl_subject(firstline, 0, logfile))
		else:
			if dir_name in failed_dict:
				print '%s has checked failed, info:\n%s' % (dir_name, failed_dict[dir_name])
			choice = raw_input('expect lastline or retry?[y/r/n]')
			if choice.startswith('r'):
				retry_hash_download(gl, logfile=logfile)
			ret = choice.startswith('y')
	f.close()
	os.chdir('..')
	return ret

def check_dirs(check_root, start_timestamp, end_timestamp, logfile_name=''):
	for dir_name in sorted(os.listdir(check_root)):
		if os.path.isdir(dir_name):
			try:
				dir_timestamp = float(dir_name)
			except ValueError:
				continue
			if dir_timestamp + 1 > start_timestamp/10000 and \
			   dir_timestamp < end_timestamp/10000:
				os.chdir(dir_name)
				if not check_dirs('%s/%s' % (check_root, dir_name),
								  start_timestamp,
								  end_timestamp,
								  logfile_name):
					return False
				os.chdir('..')
			elif dir_timestamp >= start_timestamp and \
				 dir_timestamp < end_timestamp:
				if not check_dir(dir_name, logfile_name):
					return False
	return True

def main():
	parser = argparse.ArgumentParser(description='This program is used to check log to make up redownload that unsuccess')
	parser.add_argument('-p', '--path', default='F:/nmo', help='The path to check[default: F:/nmo]')
	parser.add_argument('-s', '--start', type=float, default=default_timestamp_start, help='The timestamp starts to check[default: %f]' % default_timestamp_start)
	parser.add_argument('-e', '--end', type=float, default=default_timestamp_end, help='The timestamp ends to check[default: %f]' % default_timestamp_end)
	parser.add_argument('-l', '--log', default='check.log', help='The log name of check[default: check.log]')
	parser.add_argument('-t', '--trunklog', default='redownload.log', help='The log name of redownload log[default: redownload.log]')
	parser.add_argument('-c', '--checkedlog', default='E:/crawl/work/index.txt', help='The log name of checked download log[default: E:/crawl/work/index.txt]')
	arg = parser.parse_args()
	fill_failed_dict(arg.checkedlog)
	os.chdir(arg.path)
	global clf
	if os.path.isfile(arg.log):
		clf = trunk.HasDownloadLog(arg.log)
	check_dirs(arg.path, arg.start, arg.end, arg.trunklog)
	if clf:
		clf.close()

if __name__ == "__main__":
	main()
