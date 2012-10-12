from gevent import monkey
monkey.patch_all()

from . import carbon
from functools import partial
import argparse
import gevent
import logging
import platform
import sys

logger = logging.getLogger(__name__)


class CarbonWatD(object):
    """
    A bag for holding our emitters and our collectors
    """
    cli = argparse.ArgumentParser(description='Carbon WatD reports to Carbon on'
                                  ' what\'s happening on a node')
    cli.add_argument("--chost", default='127.0.0.1')
    cli.add_argument("--cport", default=2003)
    cli.add_argument("--supervisor_uri", "-s", default='unix:///var/run//supervisor.sock')
    cli.add_argument("--cprefix_format", default="{toplevel}.{hostname}")
    cli.add_argument("--ctoplevel", default='node')
    cli.add_argument("--fauxcarbon", "-f", action="store_true", default=False)

    emitter_class = carbon.Emitter
    syscol_class = carbon.SysCollector
    spidc_class = carbon.SuperPIDCollector

    def __init__(self, mkcol=[], mkemit=None):
        self.mkcol = mkcol
        self.mkemit = mkemit
        self.greenlets = []

    def run(self):
        e = self.mkemit()
        self.greenlets.extend(cf(e.inbox) for cf in self.mkcol)
        self.greenlets.append(e)
        [g.start() for g in self.greenlets]
        gevent.joinall(list(self.greenlets))

    def logging_setup(self, loglevel=logging.INFO):
        logging.basicConfig(level=loglevel,
                            format='[%(levelname)s] %(message)s')

    @classmethod
    def format_map(cls, **kw):
        base = dict(hostname=platform.node())
        base.update(kw)
        return base

    @classmethod
    def faux_carbon(cls, port):
        from . import util
        fc = util.FakeCarbon(port)
        return fc
    
    @classmethod
    def main(cls, args=None):
        """
        The script entrypoint for the daemon
        """
        if args is None:
            args = sys.argv[1:]
        args = cls.cli.parse_args(args)

        prefix = args.cprefix_format.format(**cls.format_map(toplevel=args.ctoplevel))
        mk_syscol = partial(cls.syscol_class, prefix=prefix)
        mk_spidcol = partial(cls.spidc_class,
                             url=args.supervisor_uri, prefix=prefix)

        mk_emitter = partial(cls.emitter_class, args.chost, args.cport)

        watd = cls([mk_syscol, mk_spidcol], mk_emitter)
        if args.fauxcarbon:
            logger.info("starting fake carbon server %s:%s", args.chost, args.cport)
            srv = cls.faux_carbon(args.cport)
            srv.start()
            
        logger.info("cwatd emitting to %s:%s", args.chost, args.cport)
        watd.run()


carbon_main = CarbonWatD.main

