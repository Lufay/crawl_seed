import re, urllib2, sys, os, time, datetime, argparse
from bs4 import BeautifulSoup

domain = 'http://dz.clcl.biz/'
#domain = 'http://dz.phonc.com/'
#domain = 'http://cl.clcl.biz/'
#domain = 'http://dz.1024pp.com/'
#domain = 'http://me.cldz.me/'
pathquery = 'thread0806.php?fid=2&search=&page='
header = { 'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.63 Safari/537.36',
		'Connection' : 'keep-alive',
		'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
		'Accept-Language' : 'zh-CN,zh;q=0.8'
#		'Referer' : domain + 'index.php',
#		'Host' : domain[7:-1],
		}
# header['Cache-Control'] = 'no-cache'

page_pattern = re.compile(ur'^(?:\[.+\].*)?\[[\w/. +-]+')  #\]
download_pattern = re.compile(ur'http://[w\.]*rmdown\.com')
redire_pattern = re.compile(ur'url=(.*)$')
filename_pattern = re.compile(ur'filename="(.*)"')


def open_page(url):
	'''Open a page with url, if fail to retry 100 times'''
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
			time.sleep(1)

def download(url, postdata=None, headers=header, filename=None, logfile=sys.stderr):
	'''Download a resource from url which will be named filename,
	if fail to retry 10 times'''
	if not filename and not postdata:
		filename = os.path.basename(url)
		if os.path.exists(filename):
			return "existed"
	req = urllib2.Request(url, postdata, headers)
	for _ in xrange(1, 11):
		logfile.write("Download from:\n%s\n" % url.encode('gbk'))
		try:
			res = urllib2.urlopen(req, timeout=30)
			if postdata:
				cnt_dp = res.info().get('Content-Disposition')
				if cnt_dp:
					filename = filename_pattern.search(cnt_dp).group(1)
				else:
					logfile.write(res.read())
					return "Not Found"
			logfile.write("Success\n\n")
			with open(filename, 'wb') as f:
				f.write(res.read())
			res.close()
			return filename
		except urllib2.HTTPError, e:
			logfile.write("%s\n\n" % e.reason)
		except urllib2.URLError, e:
			logfile.write("%s\n\n" % e)
		except Exception, e:
			logfile.write("Caght a unknown except!\n")
		time.sleep(_ * (1 if postdata else 0.3))

def fill_in_post_data(sp, data):
	'''Construct a str fit to multipart/form-data
	for example:
-----------------------------7df126910330
Content-Disposition: form-data; name="ref"

1513dff1899ab36f586cdf15323593052ae17c24a40
-----------------------------7df126910330
Content-Disposition: form-data; name="reff"

MTQyOTM2MDkwMQ==
-----------------------------7df126910330
Content-Disposition: form-data; name="submit"

download
-----------------------------7df126910330--
'''
	post_data_format = '--%s\r\nContent-Disposition: form-data; name="%s"\r\n\r\n%s\r\n'
	res = []
	for item in data:
		res.append(post_data_format % (sp, item[0], item[1]))
	res.append('--%s--\r\n' % sp)
	return ''.join(res)

log_sp = '--+-+--'
has_download_url = {}
def load_log(filename, succ_prefix):
	'''Load a log file which record which short_url saved in which directory,
	so, this function will initial the has_download_url dict'''
	if os.path.exists(filename):
		clf = open(filename, 'r+')
		for line in clf:
			if line.startswith(succ_prefix):
				url = line[:line.find(log_sp)]
				has_download_url[url] = line[line.rfind(log_sp)+len(log_sp):]
		return clf
	else:
		return open(filename, 'w+')

def crawl_subject(short_url, with_jpg=True, logfile=sys.stdout):
	'''Crawl a topic page with domain + short_url,
	the aim is to crawl img and find torrent download link,
	logfile for log the topic crawling state'''
	url = "%s%s" % (domain, short_url)
	content = open_page(url)
	if not content:
		logfile.write('Error: open page %s failed\n' % url)
		return False, "Open Page Failed"
	soup_subject = BeautifulSoup(content, from_encoding='gbk')
	if with_jpg:
		for img in soup_subject('img', src=re.compile(r'\.jpg$')):
			if download(img['src'], logfile=logfile) == 'existed':
				break
	dla = soup_subject('a', text=download_pattern)
	if len(dla) == 0:	# there isn't download link
		logfile.write('Error: not find dowload path in URL:%s\n' % url)
		return False, "No Download Link"
	else:	# log all links, download the first link
		logfile.write('Torrent Download Link:\n')
		for da in dla:
			logfile.write('%s\n' % da['href'])
		logfile.write('\n')
		# open download link
		for _ in xrange(100):
			content = open_page(dla[0]['href'])
			soup_d = BeautifulSoup(content, from_encoding='gbk')
			jump = unicode(soup_d.meta['content'])
			matched = redire_pattern.search(jump)
			if not matched:
				logfile.write('No redirect url\n\n')
				return False, 'No redirect url'
			url = matched.group(1)
			logfile.write('Jump to:\n%s\n' % url)
			if download_pattern.match(url):
				logfile.write('Success\n\n')
				break
		else:
			logfile.write("Download retry Failed\n\n")
			return False, "Download retry Failed"
		# open the jump path
		content = open_page(url)
		if not content:
			logfile.write('Error: open page %s failed\n' % url)
			return False, "Open Page Failed"
		soup_j = BeautifulSoup(content)
		form_tag = soup_j.find('form')
		url = '%s/%s' % (os.path.dirname(url), form_tag['action'])
	#	use html5lib form is not the parent of table
	#	input_tags = form_tag('input')
		input_tags = soup_j.find('td', align='center')('input')
		form_data = [(str(input_tag['name']),str(input_tag['value'])) for input_tag in input_tags]
		boundary='aejfmvo'
		post_data = fill_in_post_data(boundary, form_data)
		hd = header.copy()
		hd.update({
			'Content-Type': 'multipart/form-data; boundary=%s' % boundary,
			'Content-Length': len(post_data)
			})
		return True, download(url, post_data, hd, logfile=logfile)

def crawl_content(content, clf=sys.stdout):
	'''Crawl a forum page with its content,
	clf for common log of all'''
	if not content:
		clf.write('Error: crawl None content!!')
		return
	# install html5lib can avoid &# bug, what's more, from_encoding can be omitted
	soup = BeautifulSoup(content, from_encoding='gbk')   #gb2312
	# find subjects in the navigation page
	for a in reversed(soup('a', text='.::')):
		# the tr contain 5 tds which are a, title, author, num, citime
		sub_url = str(a['href'])
		title_td = a.parent.next_sibling
		title = unicode(title_td.h3.string)
		encode_title = str(title.encode('gb18030'))  #gb18030 is super set of gbk, so that can avoid some encode error
		if page_pattern.match(title):
			if sub_url in has_download_url:
				continue
			citime = str(title_td.next_sibling.next_sibling.div.string)  # risk!!!!
			now = str(time.time())
			os.mkdir(now)
			os.chdir(now)
			logfile = open('index.log', 'w')
			logfile.write("%s\n" % sub_url)
			logfile.write("%s\n" % encode_title)
			logfile.write("%s\n" % citime)
			logfile.write("\n")
			res_tuple = crawl_subject(sub_url, logfile=logfile)
			if res_tuple[0]:
				has_download_url[sub_url] = now
				clf.write(log_sp.join([sub_url, encode_title, now]))
			else:
				clf.write(log_sp.join([res_tuple[1], sub_url, encode_title, now]))
			clf.write("\n")
			logfile.close()
			os.chdir('..')
		else:
			clf.write(log_sp.join(['Fail matched', sub_url, encode_title]))
			clf.write("\n")
	clf.write('\n')
	clf.flush()

def crawl_page(page_id=1, page_cache={}, clf=sys.stdout):
	'''Crawl a forum page with domain + querystr + page_id,
	it will crawl page_id cache content first,
	then crawl page_id current page and cache the page before it,
	the real function will call crawl_content to accomplish,
	clf for common log of all'''
	today = datetime.datetime.today()
	if page_cache and page_id in page_cache:
		clf.write('\n%s crawl page %d from cache\n' % (today, page_id))
		crawl_content(page_cache[page_id], clf)  # update the has_download_url
		del page_cache[page_id]
	url = "%s%s%d" % (domain, pathquery, page_id)
	content = open_page(url)
	if page_cache and page_id != 1:
		url = "%s%s%d" % (domain, pathquery, page_id-1)
		page_cache[page_id-1] = open_page(url)
	clf.write('\n%s crawl page %d from latest\n' % (today, page_id))
	crawl_content(content, clf)

def main():
	parser = argparse.ArgumentParser(description='This program is used to download torrent by crawling page')
	parser.add_argument('-v', '--version', action='version', version='%(prog)s 3.0')
	parser.add_argument('-p', '--path', default='E:/crawl', help='The path to store')
	parser.add_argument('-n', '--nocache', action='store_false', help='Whether cache the page before the current')
	parser.add_argument('-m', '--mosaic', action='store_true', help='Which kind of torrent you will download')
	parser.add_argument('page', type=int, choices=xrange(1, 101), metavar='PAGE', nargs='+', help='The range of page or which pages')
	arg = parser.parse_args()
	workpath = arg.path+'/work'
	if not os.path.isdir(workpath):
		os.makedirs(workpath)
	os.chdir(workpath)
	if arg.mosaic:
		global pathquery
		pathquery = pathquery.replace('2', '15')
	clf = load_log('index.log', 'htm_data/')
	page_range = []
	page_cache = {}
	if len(arg.page) == 2:
		if arg.page[0] <= arg.page[1]:
			page_range = xrange(arg.page[0], arg.page[1]+1)
		else:
			page_range = xrange(arg.page[0], arg.page[1]-1, -1)
			page_cache[0] = ''
	else:
		page_range = sorted(set(arg.page), reverse=True)
		if not arg.nocache:
			page_cache[0] = ''
	for pid in page_range:
		crawl_page(pid, page_cache, clf)
	clf.close()

if __name__ == "__main__":
	main()

