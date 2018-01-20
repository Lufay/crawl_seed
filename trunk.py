# coding: gbk
import sys, os, time, datetime
import argparse, random
import string, re
import urllib, urllib2
from bs4 import BeautifulSoup

domain = 'http://cl.g0d7.pw/'
pathquery = 'thread0806.php?fid=2&search=&page='
header = { 'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.63 Safari/537.36',
		'Connection' : 'keep-alive',
		'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
		'Accept-Language' : 'zh-CN,zh;q=0.8'
#		'Referer' : domain + 'index.php',
#		'Host' : domain[7:-1],
}
# header['Cache-Control'] = 'no-cache'

page_pattern = re.compile(ur'^(?:[([][\u4e00-\u9fa5\w/. +-]+[)\]]?)+')
download_pattern = re.compile(ur'http://w*[._]*(rmdown|xunfs)[._]*com')
text_download_pattern = re.compile(download_pattern.pattern + ur'/link\.php\?hash=[0-9a-fA-F]+')
redire_pattern = re.compile(ur'url=(.*)$')
filename_pattern = re.compile(ur'filename="(.*)"')

class GetFileLine:
	def __init__(self, f, line_block=128):
		'''f must support seek/tell, readlines, iterator'''
		self.f = f
		self.lb = line_block
		self.file_size = os.path.getsize(f.name)
	def get_first(self, n=1):
		ori_pos = self.f.tell()
		self.f.seek(0)
		lines = []
		for line in self.f:
			line = line.strip()
			if line:
				lines.append(line)
				n -= 1
				if n == 0:
					break
		self.f.seek(ori_pos)
		return lines
	def get_last(self, n=1):
		ori_pos = self.f.tell()
		lines = []
		line_size = self.lb
		while line_size <= self.file_size:
			self.f.seek(-line_size, 2)
			rlines = self.f.readlines()
			if len(rlines) > n:
				for line in reversed(rlines):
					line = line.strip()
					if line:
						lines.append(line)
						if len(lines) == n:
							break
				else:
					lines = []
					line_size += self.lb
					continue
				break
			else:
				line_size += self.lb
				continue
		else:
			self.f.seek(0)
			lines = [line.strip() for line in self.f if line.strip()]
			lines.reverse()
		self.f.seek(ori_pos)
		return lines
	def gen_line(self):
		ori_pos = self.f.tell()
		self.f.seek(0)
		for line in self.f:
			line = line.strip()
			if line:
				yield line
		self.f.seek(ori_pos)
	def gen_rline(self):
		pass

def open_page(url, retry=20):
	'''Open a page with url, if fail to retry,
    return:content or None'''
	if isinstance(url, (str, unicode)):
		h = header
	else:
		h = header.copy()
		url, h['Referer'] = url
	req = urllib2.Request(url, headers=h)
	for _ in xrange(retry):
		try:
			print 'Openning URL:'
			print url
			res = urllib2.urlopen(req, timeout=15)
			content = res.read()
			res.close()
			print 'Success\n'
			return content
		except urllib2.HTTPError, e:
			print e
			return e.getcode(), e.reason
		except:
			print "open failed"
			time.sleep(1.5)

def download(url, postdata=None, headers=header, filename=None, check=None, logfile=sys.stderr, retry=5):
	'''Download a resource from url which will be named filename,
	if fail to retry 10 times, retry failed return False, "Retry Failed"
    if existed return False, "Existed",
    if can't find Content-Disposition return False, "Not Found",
    if check fail return the check function's ret val,
    success return True, filename.'''
	if not filename:
		filename = os.path.basename(url)
		if os.path.exists(filename):
			return False, "Existed"
	try:
		req = urllib2.Request(url, postdata, headers)
	except ValueError, e:
		logfile.write("Exception message: %s\n" % e.message)
		return False, "Download Request Failed"
	for _ in xrange(1, retry+1):
		logfile.write("Download from:\n%s\n" % url.encode('cp1252', errors='ignore'))  #gbk
		try:
			res = urllib2.urlopen(req, timeout=30 if filename == 'GENERATE_FROM_RESPONSE' else 10)
			content = res.read()
			if check:
				check_res = check(content)
				if not check_res[0]:
					logfile.write('Checked fail: %s\n' % check_res[1])
					logfile.write("Ret code: %d\n" % res.getcode())
					logfile.write("URL info:\n%s\n" % res.info())
					logfile.write('Content:\n%s\n' % content)
					return check_res
			if filename == 'GENERATE_FROM_RESPONSE':
				cnt_dp = res.info().get('Content-Disposition')
				if cnt_dp:
					filename = filename_pattern.search(cnt_dp).group(1)
				else:
					logfile.write("Can't find file name!\n")
					logfile.write("Ret code: %d\n" % res.getcode())
					logfile.write("URL info:\n%s\n" % res.info())
					logfile.write("Content:\n%s\n" % content)
					return False, "Not Found"
			logfile.write("Success\n\n")
			with open(filename, 'wb') as f:
				f.write(content)
			res.close()
			return True, filename
		except urllib2.HTTPError, e:
			logfile.write("Exception Reasion: %s\n" % e.reason)
			logfile.write("Caght a HTTP except!\n\n")
		except urllib2.URLError, e:
			logfile.write("Exception: %s\n" % e)
			logfile.write("Caght a URL except!\n\n")
		except Exception, e:
			logfile.write("Exception message: %s\n" % e.message)
			logfile.write("Caght a unknown except!\n\n")
		time.sleep(_ * (1 if postdata else 0.3))
	return False, "Download Retry Failed"

def gen_boundary():
	return '----WebKitFormBoundary' + ''.join(random.sample(string.ascii_letters+string.digits, 16))

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

class HasDownloadLog:
	'''Load a log file which record which short_url saved in which directory, redownload the failed short_url if ignore_failed is False,
	so, this class will initial the has_download_url dict,
	and provide write logfile interface'''
	redownload_error = ('Download Retry Failed',
			'Open Page Failed',
			'Can\'t open download link',
			'Check title failed'
			)
	black_error = ('No Valid Tag in center td',
			'Dead download link',
			'Internal Server Error')
	black_short_url = set()
	def __init__(self, filename, succ_prefix='htm_data/', log_sp='--+-+--', has_download_url = {}, ignore_failed=True):
		self.sp = log_sp
		self.hdu = has_download_url
		if os.path.exists(filename):
			self.f = open(filename, 'r+')
			failed_dict = {}
			for line in self.f:
				if line.startswith(succ_prefix):
					url = line[:line.find(log_sp)]
					self.hdu[url] = line[line.rfind(log_sp)+len(log_sp):]
				elif not ignore_failed:
					fail_snips = line.strip().split(log_sp)
					if len(fail_snips) == 4:
						fail_info, url = fail_snips[0:2]
						if url not in self.black_short_url:
							if fail_info in self.black_error:
								self.black_short_url.add(url)
							elif fail_info in self.redownload_error:
								failed_dict[url] = fail_snips[0:1] + fail_snips[2:]
							else:
								if url in failed_dict:
									del failed_dict[url]
								print "Load log: ignore fail_info %s" % fail_info
					else:
						#print "Load log: Can't interpret line %r" % line
						print "Load log: Can't interpret line '%s'" % line
			if not ignore_failed:
				today = datetime.datetime.today()
				self.write('\n%s redownload %d failed\n' % (today, len(failed_dict)))
				for url in failed_dict:
					if url not in self.hdu and url not in self.black_short_url:
						fail_info, title, dirname = failed_dict[url]
						dir_not_exist = not os.path.isdir(dirname)
						if dir_not_exist:
							per_dir = '../%s' % dirname[:3]
							if os.path.isdir(per_dir):
								os.chdir(per_dir)
								dir_not_exist = not os.path.isdir(dirname)
						if dir_not_exist:
							os.mkdir(dirname)
							logfile = open(dirname + '/index.log', 'w+')
							logfile.write("%s\n" % url)
							logfile.write("%s\n" % title)
							logfile.write("\n")
							logfile.close()
						os.chdir(dirname)
						logfile = open('index.log', 'a')
						logfile.write('\nRedownload\n')
						res = crawl_subject(url, 50 if dir_not_exist else 0, logfile)
						if res[0]:
							self.hdu[url] = dirname
							self.write((url, title, dirname))
							self.write("\n")
						elif res[1] != fail_info:
							self.write((res[1], url, title, dirname))
							self.write("\n")
							if res[1] in self.black_error:
								self.black_short_url.add(url)
						logfile.write("\n")
						logfile.close()
						os.chdir('../../work')
		else:
			self.f = open(filename, 'w+')
	def write(self, content):
		if isinstance(content, (int, long, float, str)):
			self.f.write(content)
		elif isinstance(content, (list, tuple)):
			self.f.write(self.sp.join(content))
		else:
			print >> sys.stderr, 'HasDownloadLog write a unknown type: %s' % type(content)
			sys.exit(1)
	def flush(self):
		self.f.flush()
	def close(self):
		self.f.close()
	def has_download(self, short_url):
		return short_url in self.hdu
	def add_download(self, short_url, dirname):
		self.hdu[short_url] = dirname

def not_refresh(content):
	'''A check function,
	ret val must be bool, "info".'''
	if content.strip().startswith('Refresh this page'):
		return False, 'Refresh this page'
	return True, ''

def download_img(soup, num, img_suffix=('jpg', 'jpeg'), logfile=sys.stdout):
	if num > 0:
		print 'Download img ',
		if isinstance(img_suffix, (str, unicode)):
			img_pattern_str = r'\.%s$' % img_suffix
		elif isinstance(img_suffix, (list, tuple)):
			img_pattern_str = r'\.(%s)$' % '|'.join(img_suffix)
		for img in soup('img', src=re.compile(img_pattern_str)):
			res = download(img['src'], logfile=logfile)
			if res == (False, 'Existed'):
				break
			elif res[0]:
				print '.',
				num -= 1
				if not num:
					break
		print

def download_seed(url, logfile=sys.stdout, retry=5, open_page_retry=0, download_retry=0):
	'''download seed from hash page
	'''
	for _ in xrange(retry):
		content = ''
		if open_page_retry > 0:
			content = open_page(url, open_page_retry)
		else:
			content = open_page(url)
		if isinstance(url, (list, tuple)):
			url, referer = url
		if isinstance(content, tuple):
			logfile.write('HTTP Error %d: %s\n' % content)
			return False, content[1]
		if not content:
			logfile.write('Error: open page %s failed\n' % url)
			res = (False, "Open Seed Page Failed")
			continue
		soup_j = BeautifulSoup(content)
		form_tag = soup_j.find('form')
		if not form_tag:
			logfile.write('Error: can\'t find form tag at %s\n' % url)
			logfile.write('Content:\n%s\n' % content)
			res = (False, "No Form Tag")
			continue
		res = download_seed_by_get_v2(form_tag, os.path.dirname(url), logfile, download_retry)
		if res in ((False, "No Valid Tag in center td"), (False, "No Input Tag in Form")):
			continue
		if res != (False, "Refresh this page"):
			break
		else:
			hash_code = url.split('=', 2)[1]
			# the const str of addr is from refresh page hit, so it can be extracted from that page
			url = ('http://www.rmdown.com/link.php?hash=' + hash_code, referer)
		time.sleep(2)
	return res

def download_seed_by_post(form_tag, soup, hosturl, logfile=sys.stdout, download_retry=0):
	dwn_url = '%s/%s' % (hosturl, form_tag['action'])
#	use html5lib form is not the parent of table
#	input_tags = form_tag('input')
	input_tags = soup.find('td', align='center')('input')
	form_data = [(str(input_tag['name']),str(input_tag['value'])) for input_tag in input_tags]
	boundary = gen_boundary()
	post_data = fill_in_post_data(boundary, form_data)
	hd = header.copy()
	hd.update({
		'Cache-Control': 'max-age=0',
		'Content-Type': 'multipart/form-data; boundary=%s' % boundary,
		'Content-Length': len(post_data)
	})
	if download_retry > 0:
		return download(dwn_url, post_data, hd, check=not_refresh, logfile=logfile, retry=download_retry)
	else:
		return download(dwn_url, post_data, hd, check=not_refresh, logfile=logfile)

def download_seed_by_get_v1(form_tag, soup, hosturl, logfile=sys.stdout, download_retry=0):
#	use html5lib form is not the parent of table
#	input_tags = form_tag('input')
	center_tag = soup.find('td', align='center')
	input_tags = center_tag('input')
	if len(input_tags) == 0:
		magnet_a = center_tag.find('a', text='Download this file using magnet')
		if magnet_a:
			filename = 'magnet.torrent'
			with open(filename, 'wb') as f:
				f.write(magnet_a['href'])
			return True, filename
		else:
			return False, "No Valid Tag in center td"
	form_data = [(str(input_tag['name']),str(input_tag['value'])) for input_tag in input_tags]
	dwn_url = '%s/%s?%s' % (hosturl, form_tag['action'], urllib.urlencode(dict(form_data)))
	if download_retry > 0:
		return download(dwn_url, filename='GENERATE_FROM_RESPONSE', check=not_refresh, logfile=logfile, retry=download_retry)
	else:
		return download(dwn_url, filename='GENERATE_FROM_RESPONSE', check=not_refresh, logfile=logfile)

def download_seed_by_get_v2(form_tag, hosturl, logfile=sys.stdout, download_retry=0):
	input_tags = form_tag('input')
	if len(input_tags) == 0:
		return False, "No Input Tag in Form"
	form_data = [(str(input_tag['name']),str(input_tag['value'])) for input_tag in input_tags]
	dwn_url = '%s/%s?%s' % (hosturl, form_tag['action'], urllib.urlencode(dict(form_data)))
	if download_retry > 0:
		return download(dwn_url, filename='GENERATE_FROM_RESPONSE', check=not_refresh, logfile=logfile, retry=download_retry)
	else:
		return download(dwn_url, filename='GENERATE_FROM_RESPONSE', check=not_refresh, logfile=logfile)

def jump_page(ori_url, logfile=sys.stdout):
	logfile.write('%s\n' % ori_url.encode('cp1252', errors='ignore'))
	content = open_page(ori_url)
	if isinstance(content, tuple):
		logfile.write('HTTP Error %d: %s\n' % content)
		return False, content[1]
	if not content:
		logfile.write("Can't open download link\n\n")
		return False, "Can't open download link"
	soup_d = BeautifulSoup(content, from_encoding='gbk')
	if u'Loading' in unicode(soup_d.body):
		jump = unicode(soup_d.meta['content'])
		matched = redire_pattern.search(jump)
		if not matched:
			logfile.write('No redirect url\n\n')
			return False, 'No redirect url'
		check_url = jump_url = matched.group(1)
		url = (jump_url, ori_url)
		logfile.write('Jump to:\n%s\n' % jump_url)
	else:
		check_url = url = ori_url
		logfile.write('Stay in:\n%s\n' % ori_url)
	if download_pattern.match(check_url):
		logfile.write('Url matched Success\n\n')
		return download_seed(url, logfile)
	else:
		logfile.write('Url not matched\n\n')
		return False, "Url not matched"

def crawl_subject(short_url, num_jpg=100, logfile=sys.stdout):
	'''Crawl a topic page with domain + short_url,
	the aim is to crawl img and find torrent download link,
	logfile for log the topic crawling state'''
	while True:
		url = "%s%s" % (domain, short_url)
		content = open_page(url)
		if isinstance(content, tuple):
			logfile.write('HTTP Error %d: %s\n' % content)
			return False, content[1]
		if not content:
			logfile.write('Error: open page %s failed\n' % url)
			return False, "Open Page Failed"
		soup_subject = BeautifulSoup(content, from_encoding='gbk')
		meta = soup_subject.find('meta', {'http-equiv': 'refresh'})
		if meta:
			pattern = re.compile(ur'\s*\d+;\s*url=(.*\.html)', re.I)
			mt = pattern.match(meta['content'])
			if mt:
				short_url = mt.group(1)
			else:
				return False, 'Refresh short_url failed'
		else:
			title = unicode(soup_subject.title.string)
			if page_pattern.match(title):
				break
			else:
				with open('dump.html', 'wb') as dump_file:
					dump_file.write(content)
				return False, "Check title failed"
	download_img(soup_subject, num_jpg, logfile=logfile)
	dla_main = soup_subject('a', text=download_pattern)
	dla_all = soup_subject('a', href=download_pattern)
	main_urls = set([da['href'] for da in dla_main])
	extra_urls = set([da['href'] for da in dla_all]) - main_urls
	if len(main_urls) == 0:
		for s in soup_subject.body.strings:
			m = text_download_pattern.search(s.encode('gb18030'))
			if m:
				main_urls.add(m.group())
		if len(main_urls) == 0:
			logfile.write('Error: not find dowload path in URL:%s\n' % url)
			res_main = (False, "No Download Link")
	# log all links, download the first link
	logfile.write('Torrent Download Link:\n')
	# download main link
	for ori_url in main_urls:
		res_main = jump_page(ori_url, logfile)
		if res_main[0] or res_main[1] != 'Url not matched':
			break
	else:
		logfile.write("No matched download url\n\n")
		res_main = (False, "No matched download url")
	# download extra link
	extra_seed_dirname = 'extra_seed'
	if len(extra_urls) > 0 and not os.path.isdir(extra_seed_dirname):
		os.mkdir(extra_seed_dirname)
		os.chdir(extra_seed_dirname)
		with open('download.log', 'w') as df_log:
			for ori_url in extra_urls:
				jump_page(ori_url, df_log)
		os.chdir('..')
	return res_main


def crawl_content(content, clf=sys.stdout, max_retry=12):
	'''Crawl a forum page with its (content, crawl_date),
	clf for common log of all'''
	if isinstance(content, (list, tuple)) and len(content) > 1:
		content, today = content
	else:
		today = datetime.date.today()
	if not content:
		clf.write('Error: crawl None content!!\n')
		return False
	# install html5lib can avoid &# bug, what's more, from_encoding can be omitted
	soup = BeautifulSoup(content, from_encoding='gbk')   #gb2312
	# find subjects in the navigation page
	yesterday = today - datetime.date.resolution
	for a in reversed(soup('a', text=re.compile(ur'\s*\.::\s*'))):
		# the tr contain 5 tds which are a, title, author, num, citime
		sub_url = str(a['href'])
		if sub_url in HasDownloadLog.black_short_url:
			continue
		title_td = a.parent.find_next_sibling('td')
		title = unicode(title_td.h3.string)
		encode_title = title.encode('gb18030')  #gb18030 is super set of gbk, so that can avoid some encode error
		if page_pattern.match(title):
			if clf.has_download(sub_url):
				continue
			citime = str(title_td.find_next_sibling('td').div.string.replace(u'昨天', yesterday.isoformat()).replace(u'今天', today.isoformat()))
			now = str(time.time())
			os.mkdir(now)
			os.chdir(now)
			logfile = open('index.log', 'w+')
			logfile.write("%s\n" % sub_url)
			logfile.write("%s\n" % encode_title)
			logfile.write("%s\n" % citime)
			logfile.write("\n")
			for _ in xrange(max_retry):
				res_tuple = crawl_subject(sub_url, logfile=logfile)
				if res_tuple[0]:
					clf.add_download(sub_url, now)
					clf.write([sub_url, encode_title, now])
					break
				elif res_tuple[1] == "Open Page Failed":
					time.sleep(_+0.5)
				else:
					clf.write([res_tuple[1], sub_url, encode_title, now])
					if res_tuple[1] in HasDownloadLog.black_error:
						HasDownloadLog.black_short_url.add(sub_url)
					break
			else:
				clf.write(["Open Page Failed", sub_url, encode_title, now])
			clf.write("\n")
			logfile.close()
			os.chdir('..')
		else:
			clf.write(['Fail matched', sub_url, encode_title])
			clf.write("\n")
		clf.flush()
	clf.write('\n')
	return True

def crawl_page(page_id=1, page_cache={}, clf=sys.stdout, max_retry=80):
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
	for _ in xrange(max_retry):
		content = open_page(url)
		if isinstance(content, tuple):
			return
		today_date = datetime.date.today()
		if page_cache and page_id != 1:
			url = "%s%s%d" % (domain, pathquery, page_id-1)
			pre_content = open_page(url)
			if isinstance(content, tuple):
				return
			page_cache[page_id-1] = pre_content, datetime.date.today()
		clf.write('\n%s crawl page %d from latest\n' % (today, page_id))
		if crawl_content((content, today_date), clf):
			break
		else:
			time.sleep(_+0.5)

def main():
	parser = argparse.ArgumentParser(description='This program is used to download torrent by crawling page')
	parser.add_argument('-v', '--version', action='version', version='%(prog)s 3.2')
	parser.add_argument('-p', '--path', default='E:/crawl', help='The path to store[default: E:\crawl]')
	parser.add_argument('-w', '--which', choices=['m','mosaic','o','occident'], help='Which kind of torrent you will download')
	parser.add_argument('-r', '--redownload', action='store_false', help='Whether redownload the subject which is failed')
	parser.add_argument('-n', '--nocache', action='store_false', help='Whether cache the page before the current')
	parser.add_argument('page', type=int, choices=xrange(1, 101), metavar='PAGE', nargs='+', help='The range of page or which pages')
	arg = parser.parse_args()
	workpath = arg.path+'/work'
	if not os.path.isdir(workpath):
		os.makedirs(workpath)
	os.chdir(workpath)
	global pathquery
	if arg.which == 'm' or arg.which == 'mosaic':
		pathquery = pathquery.replace('2', '15')
	elif arg.which == 'o' or arg.which == 'occident':
		pathquery = pathquery.replace('2', '4')
	clf = HasDownloadLog('index.log', 'htm_data/', ignore_failed=arg.redownload)
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

