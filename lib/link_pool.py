#!/usr/bin/env python

class LinkPool:
    def __init__(self, links, checker=None):
        self.n = len(links)
        assert self.n > 0, 'link pool empty!'
        self.idx = -1
        self.links = [link.strip() for link in links]
        self.checker = checker
    def get_link(self):
        n = self.n
        for i in xrange(1, n+1):
            idx = (self.idx + i) % n
            link = self.links[idx]
            if self.checker:
                try:
                    if self.checker(link):
                        self.idx = idx
                        return link
                except Exception, e:
                    print e
            else:
                self.idx = idx
                return link


if __name__ == '__main__':
    t = LinkPool(['a', 'b', 'c'], lambda t: t != 'b')
    print t.get_link()
    print t.get_link()
    print t.get_link()
    print t.get_link()
    t = LinkPool([])
