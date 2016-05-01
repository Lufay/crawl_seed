# coding=utf8

import os, time
from bs4 import BeautifulSoup
import trunk

#eginID = 835030
#ndID = 838261
#beginID = 840857
#endID = 840868
beginID = 843439
endID = 845261


title_end = u'  草榴社區  - powered by phpwind.net'
tmp_path = 'E:/crawl/tmp'

if not os.path.isdir(tmp_path):
	os.mkdir(tmp_path)
os.chdir(tmp_path)
clf = trunk.HasDownloadLog('index.log', ignore_failed=False)
for id in xrange(beginID, endID):
	sub_url = 'htm_data/2/1602/1%d.html' % id
	url = trunk.domain + sub_url
	content = trunk.open_page(url, 4)
	if not content:
		print '%s open failed\n' % sub_url
		continue
	soup = BeautifulSoup(content, from_encoding='gbk')
	title = unicode(soup.title.string)
	title_end_pos = title.find(title_end)
	title = title[:title_end_pos]
	encode_title = str(title.encode('gb18030'))

	now = str(time.time())
	os.mkdir(now)
	os.chdir(now)
	logfile = open('index.log', 'w+')
	logfile.write("%s\n" % sub_url)
	logfile.write("%s\n" % encode_title)
	logfile.write("\n")
	res_tuple = trunk.crawl_subject(sub_url, logfile=logfile)
	if res_tuple[0]:
		clf.write([sub_url, encode_title, now])
	else:
		clf.write([res_tuple[1], sub_url, encode_title, now])
	clf.write("\n")
	logfile.close()
	os.chdir('..')
	clf.flush()
clf.close()
