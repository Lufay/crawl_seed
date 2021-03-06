import re, urllib2, sys, os, time
from bs4 import BeautifulSoup
import trunk

domain = 'http://99btgc01.com/'
pathquery = 'forumdisplay.php?fid=21&page='
header = trunk.header
fid_id = {'weimei': 13, 'zipai':9, 'oumei':10}

# for picture
pathquery = pathquery.replace('21', str(fid_id['oumei'])

#page_pattern = re.compile(ur'\[\d{2}-\d{2}\]')
href_pattern = re.compile(ur'viewthread\.php\?tid=\d+.*extra=page%3D1$')

def crawl_subject(short_url, with_jpg=True, logfile=sys.stdout):
	url = "%s%s" % (domain, short_url)
	content = trunk.open_page(url)
	soup = BeautifulSoup(content)
	for img in soup('img', onclick=True):
		if trunk.download(img['src'], logfile=logfile) == 'existed':
			break

def crawl_content(content, clf=sys.stdout):
	soup = BeautifulSoup(content)
	for a in reversed(soup('a', href=href_pattern, title=None, style=None)):
#		clf.write('%s\n' % a.encode('gbk'))
		print a.encode('gbk')
		now = str(time.time())
		os.mkdir(now)
		os.chdir(now)
		crawl_subject(a['href'], logfile=clf)
		os.chdir('..')

def crawl_page(page_id=1, clf=sys.stdout):
	content = trunk.open_page('%s%s%d' % (domain, pathquery, page_id))
	crawl_content(content, clf)


if __name__ == "__main__":
	if not os.path.isdir('aiwei'):
		os.mkdir('aiwei')
	os.chdir('aiwei')
	f = open('temp.log', 'w')
	crawl_page(clf=f)
	f.close()
