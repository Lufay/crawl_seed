import os

root_dir = 'H:/mo/za'

def count(check_dir, out):
	out.write('CHECK in %s\n' % check_dir)
	filelist = os.listdir(check_dir)
	numfiles = len(filelist)
	if numfiles > 0 and os.path.isdir('%s/%s' % (check_dir, filelist[0])):
		for d in filelist:
			count('%s/%s' % (check_dir, d), out)
	else:
		out.write('FILE COUNT: %d\n' % numfiles)
		for name in filelist:
			out.write(name + '\n')

if __name__ == '__main__':
	with open('%s/../count.txt' % root_dir, 'w') as f:
		count(root_dir, f)
