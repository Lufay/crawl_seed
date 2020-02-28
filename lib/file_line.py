#!/usr/bin/env python

import os

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
            rlines = self.f.readlines()[1:]
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
