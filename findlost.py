# coding=utf8

import os, time
from bs4 import BeautifulSoup
import trunk

#template_sub_url = 'htm_data/2/1605/1%d.html'
#beginID = 943548
#endID = 943548
template_sub_url = 'htm_data/15/1605/1%d.html'
beginID = 945177
endID = 945883
#beginID = 946558
#endID = 946563
#beginID = 947102
#endID = 948213
#beginID = 950277
#endID = 950278
#beginID = 951213
#endID = 951215
#beginID = htm_data/15/1606/1953637.html
#endID = htm_data/15/1606/1955901.html
#beginID = htm_data/15/1606/1956589.html
#endID = htm_data/15/1606/1956610.html
#beginID = htm_data/15/1606/1956907.html
#endID = htm_data/15/1606/1958373.html
#beginID = htm_data/15/1606/1958957.html
#endID = htm_data/15/1606/1958974.html
#beginID = htm_data/15/1606/1959767.html
#endID = htm_data/15/1606/1960015.html
#...
#beginID = htm_data/15/1711/2764239.html
#endID = htm_data/15/1711/2764244.html
#beginID = htm_data/15/1712/2840328.html
#endID = htm_data/15/1712/2840347.html



title_end = u'  草榴社區  - powered by phpwind.net'
tmp_path = 'E:/crawl/tmp'

if not os.path.isdir(tmp_path):
	os.mkdir(tmp_path)
os.chdir(tmp_path)
clf = trunk.HasDownloadLog('index.log', ignore_failed=False)
for id in xrange(beginID, endID):
	sub_url = template_sub_url % id
	url = trunk.domain + sub_url
	content = trunk.open_page(url, 4)
	if not content:
		print '%s open failed\n' % sub_url
		continue
	soup = BeautifulSoup(content, from_encoding='gbk')
	title = unicode(soup.title.string)
	title_end_pos = title.find(title_end)
	title = title[:title_end_pos]
	encode_title = title.encode('gb18030')

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
