sftpserver
==========

``sftpserver`` is a simple single-threaded SFTP server based on
Paramiko's SFTPServer.

I needed a simple server that could be used as a stub for testing
Python SFTP clients so I whipped out one.


Updates/Changes
------------

* Now works also with authentication:

Note: USERNAME and PASSWORD are constants in stub_sftp.py file

* Now works also in IPv6


Installation
------------

Using ``pip``::

    $ [sudo] pip install sftpserver


Examples
--------

::

    $ sftpserver
    Usage: sftpserver [options]
    -k/--keyfile should be specified


    Options:
      -h, --help            show this help message and exit
      --host=HOST           listen on HOST [default: localhost]
      -p PORT, --port=PORT  listen on PORT [default: 3373]
      -l LEVEL, --level=LEVEL
                            Debug level: WARNING, INFO, DEBUG [default: INFO]
      -k FILE, --keyfile=FILE
                            Path to private key, for example /tmp/test_rsa.key
      -a, --auth            enable authentication on server [default: False]
      --ipv6                IPv6 addresses on interfaces [default: False]

    $ sftpserver -k /tmp/test_rsa.key -l DEBUG


Connecting with a Python client to our server:

>>> import paramiko
>>> pkey = paramiko.RSAKey.from_private_key_file('/tmp/test_rsa.key')
>>> transport = paramiko.Transport(('localhost', 3373))
>>> transport.connect(username='admin', password='admin', pkey=pkey)
>>> sftp = paramiko.SFTPClient.from_transport(transport)
>>> sftp.listdir('.')
['loop.py', 'stub_sftp.py']
