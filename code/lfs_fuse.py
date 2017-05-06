#!/usr/bin/env python

#    Copyright (C) 2006  Andrew Straw  <strawman@astraw.com>
#
#    This program can be distributed under the terms of the GNU LGPL.
#    See the file COPYING.
#

import os, stat, errno
# pull in some spaghetti to make this stuff work without fuse-py being installed
try:
    import _find_fuse_parts
except ImportError:
    pass
import fuse
from fuse import Fuse
from functools import partial

if not hasattr(fuse, '__version__'):
    raise RuntimeError, \
        "your fuse-py doesn't know of fuse.__version__, probably it's too old."

fuse.fuse_python_api = (0, 2)

hello_path = '/hello'
hello_str  = 'Hello World!\n'
file1      = '/1'
file1_str  = 'Hakooooooooooooooooonaaaaaaaaaaaa Matataaaaaaaaaaaaaaaaaa\n'

class MyStat(fuse.Stat):
    def __init__(self):
        self.st_mode = 0
        self.st_ino = 0
        self.st_dev = 0
        self.st_nlink = 0
        self.st_uid = 0
        self.st_gid = 0
        self.st_size = 0
        self.st_atime = 0
        self.st_mtime = 0
        self.st_ctime = 0

class HelloFS(Fuse):

    def __init__(self, *args, **kw):
        Fuse.__init__(self, *args, **kw)
        print("HelloFS init, {0} , {1}", args, kw)

    def getattr(self, path):
        print("getattr being called, path{0}").format(path)
        st = MyStat()
        if path == '/':
            st.st_mode = stat.S_IFDIR | 0755
            st.st_nlink = 2
        elif path == hello_path:
            st.st_mode = stat.S_IFREG | 0444
            st.st_nlink = 1
            st.st_size = len(hello_str)
        elif path[1:] in ['1', '2', '3', '4']:
            st.st_mode = stat.S_IFREG | 0444
            st.st_nlink = 1
            st.st_size = 1024
        else:
            print("going to return error")
            return -errno.ENOENT
        print("st:ouput of getattr")
        print(st)
        return st

    def readdir(self, path, offset):
        print("in readdir")
        print("offset: {0}").format(offset)
        blocks = self.block_count();
        print(blocks)
        for r in  '.', '..', '1', '2', '3', '4', hello_path[1:]:
            yield fuse.Direntry(r)

        #for r in range(1, (blocks+1)): 
        #    yield fuse.Direntry(r)

    def open(self, path, flags):
        print("in open")
        if path not in [hello_path, '/1', '/2', '/3', '/4']:
            return -errno.ENOENT
        accmode = os.O_RDONLY | os.O_WRONLY | os.O_RDWR
        if (flags & accmode) != os.O_RDONLY:
            return -errno.EACCES

    def read(self, path, size, offset):
        print("in read")
        print("offset: {0}").format(offset)
        print("size: {0}").format(size)
        if path not in [hello_path, '/1', '/2', '/3', '/4']:
            return -errno.ENOENT
        slen = len(hello_str)
        if offset < slen:
            if offset + size > slen:
                size = slen - offset
            buf = hello_str[offset:offset+size]
        else:
            buf = ''
        return buf

    def unlink(self, path):
        print("in unlink")

    ## Helper Methods

    def block_count(self):
        count = 0
        with open("/home/rubab/Fuse/code/logfile") as log:
            for chunk in iter(lambda: log.read(1024), ''):
                count += 1  #maybe make a dictionary of this
        return count
            

def main():
    print("in main")
    usage="""
Userspace hello example

""" + Fuse.fusage
    server = HelloFS(version="%prog " + fuse.__version__,
                     usage=usage,
                     dash_s_do='setsingle')

    server.parse(errex=1)
    server.main()

if __name__ == '__main__':
    main()
