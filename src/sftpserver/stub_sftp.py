# Copyright (C) 2003-2009  Robey Pointer <robeypointer@gmail.com>
#
# This file is part of paramiko.
#
# Paramiko is free software; you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#
# Paramiko is distrubuted in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Paramiko; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA.

"""
A stub SFTP server for loopback SFTP testing.
"""

import os
from paramiko import ServerInterface, SFTPServerInterface, SFTPServer, SFTPAttributes, \
    SFTPHandle, SFTP_OK, AUTH_SUCCESSFUL, OPEN_SUCCEEDED, AUTH_FAILED



#Username and Password
USERNAME = 'admin'
PASSWD = 'admin'
#ROOT = getattr(ROOT, "ROOT", os.getcwd())



class StubServer(ServerInterface):

    def check_auth_password(self, username, password):
        """
        Override method check_auth_password to verify authentication.
        Check here for correct username and password.
        username - username to be authenticated
        password - the passwrod for this username to be checked.
        return AUTH_SUCCESSFUL or AUTH_FAILED
        """
        return AUTH_SUCCESSFUL
        
    def check_channel_request(self, kind, chanid):
        """
        Override method check_channel_request to verify channel and kind.
        Here we do not check for kind or chanid so just return OPEN_SUCCEEDED
        kind - normally it is 'session'
        chanid - paramiko channel id
        return OPEN_SUCCEEDED
        """
        return OPEN_SUCCEEDED



class AuthenticationStubServer(StubServer):
    """
    class AuthenticationStubServer - inherits from StubServer
	This class manages a sftp server with authentication
	check_auth_password method is overridden
    """
    
    def check_auth_password(self, username, password):
        """
        This method verifies authentication.
        Check here for correct USERNAME and PASSWORD
        username - username to be authenticated
        password - the passwrod for this username to be checked.
        return AUTH_SUCCESSFUL or AUTH_FAILED
        """
        if username == USERNAME and password == PASSWD:
            return AUTH_SUCCESSFUL
        else:
            return AUTH_FAILED





class StubSFTPHandle (SFTPHandle):

    def stat(self):
        """
        This method performs the stat attributes
        return path SFTPAttributes or error
        """
        try:
            return SFTPAttributes.from_stat(os.fstat(self.readfile.fileno()))
        except OSError, e:
            return SFTPServer.convert_errno(e.errno)

    def chattr(self, attr):
        """
        This method performs the stat attributes for the given path
        path - file/folder path
        return path SFTPAttributes or error
        """
        # python doesn't have equivalents to fchown or fchmod, so we have to
        # use the stored filename
        try:
            SFTPServer.set_file_attr(self.filename, attr)
            return SFTP_OK
        except OSError, e:
            return SFTPServer.convert_errno(e.errno)


class StubSFTPServer (SFTPServerInterface):
    # assume current folder is a fine root
    # (the tests always create and eventualy delete a subfolder, so there shouldn't be any mess)
    ROOT = os.getcwd()
        
    def _realpath(self, path):
        return self.ROOT + self.canonicalize(path)

    def list_folder(self, path):
        """
        This method returns the list folder given a path
        path - path to folder
        return a list of folders
        """
        path = self._realpath(path)
        try:
            out = [ ]
            flist = os.listdir(path)
            for fname in flist:
                attr = SFTPAttributes.from_stat(os.stat(os.path.join(path, fname)))
                attr.filename = fname
                out.append(attr)
            return out
        except OSError, e:
            return SFTPServer.convert_errno(e.errno)

    def stat(self, path):
        """
        This method performs the stat attributes for the given path
        path - file/folder path
        return path SFTPAttributes or error
        """
        path = self._realpath(path)
        try:
            return SFTPAttributes.from_stat(os.stat(path))
        except OSError, e:
            return SFTPServer.convert_errno(e.errno)

    def lstat(self, path):
        """
        This method performs the lstat attributes for the given path
        path - file/folder path
        return lstat SFTPAttributes or error
        """
        path = self._realpath(path)
        try:
            return SFTPAttributes.from_stat(os.lstat(path))
        except OSError, e:
            return SFTPServer.convert_errno(e.errno)

    def open(self, path, flags, attr):
        """
        This method returns the list folder given a path
        path - path to folder
        flags - file flags
        attr -  file attributes
        return a file object
        """
        path = self._realpath(path)
        try:
            binary_flag = getattr(os, 'O_BINARY',  0)
            flags |= binary_flag
            mode = getattr(attr, 'st_mode', None)
            if mode is not None:
                fd = os.open(path, flags, mode)
            else:
                # os.open() defaults to 0777 which is
                # an odd default mode for files
                fd = os.open(path, flags, 0666)
        except OSError, e:
            return SFTPServer.convert_errno(e.errno)
        if (flags & os.O_CREAT) and (attr is not None):
            attr._flags &= ~attr.FLAG_PERMISSIONS
            SFTPServer.set_file_attr(path, attr)
        if flags & os.O_WRONLY:
            if flags & os.O_APPEND:
                fstr = 'ab'
            else:
                fstr = 'wb'
        elif flags & os.O_RDWR:
            if flags & os.O_APPEND:
                fstr = 'a+b'
            else:
                fstr = 'r+b'
        else:
            # O_RDONLY (== 0)
            fstr = 'rb'
        try:
            f = os.fdopen(fd, fstr)
        except OSError, e:
            return SFTPServer.convert_errno(e.errno)
        fobj = StubSFTPHandle(flags)
        fobj.filename = path
        fobj.readfile = f
        fobj.writefile = f
        return fobj

    def remove(self, path):
        """
        This method deletes the given path to file
        path - file path
        return  SFTP_OK or error
        """
        path = self._realpath(path)
        try:
            os.remove(path)
        except OSError, e:
            return SFTPServer.convert_errno(e.errno)
        return SFTP_OK

    def rename(self, oldpath, newpath):
        """
        This method renames oldpath into newpath
        oldpath - old file path
        newpath - new file path
        return  SFTP_OK or error
        """
        oldpath = self._realpath(oldpath)
        newpath = self._realpath(newpath)
        try:
            os.rename(oldpath, newpath)
        except OSError, e:
            return SFTPServer.convert_errno(e.errno)
        return SFTP_OK

    def mkdir(self, path, attr):
        """
        This method creates a dir path with passed attributes
        path - folder path to be created
        attr - attributes
        return  SFTP_OK or error
        """
        path = self._realpath(path)
        try:
            os.mkdir(path)
            if attr is not None:
                SFTPServer.set_file_attr(path, attr)
        except OSError, e:
            return SFTPServer.convert_errno(e.errno)
        return SFTP_OK

    def rmdir(self, path):
        """
        This method deletes the given folder
        path - folder path to be deleted
        return  SFTP_OK or error
        """
        path = self._realpath(path)
        try:
            os.rmdir(path)
        except OSError, e:
            return SFTPServer.convert_errno(e.errno)
        return SFTP_OK

    def chattr(self, path, attr):
        """
        This method changes the attributes of a given path
        path - the path
        attr - file attributes to be set
        return  SFTP_OK or error
        """
        path = self._realpath(path)
        try:
            SFTPServer.set_file_attr(path, attr)
        except OSError, e:
            return SFTPServer.convert_errno(e.errno)
        return SFTP_OK

    def symlink(self, target_path, path):
        """
        This method manages symbolic links.
        target_path - the symbolic link path
        path - original path
        return  SFTP_OK or error
        """
        path = self._realpath(path)
        if (len(target_path) > 0) and (target_path[0] == '/'):
            # absolute symlink
            target_path = os.path.join(self.ROOT, target_path[1:])
            if target_path[:2] == '//':
                # bug in os.path.join
                target_path = target_path[1:]
        else:
            # compute relative to path
            abspath = os.path.join(os.path.dirname(path), target_path)
            if abspath[:len(self.ROOT)] != self.ROOT:
                # this symlink isn't going to work anyway -- just break it immediately
                target_path = '<error>'
        try:
            os.symlink(target_path, path)
        except OSError, e:
            return SFTPServer.convert_errno(e.errno)
        return SFTP_OK

    def readlink(self, path):
        """
        This method reads symbolic links.
        path - path to be read
        return SFTP_OK or error
        """
        path = self._realpath(path)
        try:
            symlink = os.readlink(path)
        except OSError, e:
            return SFTPServer.convert_errno(e.errno)
        # if it's absolute, remove the root
        if os.path.isabs(symlink):
            if symlink[:len(self.ROOT)] == self.ROOT:
                symlink = symlink[len(self.ROOT):]
                if (len(symlink) == 0) or (symlink[0] != '/'):
                    symlink = '/' + symlink
            else:
                symlink = '<error>'
        return symlink