#!/usr/bin/python
# -*- coding: utf-8 -*-
#

test = 2

if test == 0:
    
    from subprocess import Popen, PIPE
    
    p1 = Popen(["grep", "-v", "not"], stdin=PIPE, stdout=PIPE) # bufsize does not change the outcome
    #p2 = Popen(["cut", "-c", "1-10"], stdin=p1.stdout, stdout=PIPE, close_fds=True)
    p1.stdin.write('Hello World\n' * 20000)
    p1.stdin.close()
    p1.poll()
    #result = p2.stdout.read() 
    print "Got the output, buffer not exceeded."
    
elif test == 1:
    
    import pexpect
    
    p1 = pexpect.spawn('grep -v not', maxread=1)
    p1.send('Hello World\n' * 10000)
    print "Is alive:", p1.isalive()
    
elif test == 2:
    
    from subprocess import Popen, PIPE
    
    p = Popen(["python", '-c', 'import sys; sys.stdout.write(\'Hello World\\n\'* 200000)'], stdin=PIPE, stdout=PIPE)
    print p.poll()
    o,e = p.communicate()
    print "Got the output, buffer not exceeded."
    
else:
    
    import sys
    sys.stdout.write('Hello World\n' * 20000)
