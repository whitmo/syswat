from gevent.server import StreamServer
from gevent import Greenlet
from gevent.queue import Queue


class Actor(Greenlet):
    
    def __init__(self):
        self.inbox = Queue()
        Greenlet.__init__(self)

    def recv(self, message):
        raise NotImplementedError

    def begin(self):
        pass
    
    def _run(self):
        self.running = True
        self.begin()
        while self.running:
            message = self.inbox.get()
            self.recv(message)


class FakeCarbon(StreamServer):

    def __init__(self, port):
        StreamServer.__init__(self, ('0.0.0.0', port), self.handler)

    @staticmethod
    def handler(socket, address):
        print('FakeCarbon: connection from %s:%s' % address)

        fileobj = socket.makefile()
        while True:
            line = fileobj.readline()
            if not line:
                print("client disconnected")
                break
            if line.strip().lower() == 'quit':
                print("client quit")
                break
            fileobj.write(line)
            fileobj.flush()
            print(line)
