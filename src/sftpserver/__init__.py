###############################################################################
#
# Copyright (c) 2011 Ruslan Spivak
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
###############################################################################

__author__ = 'Ruslan Spivak <ruslan.spivak@gmail.com>'

import time
import socket
import optparse
import sys
import textwrap

import paramiko

from sftpserver.stub_sftp import StubServer, StubSFTPServer, AuthenticationStubServer

HOST, PORT = 'localhost', 3373
BACKLOG = 10


def retrieve_socket_ipv6_address(host, port):
    """
    This function return the socket address in case of ipv6 protocol
    host - the host name (interface address)
    port - the port the host is listening
    return sockaddr
    """
    # try to detect whether IPv6 is supported at the present system and
        # fetch the IPv6 address of localhost.
    if not socket.has_ipv6:
        raise Exception("The local machine has no IPv6 support enabled")
 
    addrs = socket.getaddrinfo(host, port, socket.AF_INET6, 0, socket.SOL_TCP)
    # example output: [(23, 0, 6, '', ('::1', 10008, 0, 0))]
 
    if len(addrs) == 0:
        raise Exception("There is no IPv6 address configured for %s" % host)
 
    entry0 = addrs[0]
    sockaddr = entry0[-1]
    return sockaddr
 
 
def ipv6_bind(sockaddr):
    """
    This function returns a socket after binding the given socket address in ipv6.
    sockaddr - the socket address (obtained usually calling  socket.getaddrinfo)
    return the socket after bind operation
    """
    s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    s.bind(sockaddr)
    return  s




def start_server(host, port, keyfile, level, auth, ipv6):
    """
    This function starts the server and it is called by 'main'
    It works for both ipv4 and ipv6 using two different approaches.
    In principle, one could always use the getsockattr retrieving the
    data structure for socket address.
    host - host address (IPv4 or IPv6 address are allowed)
    port - listening port
    keyfile - the file where key s stored (fingerprint will be retrreved automatically)
    level - logging level (default is INFO)
    ipv6 - use ipv6 procedure to get the socket address (for IPv6)
    """
    paramiko_level = getattr(paramiko.common, level)
    paramiko.common.logging.basicConfig(level=paramiko_level)
    print socket.has_ipv6

    #IPv6: it is a 4-tuple
    if ipv6:
        sockaddr = retrieve_socket_ipv6_address(host, port)
        server_socket = ipv6_bind(sockaddr)
        print "You are in IPv6, ipv6 = %s" % ipv6

    #IPv4: it is a 2-tuple (host,port)
    else:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
        server_socket.bind((host, port))
        server_socket.listen(BACKLOG)


    while True:
        conn, addr = server_socket.accept()

        host_key = paramiko.RSAKey.from_private_key_file(keyfile)
        print host_key
        transport = paramiko.Transport(conn)
        transport.add_server_key(host_key)
        transport.set_subsystem_handler(
            'sftp', paramiko.SFTPServer, StubSFTPServer)
        if auth:
            server = AuthenticationStubServer()
        else:
            server = StubServer()

        transport.start_server(server=server)

        channel = transport.accept()

       #while transport.is_active():
              #    time.sleep(1)


def main():
    usage = """\
    usage: sftpserver [options]
    -k/--keyfile should be specified
    """
    parser = optparse.OptionParser(usage=textwrap.dedent(usage))
    parser.add_option(
        '--host', dest='host', default=HOST,
        help='listen on HOST [default: %default]')
    parser.add_option(
        '-p', '--port', dest='port', type='int', default=PORT,
        help='listen on PORT [default: %default]'
        )
    parser.add_option(
        '-l', '--level', dest='level', default='INFO',
        help='Debug level: WARNING, INFO, DEBUG [default: %default]'
        )
    parser.add_option(
        '-k', '--keyfile', dest='keyfile', metavar='FILE',
        help='Path to private key, for example /tmp/test_rsa.key'
        )
    parser.add_option(
        '-a', '--auth', dest='auth', action="store_true", default=False,
        help='Enable authentication on server'
    )
    parser.add_option(
        '--ipv6', action='store_true', dest='ipv6', default=False,
        help='IPv6 addresses on interfaces'
    )

    options, args = parser.parse_args()

    if options.keyfile is None:
        parser.print_help()
        sys.exit(-1)

    start_server(options.host, options.port, options.keyfile, options.level, options.auth, options.ipv6)


if __name__ == '__main__':
    main()
