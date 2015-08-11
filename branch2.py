import re, urllib2, sys, os, time, urllib, urlparse, argparse
#import posixpath, 
from bs4 import BeautifulSoup
from bs4 import element
import trunk

domain = 'http://cb.1024gc.org/bbs/'
pathquery = 'forum-%d-%d.html'
fid_id = {'latest':3, 'wuma':5, 'qibing':22, 'zipai':21, 'sanji':18, 'oumei':7, 'weimei':14, 'toupai':15}

page_pattern = re.compile(ur'\[\d{1,2}[-.]\d{1,2}\]')
href_pattern = re.compile(ur'/freeone/file.php/')

def download_torrent(url, logfile=sys.stderr):
	content = trunk.open_page(url)
	soup = BeautifulSoup(content)
	form = soup2.find('form')
#	durl = posixpath.normpath(posixpath.join(posixpath.dirname(url), form['action']))
	durl = urlparse.urljoin(url, form['action'])
	datas = form('input', {'type':'hidden'})
	data = {}
	for item in datas:
		data[item['name']] = item['value'].encode('utf8')
	postdata = urllib.urlencode(data)
	print postdata, len(postdata)
	hd = trunk.header.copy()
	hd.update({
		'Content-Type': 'application/x-www-form-urlencoded',
		'Content-Length': len(postdata),
		'Referer': str(url),
		})
	return trunk.download(durl, postdata, hd, logfile=logfile)

def crawl_subject(short_url, only_torrent=False, logfile=sys.stdout):
	url = "%s%s" % (domain, short_url)
	content = trunk.open_page(url)
	soup = BeautifulSoup(content)
	sps = soup('span', class_='bold', text=page_pattern)
	if len(sps) != 1:
		logfile.write("Error: can't find the title!\n")
		return False, "Can't find the title"
	mc = sps[0].find_next_siblings('div')
	if len(mc) != 1:
		logfile.wrire("Error: There's more than one div!\n")
		return False, "More than one div"
	if only_torrent:
		logfile.write(mc.string.encode('gbk'))
		for dpage in soup('a', href=href_pattern):
			download_torrent(dpage['href'], logfile)
		return True, sps[0].string.encode('gbk')
	dir_seq = 1
	os.mkdir(str(dir_seq))
	os.chdir(str(dir_seq))
	for child in mc[0].descendants:
		if isinstance(child, element.NavigableString):
			logfile.write(child.encode('gbk'))
		elif isinstance(child, element.Tag):
			if child.name == 'br':
				logfile.write('\n')
			elif child.name == 'img':
				trunk.download(child['src'], logfile=logfile)
			elif child.name == 'a' and href_pattern.search(child['href']):
				fn = download_torrent(child['href'], logfile)
				logfile.write('Write the file %s\n' % fn)
				dir_seq += 1
				os.chdir('..')
				os.mkdir(str(dir_seq))
				os.chdir(str(dir_seq))
		else:
			logfile.write('child type error!!!')
	os.chdir('..')
	os.rmdir(str(dir_seq))
	return True, sps[0].string.encode('gbk')

def crawl_content(content, clf=sys.stdout):
	if not content:
		clf.write('Error: crawl None content!!')
		return
	soup = BeautifulSoup(content)
	for a in reversed(soup('a', style=None, text=page_pattern)):
		now = str(time.time())
		os.mkdir(now)
		os.chdir(now)
		logfile = open('index.log', 'w')
		logfile.write('%s\n' % a.encode('gbk'))
		res_tuple = crawl_subject(a['href'], logfile=logfile)
		if res_tuple[0]:
			pass
		else:
			pass
		logfile.close()
		os.chdir('..')

def crawl_page(subject='latest', page_id=1, clf=sys.stdout):
	content = trunk.open_page(domain + pathquery % (fid_id[subject], page_id))
	crawl_content(content, clf)

def main():
	parser = argparse.ArgumentParser(description='This program is used to download torrent by crawling page')
	parser.add_argument('-v', '--version', action='version', version='%(prog)s 0.1')
	parser.add_argument('-p', '--path', default='E:/crawl/1024he', help='The path to store')
	parser.add_argument('-m', '--mode', choices=fid_id.keys(), default='latest' help='The subject to crawl')
	parser.add_argument('-n', '--nocache', action='store_false', help='Whether cache the page before the current')
	parser.add_argument('page', type=int, choices=xrange(1, 211), metavar='PAGE', nargs='+', help='The range of page or which pages')
	arg = parser.parse_args()
	if not os.path.isdir(arg.path):
		os.makedirs(arg.path)
	os.chdir(arg.path)
	clf = HasDownloadLog('index.log', '')
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
		crawl_page(arg.mode, pid, clf)
	clf.close()

if __name__ == "__main__":
	main()
