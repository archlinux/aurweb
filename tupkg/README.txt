TU Packaging Tools (tupkg)
--------------------------
- client side (python for proof of concept, later re-write to C?)
  The main purpose of this tool is to upload the compiled
  pkg.tar.gz to the server.  It can (should?) do some verification
  on the package prior to uploading to the server.  It will have
  a config file to store run-time information such as username
  (email), password, and server name.

- server side (python for proof of concept, later re-write to C?)
  The server side will handle incoming connections from its client
  side counterpart.  The server should bind to port 80 (maybe a
  vhost such as tupkg.archlinux.org?) so that firewalls won't be
  an issue.  The server verifies the client authentication data,
  and then accepts the package(s).  If port 80 is not available,
  perhaps 443, or are there other 'standard' ports that usually
  do not get filtered?

  I think the server should be multithreaded to handle simultaneous
  uploads rather than queue up requests.  The download should be
  stored in a temp directory based on the username to prevent
  directory, filename clashes.

  Once the package(s) is uploaded, the server can either kick off
  a gensync, or we can write a separate script to call gensync once
  or twice a day.  My preference would be a separate script to call
  gensync (like the *NIX philosophy of one tool per task).

- protocol (c: => client, s: => server)
  Whenever the client/server exchange a message, it is always
  preceeded by two-bytes representing the following message's
  length.  For example, when the client connects, it will send:

    0x0028username=bfinch@example.net&password=B0b

  0x0028 is the 40 byte strlen of the message in two-bytes.  The
  client and server always read two-bytes from the socket, and
  then know how much data is coming and can read that amount of
  bytes from the socket.

  ==> authentication
  c: username=emailaddy&password=mypassword
  s: result=PASS|FAIL

     NOTE:  We can add encryption easily enough with the python
            version using the socket.ssl method.

  ==> uploading package data
  if PASS:

    c: numpkgs=2&name1=p1.pkg.tar.gz&size1=123&md5sum1=abcd\
        name2=p2.pkg.tar.gz&size2=3&md5sum2=def1
    s: numpkgs=2&name1=p1.pkg.tar.gz&size1=119&\
        name2=p2.pkg.tar.gz&size2=0 (*)

    (*) NOTE: The server will reply back to the client how many
        packages it has already received and its local file size.
        This way, the client can resume an upload.  In the example
        above, the server still needs the last four (123-119) bytes
        for the first package, and that it has no part of the
        second package.  The client would then begin sending the
        last four bytes from the first package (p1.pkg.tar.gz) and
        then follow it with the full second package (p2.pkg.tar.gz).
        The data would be sent as a continuous chunk of data.  The
        server will then need to track which bytes belong to which
        package.

  else FAIL:
    c: -spits out error message on stderr to user-


  ==> after upload completes
  The server should verify the integrity of the uploaded packages
  by doing an md5sum on each and sending the info back to the client
  for comparison.  After sending the message, the server waits for
  the 'ack' message from the client and then closes the connection.

  s: np=2&m1=PASS&m2=FAIL
  c: ack

  The client replies with the 'ack' and then closes its connection
  to the server.  It then reports the PASS/FAIL status of each
  package's upload attempt.

  NOTE: If the upload fails (client connection dies), the server
  keeps any data it has received in order to support resuming an
  upload.  However, if the client uploads all data, and the server
  successully reads all data and the final MD5 fails, the server
  deletes the failed package.


Terms/definitions:
======================
TU - No change (trusted by the community, if anyone asks what trust
     means)
TUR - renamed to Arch User-community Repo (AUR) (so we can use -u for
      versions)
Incoming - renamed to "Unsupported"

