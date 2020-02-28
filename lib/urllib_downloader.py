#!/usr/bin/env python

import sys
import os
import time
import urllib2, cookielib

cj = cookielib.LWPCookieJar()
cookie_support = urllib2.HTTPCookieProcessor(cj)
opener = urllib2.build_opener(cookie_support, urllib2.HTTPHandler)
urllib2.install_opener(opener)


def open_page(url, headers, retry=20):
    '''Open a page with url, if fail to retry,
    return:content or None'''
    if isinstance(url, (str, unicode)):
        h = headers
    else:
        h = headers.copy()
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
            return e.getcode(), e.reason if e.reason else 'Unknown HTTP Error'
        except:
            print "open failed"
            time.sleep(1.5)

def download(url, headers, postdata=None, filename=None, check=None, logfile=sys.stderr, retry=5):
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

if __name__ == '__main__':
    header = { 'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36',
        'Connection' : 'keep-alive',
        'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
        'Accept-Language' : 'zh-CN,zh;q=0.9'
        }
    #c = open_page('https://cl.321i.xyz/', header)
    c = open_page('https://cc.6xm.xyz/', header)
    if 'index.php' in c:
        print c
