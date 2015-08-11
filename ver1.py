import re, urllib2, sys, os, time, datetime
from bs4 import BeautifulSoup

domain = 'http://me.mecl.me/'
#domain = 'http://re.clcl.be/'
#domain = 'http://pw.lv1024.pw/'
listpath = 'thread0806.php?fid=2&search=&page='
header = { 'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.63 Safari/537.36',
		'Connection' : 'keep-alive',
		'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
		'Accept-Language' : 'zh-CN,zh;q=0.8'
#		'Referer' : domain + 'index.php',
#		'Host' : domain[7:-1],
		}
# header['Cache-Control'] = 'no-cache'

page_pattern = re.compile(ur'^\[[\w/. ]+\]')
download_pattern = re.compile(ur'http://[w\.]*rmdown\.com')
redire_pattern = re.compile(ur'url=(.*)$')
filename_pattern = re.compile(ur'filename="(.*)"')


def open_page(url):
	req = urllib2.Request(url, headers=header)
	for _ in xrange(100):
		try:
			print 'Openning URL:'
			print url
			res = urllib2.urlopen(req) #, timeout=10
			content = res.read()
			res.close()
			print 'Success\n'
			return content
		except:
			print "open failed"

def download(url, name=None, logfile=sys.stderr):
	if not name:
		name = os.path.basename(url)
		if os.path.exists(name):
			return "existed"
	req = urllib2.Request(url, headers=header)
	for _ in xrange(10):
		logfile.write("Download:\n%s\n" % url)
		try:
			res = urllib2.urlopen(req, timeout=30)
			logfile.write("Success\n\n")
			with open(name, 'wb') as f:
				f.write(res.read())
			res.close()
			return name
		except urllib2.HTTPError, e:
			logfile.write("%s\n\n" % e.reason)
		except urllib2.URLError, e:
			logfile.write("%s\n\n" % e)
		except Exception, e:
			logfile.write("Caght a unknown except!\n")
		time.sleep(1)

#-----------------------------7df126910330
#Content-Disposition: form-data; name="ref"
#
#1513dff1899ab36f586cdf15323593052ae17c24a40
#-----------------------------7df126910330
#Content-Disposition: form-data; name="reff"
#
#MTQyOTM2MDkwMQ==
#-----------------------------7df126910330
#Content-Disposition: form-data; name="submit"
#
#download
#-----------------------------7df126910330-- 
def file_in_post_data(sp, data):
	post_data_format = '--%s\r\nContent-Disposition: form-data; name="%s"\r\n\r\n%s\r\n'
	res = []
	for item in data:
		res.append(post_data_format % (sp, item[0], item[1]))
	res.append('--%s--\r\n' % sp)
	return ''.join(res)

log_sp = '--+-+--'
has_download_url = {}
def load_log(filename):
	clf = open(filename, 'r+')
	for line in clf:
		if line.startswith('htm_data/'):
			url = line[:line.find(log_sp)]
			has_download_url[url] = line[line.rfind(log_sp)+len(log_sp):]
	return clf

def crawl_page(page_id=1, clf=sys.stdout):
	today = datetime.datetime.today()
	clf.write('\n%s crawl page %d\n' % (today, page_id))
	url = "%s%s%d" % (domain, listpath, page_id)
	content = open_page(url)
	soup = BeautifulSoup(content, from_encoding='gbk')   #gb2312
	# find items in the navigation page
	for a in reversed(soup('a', text='.::')):
		title_td = a.parent.next_sibling
		title = unicode(title_td.h3.string)
		if page_pattern.match(title):
			# the tr contain 5 tds which are a, title, author, num, citime
			item_url = str(a['href'])
			if item_url in has_download_url:
				continue
			encode_title = str(title.encode('gb18030'))  #gb18030 is super set of gbk, so that can avoid some encode error
			citime = unicode(title_td.next_sibling.next_sibling.div.string)
			now = str(time.time())
			os.mkdir(now)
			os.chdir(now)
			logfile = open('index.log', 'w')
			logfile.write("%s\n" % item_url)
			logfile.write("%s\n" % encode_title)
			logfile.write("%s\n" % citime)
			logfile.write("\n")
			clf.write(log_sp.join([item_url, encode_title, now]))
			clf.write("\n")
			# open item page to find download link
			url = "%s%s" % (domain, a['href'])
			content = open_page(url)
			soup2 = BeautifulSoup(content, from_encoding='gbk')
			for img in soup2('img', src=re.compile(r'\.jpg$')):
				if download(str(img['src']), logfile=logfile) == 'existed':
					break
			dla = soup2('a', text=download_pattern)
			if len(dla) == 0:	# there isn't download link
				logfile.write('Error: not find dowload path in URL:%s\n' % url)
			else:	# log all links, download the first link
				logfile.write('Torrent Download Link:\n')
				for da in dla:
					logfile.write('%s\n' % da['href'])
				logfile.write('\n')
				# open download link
				content = open_page(dla[0]['href'])
				soup3 = BeautifulSoup(content, from_encoding='gbk')
				jump = unicode(soup3.meta['content'])
				url = redire_pattern.search(jump).group(1)
				# open the jump path
				content = open_page(url)
				soup4 = BeautifulSoup(content, from_encoding='gbk')
				form_tag = soup4.find('form')
				url = '%s/%s' % (os.path.dirname(url), form_tag['action'])
				input_tags = form_tag('input')
				form_data = [(str(input_tag['name']),str(input_tag['value'])) for input_tag in input_tags]
				boundary='aejfmvo'
				post_data = file_in_post_data(boundary, form_data)
				hd = header.copy()
				hd.update({
					'Content-Type': 'multipart/form-data; boundary=%s' % boundary,
					'Content-Length': len(post_data)
					})
				req = urllib2.Request(url, post_data, hd)
				res = urllib2.urlopen(req)
				cnt_dp = res.info().get('Content-Disposition')
				if cnt_dp:
					filename = filename_pattern.search(cnt_dp).group(1)
					with open(filename, 'wb') as seedfile:
						seedfile.write(res.read())
				else:
					logfile.write(res.read())
				res.close()
			logfile.close()
			os.chdir('..')
	clf.write('\n')
	clf.flush()

if __name__ == "__main__":
	os.chdir('E:/crawl/')
	if not os.path.isdir('work'):
		os.mkdir('work')
	os.chdir('./work')
	argc = len(sys.argv)
	if argc == 2:
		pid = int(sys.argv[1])
		with load_log('index.log') as f:
			crawl_page(pid, f)
	elif argc == 3:
		start_pid = int(sys.argv[1])
		end_pid = int(sys.argv[2])
		clf = load_log('index.log')
		if start_pid <= end_pid:
			for pid in range(start_pid, end_pid+1):
				crawl_page(pid, clf)
		else:
			for pid in range(start_pid, end_pid-1, -1):
				crawl_page(pid, clf)
		clf.close()
	else:
		print >>sys.stderr, "Usage: %s start_page_id [end_page_id]"

