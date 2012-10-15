from . import util
from functools import partial
from gevent.socket import socket
from itertools import count
from itertools import groupby
from operator import attrgetter
from statlib import stats
from supervisor.xmlrpc import SupervisorTransport
import gevent
import logging
import psutil
import stuf
import time
import xmlrpclib

logger = logging.getLogger(__name__)


class Emitter(util.Actor):
    """
    A actor that receives messages and sends them to carbon
    """
    def __init__(self, host='127.0.0.1', port=2003):
        self.host = host
        self.port = port
        self.sock = socket()
        util.Actor.__init__(self)

    def begin(self):
        self.sock.connect((self.host, self.port))

    def recv(self, message):
        if isinstance(message, list):
            message = "\n".join(message)
        if not message.endswith('\n'):
            message = message + '\n'
        self.sock.sendall(message)
            

class Collector(gevent.Greenlet):
    """
    Generic base class for an ojbect that feeds lists to an emitter queue
    """
    def __init__(self, outbox, prefix="server.sys", period=0.5):
        self.period = period
        self.outbox = outbox
        self.prefix = prefix
        gevent.Greenlet.__init__(self)    

    def begin(self):
        """
        stub for anything that should wait until the greenlet runs in earnest
        """
        pass

    def send(self, payload):
        self.outbox.put(payload)

    def _run(self):
        self.begin()
        self.running = True
        while self.running:
            self.send(list(self.report(self.prefix)))
            gevent.sleep(self.period)


class SysCollector(Collector):

    @staticmethod
    def report(prefix, tmplt="{1}.{2} {3} {0}"):
        now = time.time()
        fmt = partial(tmplt.format, now, prefix)
        yield fmt('cpu_percent', psutil.cpu_percent())

        cput = psutil.cpu_times()
        yield fmt('cput_idle', cput.idle)
        yield fmt('cput_user', cput.user)
        yield fmt('cput_sys', cput.system)

        swap = psutil.swap_memory()
        yield fmt('swap_percent', swap.percent)
        yield fmt('swap_free', swap.free)
        yield fmt('swap_used', swap.free)

        virt = psutil.virtual_memory()
        yield fmt('mem_available', virt.available)
        yield fmt('mem_percent', virt.percent) 


class MetricFormatter(object):
    op = stuf.stuf(mem_perc=attrgetter('memory_percent'),
                   cpu_perc=attrgetter('cpu_percent'),
                   cnxs=attrgetter('connections'),
                   time=attrgetter('time'))

    def amf(self, values, attr, func=None):
        """
        Attribute mean filtered

        For a list of objects, filter out an object with a attr value
        of None, and return mean if any values are left.
        """
        getter = self.op[attr]
        res = (getter(x) for x in values if not  getter(x) is None)
        if func:
            res = (func(x) for x in res if not func(x) is None)
        res = tuple(res)
        res = res and stats.mean(res) or 0.0
        return res
        
    def out(self, prefix, appuser, proclist, tmplt="{1}.{2}.{3} {4} {0}", op=op):
        """
        returns an iterable of metrics for a user and list of procs
        """
        proclist = [x for x in proclist]
        amf = partial(self.amf, proclist)
        fmt = partial(tmplt.format, amf('time'), prefix, appuser)
        yield fmt('procs_running', len(tuple(proclist)))
        yield fmt('cpu_percent', amf('cpu_perc'))
        yield fmt('memory_percent', amf('mem_perc'))
        yield fmt('connections', amf('cnxs', func=len))


class PIDCollector(Collector):
    """
    A collector that focusses on the pids inside supervisor
    """
    limit = 5
    metric_out = staticmethod(MetricFormatter().out)
    get_username = attrgetter('username')

    @property
    def pid_info(self):
        """
        Return a data structure for every process
        """
        if self.limit:
            counter = count(1)
            
        for proc in reversed(tuple(psutil.process_iter())):
            if self.limit and next(counter) > self.limit:
                raise StopIteration('Limit reached')
            yield self.to_proc_info(proc)

    @staticmethod
    def to_proc_info(proc, **kw):
        raw = proc.as_dict()
        raw['time'] = time.time()
        raw.update(kw)
        out = stuf.stuf(raw)
        return out

    @staticmethod
    def procs_by_user(proclist, keyfunc=get_username):
        grouped = groupby(sorted(proclist, key=keyfunc), keyfunc)
        return ((user, [x for x in procs]) for user, procs in grouped)

    def report(self, prefix):
        proclist = list(self.pid_info)
        yield list(self.metric_out(prefix, 'all', proclist))
        by_user = self.procs_by_user(proclist)
        for user, procs in by_user:
            yield list(self.metric_out(prefix, user, procs))

    def send(self, payload):
        [self.outbox.put(sub) for sub in payload]
            


class SuperPIDCollector(PIDCollector):
    """
    PIDCollector constrained to a supervisor
    """
    def __init__(self, outbox, url='unix:///var/run//supervisor.sock',
                 prefix="server.sys", period=0.5):
        Collector.__init__(self, outbox, prefix, period)
        self.url = url

    def begin(self):
        self.xmlrpc = xmlrpclib.ServerProxy('http://127.0.0.1', # will always be local
                                            transport=SupervisorTransport(None, None, self.url))
        self.sapi = self.xmlrpc.supervisor    

    @property
    def pid_info(self):
        """
        Return process info for only processes managed by supervisorctl
        """
        procinfo = ((pi['pid'], pi['name'], pi['now'] - pi['start']) \
                    for pi in self.sapi.getAllProcessInfo())

        for pid, name, uptime in procinfo:
            try:
                proc = psutil.Process(pid)
                yield self.to_proc_info(proc, super_name=name, super_uptime=uptime)
            except psutil.NoSuchProcess(pid):
                logger.debug("NoSuchProcess(%s)", pid)
                continue

            


