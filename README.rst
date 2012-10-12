========
 syswat
========

A simple stats collector that streams collected stats to carbon.

On a stock ubuntu install w/ the supervisor package installed, `cwatd`
will stream the following stats to carbon.

Systemwide stats::

 node.HOST.cpu_percent 3.5 1350070515.95
 node.HOST.cput_idle 700504.54 1350070515.95
 node.HOST.cput_user 36357.82 1350070515.95
 node.HOST.cput_sys 23021.61 1350070515.95
 node.HOST.swap_percent 0.0 1350070515.95
 node.HOST.swap_free 67108864 1350070515.95
 node.HOST.swap_used 67108864 1350070515.95
 node.HOST.mem_available 7819300864 1350070515.95
 node.HOST.mem_percent 54.5 1350070515.95

Cummulative means for all pids managed by a supervisord::

 node.HOST.all.procs_running 5 1350070515.98
 node.HOST.all.cpu_percent 0.0 1350070515.98
 node.HOST.all.memory_percent 0.126957893372 1350070515.98
 node.HOST.all.connections 1.0 1350070515.98

Per user means for all pids managed by a supervisord::

 node.HOST.bob.procs_running 5 1350070515.98
 node.HOST.bob.cpu_percent 0.0 1350070515.98
 node.HOST.bob.memory_percent 0.126957893372 1350070515.98
 node.HOST.bob.connections 1.0 1350070515.98



