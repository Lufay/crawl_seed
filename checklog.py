import os, sys, trunk

os.chdir("E:/crawl/work")

start_time = 1436653350.64

for dir_name in sorted(os.listdir('.')):
	try:
		dir_time = float(dir_name)
	except ValueError:
		continue
	if dir_time >= start_time:
		os.chdir(dir_name)
		try:
			f = open('index.log')
		except IOError:
			print "can't open index.log in %s\n" % dir_name
			sys.exit(1)
		gl = trunk.GetFileLine(f, 200)
		firstline = gl.get_first()
		lastline = gl.get_last()
		f.close()
#		if lastline != 'Success\n':
#			print "last line of index.log in %s is:" % dir_name
#			print lastline
		if lastline.startswith('Refresh this page'):
			res = trunk.crawl_subject(firstline, False)
			if res[0]:
				f = open('index.log', 'a')
				f.write('\nSuccess\n')
				f.close()
			else:
				if res[1] != 'Open Page Failed':
					print "\nEncount a error in %s\n" % dir_name
					print '%s\n' % res[1]
					sys.exit(2)
		os.chdir('..')
