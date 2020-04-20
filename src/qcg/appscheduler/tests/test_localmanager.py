import pytest

from os.path import exists, join


from qcg.appscheduler.api.manager import LocalManager
from qcg.appscheduler.api.job import Jobs
from qcg.appscheduler.utils.auxdir import find_single_aux_dir


def test_local_manager_resources(tmpdir):
    cores = 4

   # switch on debugging (by default in api.log file)
    m = LocalManager(['--wd', str(tmpdir), '--nodes', str(cores)], {'wdir': str(tmpdir)})

    res = m.resources()

    assert all(('totalNodes' in res, 'totalCores' in res, res['totalNodes'] == 1, res['totalCores'] == cores))

    m.finish()
    m.stopManager()
    m.cleanup()


def test_local_manager_resources_nodes(tmpdir):
    nodes = 2
    cores_per_node = 3
    res_desc = ','.join([str(cores_per_node) for i in range(nodes)])

   # switch on debugging (by default in api.log file)
    m = LocalManager(['--wd', str(tmpdir), '--nodes', res_desc], {'wdir': str(tmpdir)})

    res = m.resources()

    assert all(('totalNodes' in res, 'totalCores' in res, res['totalNodes'] == 2, res['totalCores'] == cores_per_node * nodes))

    m.finish()
    m.stopManager()
    m.cleanup()


def test_local_manager_submit_simple(tmpdir):
    cores = 4

    # switch on debugging (by default in api.log file)
    m = LocalManager(['--wd', str(tmpdir), '--nodes', str(cores)], {'wdir': str(tmpdir)})

    try:
        res = m.resources()

        assert all(('totalNodes' in res, 'totalCores' in res, res['totalNodes'] == 1, res['totalCores'] == cores))

        ids = m.submit(Jobs().
            add(name='host', exec='/bin/hostname', args=[ '--fqdn' ], stdout='host.stdout').
            add(name='date', exec='/bin/date', stdout='date.stdout', numCores={ 'exact': 2 })
            )

        assert len(m.list()) == 2

        m.wait4(ids)

        jinfos = m.info(ids)

        assert all(('jobs' in jinfos,
                    len(jinfos['jobs'].keys()) == 2,
                    'host' in jinfos['jobs'],
                    'date' in jinfos['jobs'],
                    jinfos['jobs']['host'].get('data', {}).get('status', '') == 'SUCCEED',
                    jinfos['jobs']['date'].get('data', {}).get('status', '') == 'SUCCEED'))

        aux_dir = find_single_aux_dir(str(tmpdir))

        assert all((exists(tmpdir.join('.qcgpjm-client', 'api.log')),
                    exists(join(aux_dir, 'service.log')),
                    exists(tmpdir.join('host.stdout')),
                    exists(tmpdir.join('date.stdout'))))
    finally:
        m.finish()
        m.stopManager()
        m.cleanup()


def test_local_manager_wait4all(tmpdir):
    cores = 4

   # switch on debugging (by default in api.log file)
    m = LocalManager(['--wd', str(tmpdir), '--nodes', str(cores)], {'wdir': str(tmpdir)})

    res = m.resources()

    assert all(('totalNodes' in res, 'totalCores' in res, res['totalNodes'] == 1, res['totalCores'] == cores))

    ids = m.submit(Jobs().
        add(name='host', exec='/bin/hostname', args=[ '--fqdn' ], stdout='host.stdout').
        add(name='date', exec='/bin/date', stdout='date.stdout', numCores={ 'exact': 2 })
        )

    assert len(m.list()) == 2

    m.wait4all()

    jinfos = m.info(ids)

    assert all(('jobs' in jinfos,
                len(jinfos['jobs'].keys()) == 2,
                'host' in jinfos['jobs'],
                'date' in jinfos['jobs'],
                jinfos['jobs']['host'].get('data', {}).get('status', '') == 'SUCCEED',
                jinfos['jobs']['date'].get('data', {}).get('status', '') == 'SUCCEED'))

    aux_dir = find_single_aux_dir(str(tmpdir))

    assert all((exists(tmpdir.join('.qcgpjm-client', 'api.log')),
                exists(join(aux_dir, 'service.log')),
                exists(tmpdir.join('host.stdout')),
                exists(tmpdir.join('date.stdout'))))

    m.finish()
    m.stopManager()
    m.cleanup()

