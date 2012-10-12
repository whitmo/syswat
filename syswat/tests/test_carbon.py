from mock import Mock
import psutil
import unittest


def test_metric_out():
    proc = psutil.Process(psutil.get_pid_list()[0])
    from syswat.carbon import PIDCollector
    info = PIDCollector.to_proc_info(proc)
    out = list(PIDCollector.metric_out('test', 'test', [info]))
    assert len(out) == 4
    assert len(out[0].split(' ')) == 3
    assert out[0].startswith('test.test')


class TestPIDCollector(unittest.TestCase):

    def make_pidc(self):
        from syswat.carbon import PIDCollector
        ob = self.outbox = Mock()
        return PIDCollector(ob)
        
    def test_pidc_returns_at_least_2_data_group(self):
        """
        PIDCollector returns at least to data groups (all & user)
        """
        pc = self.make_pidc()
        out = list(pc.report('test'))
        assert len(out) >= 2, len(out) 

    def test_pid_out(self):
        pc = self.make_pidc()
        out = list(pc.report('test'))
        #pprint(out)
        proc_cnts = dict(group[0].split(' ')[:2] for group in out)
        total = proc_cnts.pop('test.all.procs_running')
        data_total = sum(int(x) for x in proc_cnts.values())
        assert int(total) == data_total, "%s != %s" %(total, data_total)

        
