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
from collections import defaultdict

if not hasattr(fuse, '__version__'):
    raise RuntimeError, \
        "your fuse-py doesn't know of fuse.__version__, probably it's too old."

fuse.fuse_python_api = (0, 2)

hello_path = '/hello'
hello_str  = 'Hello World!\n'
file1      = '/1'
file1_str  = 'Hakooooooooooooooooonaaaaaaaaaaaa Matataaaaaaaaaaaaaaaaaa\n'
blist      = ['.', '..']
total_inodes     = 1024


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
        self.datablocks   = {}
        self.inodes = defaultdict(list)
        self.set_datablocks()
        self.set_inodes()
#        self.generate_list(self.block_count())      # Calculating number of blocks
        self.generate_list(total_inodes)      # Calculating number of blocks

    def getattr(self, path):
        print("getattr being called, path{0}").format(path)
        st = MyStat()
        if path == '/':
            st.st_mode = stat.S_IFDIR | 0755
            st.st_nlink = 2
        elif path[1:] in blist:
            st.st_mode = stat.S_IFREG | 0640   # Giving all permissions
            st.st_nlink = 1
            st.st_size = 0
        else:
            return -errno.ENOENT
        return st

    def readdir(self, path, offset):
        print("in readdir")
        print("offset: {0}").format(blist)
        
        for r in  blist:
            yield fuse.Direntry(r)

    def open(self, path, flags):
        print("in open")
        if path[1:] not in blist:
            return -errno.ENOENT
        accmode = os.O_RDONLY | os.O_WRONLY | os.O_RDWR
        if (((flags & accmode) != os.O_RDONLY) and ((flags & accmode) != os.O_WRONLY)):  #Catering write?
            return -errno.EACCES

    def read(self, path, size, offset):
        print("in read")
        print("offset: {0}").format(offset)
        print("size: {0}").format(size)
        buf = ''
        if path[1:] not in blist:
            return -errno.ENOENT
                
        blk_list = self.lookup_inode(path)
        for block in blk_list:
            buf += self.datablocks[block]        #combining the data of all the eight blocks
            
        return buf

    def unlink(self, path):
        print("in unlink")

    def write(self, path, buf, offset):
        print("in write")
        print("buf: {0}").format(buf)
        self.data[int(path[1:])] = buf
        #self.write_to_logfile(path, buf)
        return len(buf)

    def chmod(self, path, mode):
        print("in chmod")
        #self.[path]['st_mode'] &= 0o770000
        #self.files[path]['st_mode'] |= mode
        #return 0
        
    def chown(self, path, uid, gid):
        print("in chown")
        #self.files[path]['st_uid'] = uid
        #self.files[path]['st_gid'] = gid
        
    def create(self, path, mode):
        print("in create")
        #self.files[path] = dict(st_mode=(S_IFREG | mode), st_nlink=1,
        #                        st_size=0, st_ctime=time(), st_mtime=time(),
        #                        st_atime=time())
        
        #self.fd += 1
        #return self.fd

    def rename(self, old, new):
        print("in rename")
        #self.files[new] = self.files.pop(old)

    def rmdir(self, path):
        print("in rmdir")
        #self.files.pop(path)
        #self.files['/']['st_nlink'] -= 1

    def symlink(self, target, source):
        print("in symlink")
        #self.files[target] = dict(st_mode=(S_IFLNK | 0o777), st_nlink=1,
        #                          st_size=len(source))

        #self.data[target] = source

    def truncate(self, path, length, fh=None):
        print("in truncate")
        #self.data[path] = self.data[path][:length]
        #self.files[path]['st_size'] = length

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

    def set_datablocks(self):
        for i in range(40, 8232):
            self.datablocks[i] = ""  #Ideally should read from logfile, no data right now

    def set_inodes(self):
        start = 40
        for i in range(0, 1024):
            end = start + 8
            for j in range(start, end):
                self.inodes[i].append(j)
            start = end
            
    
    def lookup_inode(self, path):
        return self.inodes[int(path[1:])]

#    def write_to_logfile(self, path, buf):
        #with open("/home/rubab/Fuse/code/logfile", "r+") as log:
        #    log.seek()
        #    log.write() Future parts

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
