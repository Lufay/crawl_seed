#!/usr/bin/env python

import sys, os, time, datetime
import argparse, random
import string, re
from functools import partial
import urllib
from multiprocessing import Pool, TimeoutError
from urlparse import urlparse

from bs4 import BeautifulSoup
try:
    import lxml
    html_parser = 'lxml'
except ImportError:
    html_parser = 'html.parser'

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from lib.file_line import GetFileLine
from lib.urllib_downloader import open_page, download as download_with_headers
from lib.link_pool import LinkPool


pic_mode = ('p', 'pic', 'g', 'original')
ori_topic = {
    'Nomosaic': 2,
    'Mosaic': 15,
    'Occident': 4,
    'Comic': 5,
    'Indigenous': 25,
    'cAptions': 26,
    'Repost': 27,
    'Pic': 8,
    'oriGinal': 16
}
header = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36',
    'Connection' : 'keep-alive',
    'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Language' : 'zh-CN,zh;q=0.9',
    'Cache-Control': 'max-age=0'
#    'Accept-Encoding': 'gzip, deflate, sdch',
#    'Referer' : domain + 'index.php',
#    'Host' : domain[7:-1],
}

#page_pattern = re.compile(ur'^(?:[([\u3010][\u4e00-\u9fa5\w/. +-]+[)\]\u3011]?)+|\u25b2\u9b54\u738b\u25b2.*\u5408\u96c6|.*\u7063\u642d.*\u65b0\u7247\u9996\u53d1')
download_pattern = re.compile(ur'http://w*[._]*(rmdown|xunfs)[._]*com')
text_download_pattern = re.compile(download_pattern.pattern + ur'/link\.php\?hash=[0-9a-fA-F]+')
redire_pattern = re.compile(ur'url=(.*)$')

open_page = partial(open_page, headers=header)
download = partial(download_with_headers, headers=header)

def load_domain(domain_file):
    with open(domain_file) as f:
        link_pool = LinkPool(f.readlines(),
                lambda link: 'index.php' in open_page(link, retry=5))
        return link_pool.get_link()

def load_topic(topic_conf):
    t = {}
    for key in topic_conf:
        newkey = key.lower()
        val = topic_conf[key]
        t[newkey] = val
        for i, c in enumerate(newkey):
            if c != key[i]:
                t[c] = val
                break
    return t

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
            'Check title failed',
            'Gateway Time-out',
            'Unknown HTTP Error',
            'Open Seed Page Failed',
            'Origin Error',
            'Empty'
            )
    black_error = ('No Valid Tag in center td',
            'Dead download link',
            'Internal Server Error',
            'Not Found')
    black_short_url = set()
    def __init__(self, filename, succ_prefix='htm_data/', log_sp='--+-+--', target='seed', has_download_url = {}, ignore_failed=True):
        self.sp = log_sp
        self.hdu = has_download_url
        if os.path.exists(filename):
            self.f = open(filename, 'r+')
            failed_dict = {}
            for line in self.f:
                if HasDownloadLog.is_succ_download(line, succ_prefix):
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
                        res = crawl_subject(url, -1 if target == 'pic'
                                else (50 if dir_not_exist else 0), logfile)
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
        return short_url in self.hdu or change_sub_url_form(short_url) in self.hdu
    def add_download(self, short_url, dirname):
        self.hdu[short_url] = dirname
    @staticmethod
    def is_succ_download(line, succ_prefix):
        if isinstance(succ_prefix, (str, unicode)):
            return line.startswith(succ_prefix)
        elif isinstance(succ_prefix, (list, tuple)):
            for prefix in succ_prefix:
                if line.startswith(prefix):
                    return True

def change_sub_url_form(sub_url):
    '''change htm_data/1903/2/3476625.html to htm_data/2/1903/3476625.html
    '''
    sub_url_seg = sub_url.split('/', 3)
    if len(sub_url_seg) > 3:
        sub_url_seg[1], sub_url_seg[2] = sub_url_seg[2], sub_url_seg[1]
        return '/'.join(sub_url_seg)

def not_refresh(content):
    '''A check function,
    ret val must be bool, "info".'''
    flag = 'Refresh this page'
    if flag in content:
        return False, flag, content
    return True, ''

class Buffer:
    def __init__(self):
        self.log_cont = []
    def write(self, s):
        self.log_cont.append(s)

class BufferList:
    def __init__(self):
        self.t = []
        self.c = 0
    def append(self, a):
        self.t.append(a)
        res = a[0]
        if res[0] or res[1] == 'Existed':
            if res[0]:
                print '.',
            self.c += 1
    @staticmethod
    def check(ts):
        cnt_succ = 0
        cnt_total = 0
        for res, _ in ts:
            if res[0]:
                cnt_succ += 1
                cnt_total += 1
            elif res[1] == 'Existed':
                cnt_total += 1
        print '.'*cnt_succ
        return cnt_total
    @staticmethod
    def dump_log(ts, logfile):
        for _, log_cont in ts:
            logfile.writelines(log_cont)

def download_BufferList(url):
    '''due to multiprocessing don't support staticmethod'''
    bf = Buffer()
    res = download(url, logfile=bf)
    return res, bf.log_cont

def download_img(soup, num, img_suffix=('jpg', 'jpeg', 'png', 'gif'), logfile=sys.stdout):
    if num == 0:
        return 0,0
    else:
        print 'Download img ',
        if isinstance(img_suffix, (str, unicode)):
            img_suffixs = (img_suffix, img_suffix.upper())
        elif isinstance(img_suffix, (list, tuple)):
            img_suffixs = [suffix.upper() for suffix in img_suffix]
            img_suffixs.extend(img_suffix)
        img_pattern_str = r'\.(%s)$' % '|'.join(img_suffixs)
        pattern = re.compile(img_pattern_str)
        it = soup('img', src=pattern, border=None) + soup('input', src=pattern, type='image')
        pic_urls = [img['src'] for img in it]
        attr = 'data-src'
        link_attr = 'data-link'
        it = soup('img', {attr:pattern}) + soup('input', {attr:pattern, 'type':'image'})
        pic_urls.extend((img[attr] for img in it
            if not img.has_attr(link_attr) or
            urlparse(img[attr]).netloc == urlparse(img[link_attr]).netloc))
        p = Pool()
        if num < 0:
            res = []
            try:
                # ^C can't kill multiprocessing
                #res = p.map(download_BufferList, pic_urls)
                res = p.map_async(download_BufferList, pic_urls).get(900)
            except TimeoutError, e:
                print "map_async download timeout!"
            finally:
                p.close()
                #p.terminate()
                p.join()
            cnt = BufferList.check(res)
        else:
            res = BufferList()
            for img_url in pic_urls:
                p.apply_async(download_BufferList, (img_url,),
                        callback=res.append)
            while res.c < num and len(res.t) != len(pic_urls):
                time.sleep(1)
            p.terminate()
            p.join()
            cnt = res.c
            res = res.t
        print
        BufferList.dump_log(res, logfile)
        return cnt, len(pic_urls)

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
        soup_j = BeautifulSoup(content, html_parser)
        form_tag = soup_j.find('form')
        if not form_tag:
            logfile.write('Error: can\'t find form tag at %s\n' % url)
            logfile.write('Content:\n%s\n' % content)
            res = (False, "No Form Tag")
            continue
        hosturl = os.path.dirname(url)
        res = download_seed_by_get_v2(form_tag, hosturl, logfile, download_retry)
        if res in ((False, "No Valid Tag in center td"), (False, "No Input Tag in Form")):
            continue
        if res[1] == "Refresh this page":
            #hash_code = url.split('=', 2)[1]
            soup_r = BeautifulSoup(res[2], html_parser)
            url = '%s/%s' % (hosturl, soup_r.a['href'])
            if 'referer' in locals():
                url = (url, referer)
        else:
            break
        time.sleep(1)
    return res

def download_seed_by_post(form_tag, soup, hosturl, logfile=sys.stdout, download_retry=0):
    dwn_url = '%s/%s' % (hosturl, form_tag['action'])
#    use html5lib form is not the parent of table
#    input_tags = form_tag('input')
    input_tags = soup.find('td', align='center')('input')
    form_data = [(str(input_tag['name']),str(input_tag['value'])) for input_tag in input_tags]
    boundary = gen_boundary()
    post_data = fill_in_post_data(boundary, form_data)
    hd = header.copy()
    hd.update({
        'Content-Type': 'multipart/form-data; boundary=%s' % boundary,
        'Content-Length': len(post_data)
    })
    if download_retry > 0:
        return download_with_headers(dwn_url, hd, post_data, check=not_refresh, logfile=logfile, retry=download_retry)
    else:
        return download_with_headers(dwn_url, hd, post_data, check=not_refresh, logfile=logfile)

def download_seed_by_get_v1(form_tag, soup, hosturl, logfile=sys.stdout, download_retry=0):
#    use html5lib form is not the parent of table
#    input_tags = form_tag('input')
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
    soup_d = BeautifulSoup(content, html_parser, from_encoding='gbk')
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
        soup_subject = BeautifulSoup(content, html_parser, from_encoding='gbk')
        meta = soup_subject.find('meta', {'http-equiv': 'refresh'})
        if meta:
            pattern = re.compile(ur'\s*\d+;\s*url=(.*\.html)', re.I)
            mt = pattern.match(meta['content'])
            if mt:
                short_url = mt.group(1)
            else:
                return False, 'Refresh short_url failed'
        else:
            try:
                title = unicode(soup_subject.title.string)
            except AttributeError, e:
                logfile.write('Error: get content\'s title failed\n')
                with open('dump.html', 'wb') as dump_file:
                    dump_file.write(content)
                return False, "Check title failed"
            break
    dcnt, dtotal = download_img(soup_subject, num_jpg, logfile=logfile)
    print 'Download Image Succuss Rate: %d/%d\n' % (dcnt, dtotal)
    if num_jpg < 0:
        if dcnt == 0:
            return False, 'Empty'
        elif dcnt <= dtotal*2/3:
            return False, 'LessSucc %d/%d' % (dcnt, dtotal)
        else:
            return True,
    dla_main = soup_subject('a', text=download_pattern)
    dla_all = soup_subject('a', href=download_pattern)
    # soup_subject.h4 is the title too
    main_urls = set([da['href'] if download_pattern.search(da['href'])
            else da.string for da in dla_main]
                + [da['href'] for da in dla_all if da.string == soup_subject.h4.string])
    if len(main_urls) == 0:
        for s in soup_subject.body.strings:
            m = text_download_pattern.search(s.encode('gb18030'))
            if m:
                main_urls.add(m.group())
        if len(main_urls) == 0:
            logfile.write('Error: not find dowload path in URL:%s\n' % url)
            res_main = (False, "No Download Link")
    extra_urls = set([da['href'] for da in dla_all]) - main_urls
    # log all links, download the first link
    if len(main_urls) > 0:
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


def crawl_content(content, target='seed', clf=sys.stdout, max_retry=12):
    '''Crawl a forum page with its (content, crawl_date),
    clf for common log of all'''
    if isinstance(content, (list, tuple)) and len(content) > 1:
        content, today = content
    else:
        today = datetime.date.today()
    if not content:
        clf.write('Error: crawl None content!!\n')
        return False
    uc = content.decode('gbk')   #gb2312
    content = uc.replace(u'<span class="sred">\u71b1</span>', u'.::')
    # install html5lib can avoid &# bug, what's more, from_encoding can be omitted
    soup = BeautifulSoup(content, html_parser)
    # find subjects in the navigation page
    yesterday = today - datetime.date.resolution
    for a in reversed(soup('a', text=re.compile(ur'\s*\.::\s*'))):
        # the tr contain 5 tds which are a, title, author, num, citime
        sub_url = str(a['href'])
        sub_url = urlparse(sub_url).path.lstrip('/')
        if sub_url in HasDownloadLog.black_short_url or clf.has_download(sub_url):
            continue
        title_td = a.parent.find_next_sibling('td')
        title = u''.join((s.strip() for s in title_td.strings))
        encode_title = title.encode('gb18030')  #gb18030 is super set of gbk, so that can avoid some encode error
        # if page_pattern.match(title):
        citime = str(title_td.find_next_sibling('td').div.string.replace(u'\u6628\u5929', yesterday.isoformat()).replace(u'\u4eca\u5929', today.isoformat()))
        now = str(time.time())
        os.mkdir(now)
        os.chdir(now)
        logfile = open('index.log', 'w+')
        logfile.write("%s\n" % sub_url)
        logfile.write("%s\n" % encode_title)
        logfile.write("%s\n" % citime)
        logfile.write("\n")
        for _ in xrange(max_retry):
            if target == 'seed':
                res_tuple = crawl_subject(sub_url, logfile=logfile)
            elif target == 'pic':
                res_tuple = crawl_subject(sub_url, -1, logfile)
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
        # endif
        clf.flush()
    clf.write('\n')
    return True

def crawl_page(page_id=1, page_cache={}, target='nomosaic', clf=sys.stdout, max_retry=80):
    '''Crawl a forum page with domain + querystr + page_id,
    it will crawl page_id cache content first,
    then crawl page_id current page and cache the page before it,
    the real function will call crawl_content to accomplish,
    clf for common log of all'''
    if 1 <= page_id <= 100:
        pathquery = 'thread0806.php?fid=%d&search=&page=' % topic[target]
        if target in pic_mode:
            target = 'pic'
        else:
            target = 'seed'
        today = datetime.datetime.today()
        if page_cache and page_id in page_cache:
            clf.write('\n%s crawl page %d from cache\n' % (today, page_id))
            crawl_content(page_cache[page_id], target, clf)  # update the has_download_url
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
            if crawl_content((content, today_date), target, clf):
                break
            else:
                time.sleep(_+0.5)

def main():
    parser = argparse.ArgumentParser(description='This program is used to download torrent by crawling page')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 3.2')
    parser.add_argument('-p', '--path', default='E:/crawl', help='The path to store[default: E:\crawl]')
    parser.add_argument('-w', '--which', choices=topic.keys(), default='n', help='Which kind of torrent you will download[default: nomosaic]')
    parser.add_argument('-r', '--redownload', action='store_false', help='Whether redownload the subject which is failed')
    parser.add_argument('-n', '--nocache', action='store_false', help='Whether cache the page before the current')
    parser.add_argument('-f', '--file', action='append', help='firstly download local page file')
    parser.add_argument('page', type=int, choices=xrange(1, 101), metavar='PAGE', nargs='+', help='The range of page or which pages')
    arg = parser.parse_args()
    workpath = arg.path+'/work'
    if not os.path.isdir(workpath):
        os.makedirs(workpath)
    os.chdir(workpath)
    clf = HasDownloadLog('index.log', ('htm_data/', 'read.php?tid='),
            target='pic' if arg.which in pic_mode else 'seed',
            ignore_failed=arg.redownload)
    if arg.file:
        for filename in arg.file:
            with open(filename) as f:
                c = f.read()
                crawl_content(c, 'pic' if arg.which in pic_mode else 'seed', clf)
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
        crawl_page(pid, page_cache, arg.which, clf)
    clf.close()

if __name__ == "__main__":
    print 'using parser %s' % html_parser
    domain = load_domain('url')
    assert domain, 'No Available domain'
    topic = load_topic(ori_topic)
    main()

