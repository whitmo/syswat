import gevent

def test_actor():
    from syswat.util import Actor
    class ActorTest(Actor):
        state = []
        def recv(self, message):
            self.state.append(message)
    at = ActorTest()
    at.start()
    at.inbox.put('WAT')
    gevent.sleep(0.1)
    assert 'WAT' in at.state
