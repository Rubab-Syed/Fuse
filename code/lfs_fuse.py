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
blist      = ['.', '..']

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
        self.data = dict()
        self.generate_list(self.block_count())      # Calculating number of blocks
        print("HelloFS init, {0} , {1}", args, kw)

    def getattr(self, path):
        print("getattr being called, path{0}").format(path)
        st = MyStat()
        if path == '/':
            st.st_mode = stat.S_IFDIR | 0755
            st.st_nlink = 2
        elif path[1:] in blist:
            st.st_mode = stat.S_IFREG | 0444
            st.st_nlink = 1
            st.st_size = 1024
        else:
            return -errno.ENOENT
        print("st:ouput of getattr")
        print(st)
        return st

    def readdir(self, path, offset):
        print("in readdir")
        print("offset: {0}").format(offset)

        for r in  blist:
            yield fuse.Direntry(r)

    def open(self, path, flags):
        print("in open")
        if path[1:] not in blist:
            return -errno.ENOENT
        accmode = os.O_RDONLY | os.O_WRONLY | os.O_RDWR
        if (flags & accmode) != os.O_RDONLY:  #Catering write?
            return -errno.EACCES

    def read(self, path, size, offset):
        print("in read")
        print("offset: {0}").format(offset)
        print("size: {0}").format(size)

        if path[1:] not in blist:
            return -errno.ENOENT
                
        buf = self.data[int(path[1:])]        #reading just the value of hash by giving file number as key
            
        return buf

    def unlink(self, path):
        print("in unlink")

    def write(self, path):
        print("in write")

    ## Helper Methods

    def block_count(self):
        count = 0
        with open("/home/rubab/Fuse/code/logfile") as log:
            for chunk in iter(lambda: log.read(1024), ''):
                self.data[count] = chunk      #creating a dictionary of filename/filenumber and corresponding content              
                count += 1  
        return count
            
    def generate_list(self, count):
        for i in range(0, count):
            blist.append(str(i))
        return blist


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
