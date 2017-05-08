#!/usr/bin/env python

import os, stat, errno

try:
    import _find_fuse_parts
except ImportError:
    pass

import math
import fuse
from fuse import Fuse
from functools import partial
from collections import defaultdict

if not hasattr(fuse, '__version__'):
    raise RuntimeError, \
        "your fuse-py doesn't know of fuse.__version__, probably it's too old."

fuse.fuse_python_api = (0, 2)

blist                  = ['.', '..']
total_inodes           = 1024
BLOCK_SIZE             = 1024
INODE_SIZE             = 40
INODE_TABLE_OFFSET     = 0
INODE0_OFFSET          = 40 * BLOCK_SIZE
DATABLOCK_OFFSET       = INODE0_OFFSET + 8 * BLOCK_SIZE
ZERO_OFFSET            = 1 * BLOCK_SIZE

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
        self.datablocks   = {}                # { 41 : "This is the content in block 41!" }
        self.inode_table  = defaultdict(list)  # { 0 : [41, 21, 213 , 53, 32, 111, 219, 2] }
        self.inode0       = {}
        self.free_count   = 1
        self.read_inode_table()
        self.read_inode0()
        self.read_datablocks()
       # print("inode_table: {0}".format(self.inode_table))
       # print("inode0: {0}".format(self.inode0))
       # print("datablocks: {0}".format(self.datablocks))
        #self.set_datablocks()
        #self.set_inodes()
        #self.generate_list(total_inodes)      # Total number of blocks

    def getattr(self, path):
        print("getattr being called, path{0}").format(path)
        st = MyStat()
        if path == '/':
            st.st_mode = stat.S_IFDIR | 0755
            st.st_nlink = 2
        elif path[1:] in self.inode0:          # Check if the file is from directory
            st.st_mode = stat.S_IFREG | 0640   # Giving all permissions
            st.st_nlink = 1
            st.st_size = 8096                  # pros and cons?
        else:
            return -errno.ENOENT
        return st

    def readdir(self, path, offset):
        print("in readdir")
        
        for filename in  self.inode0:
            yield fuse.Direntry(filename)

    def open(self, path, flags):
        print("in open")
        if path[1:] not in self.inode0:
            print "sth wrong"
            return -errno.ENOENT
        accmode = os.O_RDONLY | os.O_WRONLY | os.O_RDWR
        if (((flags & accmode) != os.O_RDONLY) and ((flags & accmode) != os.O_WRONLY)):  #Catering write?
            return -errno.EACCES

    def read(self, path, size, offset):
        print("in read")
        count = 1
        buf = ""
        if path[1:] not in self.inode0:
            return -errno.ENOENT
        
        ino = self.lookup_inode0(path[1:])
        blk_list = self.lookup_datablocks(ino)
        print("in read inode: {0}, blk_list: {1}".format(ino, blk_list))
        print("in read datablocks: {0}".format(self.datablocks))
        for block in blk_list:
            if block == "0000":                       # don't need this
                continue                              # modify for reshow of data, check datablock content
            buf = buf + self.datablocks[int(block)]         # just combine and show. combining the data of all the eight blocks   ?? wrong
            
        return buf

    def unlink(self, path):
        print("in unlink")

    def write(self, path, buf, offset):
        print("in write")
        print("write offset {0}, buf: {1}".format(offset, buf))
    
        ino = self.lookup_inode0(path[1:])
        blk_list = self.lookup_datablocks(ino)
        print("in write blk list: {0}".format(blk_list))
        new_blk_list = self.update_datablocks(buf, blk_list, offset)
        print("new blk list: {0}".format(new_blk_list))
        if new_blk_list:
            self.update_inode_table(ino, new_blk_list)
            
        #print("inode table: {0}, datablock: {1}", self.inode_table, self.datablocks)
        return len(buf)

    def rename(self):
        print("in rename")

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
        return self.inode_table[int(path[1:])]

    def read_inode0(self):
        count = 0
        with open("/home/rubab/Fuse/code/logfilev2") as log:
            log.seek(40 * BLOCK_SIZE + INODE_TABLE_OFFSET)
            while 1:
                if count > 1023:
                    break
                count = count + 1
                line = log.readline()
                filename, ino = (line.strip()).split(" ")
                self.inode0[filename] = ino    

    def update_inode0(self, inode0, filename, ino):
        for k, v in self.inode0.items():
            if str(inode) == str(v):
                self.inode0.pop(k)
                self.inode0[filename] = str(v)
                break

        with open("/home/rubab/Fuse/code/logfilev2") as log:
            log.seek(40 * BLOCK_SIZE + INODE_TABLE_OFFSET)
            for k, v in self.inode0.items:
                log.write("{0} {1}\n".format(str(k), str(v)))

    def read_inode_table(self):    # have to fetch list of allocated datablocks and inode 0                                                    
        count = 0
        start = 4
        with open("/home/rubab/Fuse/code/logfilev2") as log:
            for chunk in iter(lambda: log.read(40), ''):
                start = 4
#                print("chunk: {0}").format(chunk)
                for j in range(0, 8):
                    end = start + 4
                    blk = chunk[start:end]
                    self.inode_table[count].append(blk)
                    start = end
                count += 1

    #update only when new allocation                                                                                                           
    #rewrite in case of lfs                                                                                                                
    def update_inode_table(self, ino, blk_list):
        count = 0
        start = 4
        #keep the list len to 8
        
        self.inode_table[int(ino)] = blk_list + self.inode_table[int(ino)]
        self.inode_table[int(ino)] = self.inode_table[int(ino)][:8]
        print("updated inode table: {0}".format(self.inode_table[int(ino)]))
        with open("/home/rubab/Fuse/code/logfilev2", "rb+") as log:
            log.seek(int(ino) * INODE_SIZE + INODE_TABLE_OFFSET)
            log.seek(4, 1)
            for blk in self.inode_table[int(ino)]:
                log.write(str(blk).zfill(4))
    
    def read_datablocks(self):  #save size too
        count = 1
        with open("/home/rubab/Fuse/code/logfilev2") as log:
            log.seek(DATABLOCK_OFFSET + ZERO_OFFSET)        #Data blocks start from here
            print "in readblock loop before {0}".format(log.tell())
            for chunk in iter(lambda: log.read(1024), ''):
                print "in readblock loop"
                self.datablocks[count] = chunk               #creating a dictionary of filename/filenumber and corresponding content 
                count += 1
            print self.datablocks
        return self.datablocks
        
    def update_datablocks(self, buf, blk_list, offset):  #in DS as well as file
        if offset > 0:
            buf = buf + self.datablocks[int(blk_list[0])]
        data_size = len(buf)
        chunks    = int(math.ceil(float(data_size)/float(BLOCK_SIZE)))
        new_blk_list = []
        for i in range(0, chunks):    # overwrite all data
            offset = i*1024
            blk = blk_list[i]
            if blk == "0000":
                blk = self.allocate_block() # it means first time allocation
                new_blk_list.append(blk)

            self.datablocks[int(blk)] = buf[offset:offset+1023]  

        with open("/home/rubab/Fuse/code/logfilev2", "rb+") as log:
            for blk in new_blk_list:
                log.seek(DATABLOCK_OFFSET + blk * BLOCK_SIZE)
                log.write(self.datablocks[int(blk)])

        print("in update datablocks buf : {0}".format(buf))
        print("in update datablocks : {0}".format(self.datablocks))
        print("new blk list in update: {0}".format(new_blk_list))
        return new_blk_list

    def allocate_block(self): # find next free, in log would be sequential so don't have to find
        #self.datablocks[self.free_count] = ""
        #self.free_count += 1
        #return self.free_count
        while 1:
            print "in while"
            if self.free_count not in self.datablocks:
                break
            self.free_count += 1
        return self.free_count

    def lookup_inode0(self, filename):
        return self.inode0[filename]

    def lookup_datablocks(self, ino):
        return self.inode_table[int(ino)]

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
