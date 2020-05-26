import pytest
import json

from os.path import exists, join

from qcg.appscheduler.api.manager import LocalManager
from qcg.appscheduler.api.errors import ConnectionError
from qcg.appscheduler.request import ControlReq, SubmitReq, JobStatusReq, JobInfoReq, CancelJobReq, RemoveJobReq
from qcg.appscheduler.request import ListJobsReq, ResourcesInfoReq, FinishReq, StatusReq, NotifyReq, RegisterReq
from qcg.appscheduler.api.job import Jobs
from qcg.appscheduler.tests.utils import find_single_aux_dir


def test_request_general(tmpdir):
    m = LocalManager(['--wd', str(tmpdir), '--nodes', 2], {'wdir': str(tmpdir)})

    try:
        # missing 'request' element
        with pytest.raises(ConnectionError, match=r".*Invalid request.*"):
            m.sendRequest({ 'notARequestElement': 'some value'})

        # unknown 'request'
        with pytest.raises(ConnectionError, match=r".*Unknown request name.*"):
            m.sendRequest({ 'request': 'some unknown request'})
    finally:
        m.finish()


def test_request_control(tmpdir):
    # raw control request test
    req = ControlReq({'request': 'control', 'command': 'finishAfterAllTasksDone'})
    req_clone = ControlReq(json.loads(req.toJSON()))
    assert req.toJSON() == req_clone.toJSON()

    m = LocalManager(['--wd', str(tmpdir), '--nodes', 2], {'wdir': str(tmpdir)})

    try:
        # missing 'command' for control request
        with pytest.raises(ConnectionError, match=r".*Wrong control request - missing command.*"):
            m.sendRequest({ 'request': 'control'})

        # unknown 'command' for control request
        with pytest.raises(ConnectionError, match=r".*Wrong control request - unknown command.*"):
            m.sendRequest({ 'request': 'control', 'command': 'unknown command'})

        # finishAfterAllTasksDone 'command' for control request
        res =  m.sendRequest({ 'request': 'control', 'command': 'finishAfterAllTasksDone'})
        assert all((res.get('code', -1) == 0, res.get('message', None) == 'finishAfterAllTasksDone command accepted'))
    finally:
        try:
            # if finishAfterAllTasksDone has been sent we might get error 'Finish request already requested'
            m.finish()
        except Exception:
            pass

        m.wait4ManagerFinish()
        m.cleanup()


def test_request_submit(tmpdir):
    # raw submit request test
    req = SubmitReq({'request': 'submit', 'jobs': [ {'name': 'job1',
                                                     'execution': {'exec': '/bin/date', 'args': ['1', '2']}},
                                                    {'name': 'job2',
                                                     'execution': {'script': 'date'},
                                                     'resources': { 'numCores': {'exact': 1}}}
                                                    ]})
    req_clone = SubmitReq(json.loads(req.toJSON()))
    assert req.toJSON() == req_clone.toJSON()

    m = LocalManager(['--wd', str(tmpdir), '--nodes', 2], {'wdir': str(tmpdir)})

    try:
        # missing 'jobs' for submit request
        with pytest.raises(ConnectionError, match=r".*Wrong submit request - missing jobs data.*"):
            m.sendRequest({ 'request': 'submit'})

        # wrong 'jobs' data format for submit request
        with pytest.raises(ConnectionError, match=r".*Wrong submit request - missing jobs data.*"):
            m.sendRequest({ 'request': 'submit', 'jobs': None })

        # wrong 'jobs' data format for submit request
        with pytest.raises(ConnectionError, match=r".*Wrong submit request - missing jobs data.*"):
            m.sendRequest({ 'request': 'submit', 'jobs': 'not a list' })

        # wrong 'jobs' data format for submit request
        with pytest.raises(ConnectionError, match=r".*Wrong submit request - wrong job data.*"):
            m.sendRequest({ 'request': 'submit', 'jobs': [ 'not a dictionary' ] })

        # missing job's name
        with pytest.raises(ConnectionError, match=r".*Missing name in job description.*"):
            m.sendRequest({ 'request': 'submit', 'jobs': [ { 'execution': '/bin/date' } ] })

        # missing execution element
        with pytest.raises(ConnectionError, match=r".*Missing execution element in job description.*"):
            m.sendRequest({ 'request': 'submit', 'jobs': [ { 'name': 'date' } ] })

        # wrong iterations format
        with pytest.raises(ConnectionError, match=r".*Wrong format of iteration directive: not a dictionary.*"):
            m.sendRequest({ 'request': 'submit', 'jobs': [ { 'name': 'date',
                                                             'execution': { 'exec': '/bin/date' },
                                                             'iteration': 'not a list' } ] })

        # wrong iterations format
        with pytest.raises(ConnectionError, match=r".*Wrong format of iteration directive: start index larger then stop one.*"):
            m.sendRequest({ 'request': 'submit', 'jobs': [ { 'name': 'date',
                                                             'execution': { 'exec': '/bin/date' },
                                                             'iteration': { 'start': 2, 'stop': 1 } } ] })

    finally:
        m.finish()


def test_request_job_status(tmpdir):
    # raw jobStatus request test
    req = JobStatusReq({'request': 'jobStatus', 'jobNames': ['job1', 'job1:2', 'job3']})
    req_clone = JobStatusReq(json.loads(req.toJSON()))
    assert req.toJSON() == req_clone.toJSON()

    m = LocalManager(['--wd', str(tmpdir), '--nodes', 2], {'wdir': str(tmpdir)})

    try:
        # missing 'jobNames' for jobStatus request
        with pytest.raises(ConnectionError, match=r".*Wrong job status request - missing job names.*"):
            m.sendRequest({ 'request': 'jobStatus'})

        # wrong format of 'jobNames' element
        with pytest.raises(ConnectionError, match=r".*Wrong job status request - missing job names.*"):
            m.sendRequest({ 'request': 'jobStatus', 'jobNames': 'not a list' })

        # wrong format of 'jobNames' element - empty list
        with pytest.raises(ConnectionError, match=r".*Wrong job status request - missing job names.*"):
            m.sendRequest({ 'request': 'jobStatus', 'jobNames': [ ] })
    finally:
        m.finish()


def test_request_job_info(tmpdir):
    # raw jobInfo request test
    req = JobInfoReq({'request': 'jobInfo', 'jobNames': ['job1', 'job2'], 'params': { 'withChilds': True }})
    req_clone = JobInfoReq(json.loads(req.toJSON()))
    assert req.toJSON() == req_clone.toJSON()

    req = JobInfoReq({'request': 'jobInfo', 'jobNames': ['job1', 'job2'] })
    req_clone = JobInfoReq(json.loads(req.toJSON()))
    assert req.toJSON() == req_clone.toJSON()

    m = LocalManager(['--wd', str(tmpdir), '--nodes', 2], {'wdir': str(tmpdir)})

    try:
        # missing 'jobNames' for jobInfo request
        with pytest.raises(ConnectionError, match=r".*Wrong job info request - missing job names.*"):
            m.sendRequest({ 'request': 'jobInfo'})

        # wrong format of 'jobNames' element
        with pytest.raises(ConnectionError, match=r".*Wrong job info request - missing job names.*"):
            m.sendRequest({ 'request': 'jobInfo', 'jobNames': 'not a list' })

        # wrong format of 'jobNames' element - empty list
        with pytest.raises(ConnectionError, match=r".*Wrong job info request - missing job names.*"):
            m.sendRequest({ 'request': 'jobInfo', 'jobNames': [ ] })
    finally:
        m.finish()


def test_request_cancel_job(tmpdir):
    # raw cancelJob request test
    req = CancelJobReq({'request': 'cancelJob', 'jobNames': ['job1', 'job2']})
    req_clone = CancelJobReq(json.loads(req.toJSON()))
    assert req.toJSON() == req_clone.toJSON()

    m = LocalManager(['--wd', str(tmpdir), '--nodes', 2], {'wdir': str(tmpdir)})

    try:
        # missing 'jobNames' for jobInfo request
        with pytest.raises(ConnectionError, match=r".*Wrong cancel job request - missing job names.*"):
            m.sendRequest({ 'request': 'cancelJob'})

        # wrong format of 'jobNames' element
        with pytest.raises(ConnectionError, match=r".*Wrong cancel job request - missing job names.*"):
            m.sendRequest({ 'request': 'cancelJob', 'jobNames': 'not a list' })

        # wrong format of 'jobNames' element - empty list
        with pytest.raises(ConnectionError, match=r".*Wrong cancel job request - missing job names.*"):
            m.sendRequest({ 'request': 'cancelJob', 'jobNames': [ ] })
    finally:
        m.finish()


def test_request_remove_job(tmpdir):
    # raw removeJob request test
    req = RemoveJobReq({'request': 'removeJob', 'jobNames': ['job1', 'job2']})
    req_clone = RemoveJobReq(json.loads(req.toJSON()))
    assert req.toJSON() == req_clone.toJSON()

    m = LocalManager(['--wd', str(tmpdir), '--nodes', 2], {'wdir': str(tmpdir)})

    try:
        # missing 'jobNames' for jobInfo request
        with pytest.raises(ConnectionError, match=r".*Wrong remove job request - missing job names.*"):
            m.sendRequest({ 'request': 'removeJob'})

        # wrong format of 'jobNames' element
        with pytest.raises(ConnectionError, match=r".*Wrong remove job request - missing job names.*"):
            m.sendRequest({ 'request': 'removeJob', 'jobNames': 'not a list' })

        # wrong format of 'jobNames' element - empty list
        with pytest.raises(ConnectionError, match=r".*Wrong remove job request - missing job names.*"):
            m.sendRequest({ 'request': 'removeJob', 'jobNames': [ ] })
    finally:
        m.finish()


def test_request_list_jobs(tmpdir):
    # raw listJobs request test
    req = ListJobsReq({'request': 'listJobs'})
    req_clone = ListJobsReq(json.loads(req.toJSON()))
    assert req.toJSON() == req_clone.toJSON()


def test_request_resources_info(tmpdir):
    # raw resourcesInfo request test
    req = ResourcesInfoReq({'request': 'resourcesInfo'})
    req_clone = ResourcesInfoReq(json.loads(req.toJSON()))
    assert req.toJSON() == req_clone.toJSON()

def test_request_finish(tmpdir):
    # raw finish request test
    req = FinishReq({'request': 'finish'})
    req_clone = FinishReq(json.loads(req.toJSON()))
    assert req.toJSON() == req_clone.toJSON()

def test_request_status(tmpdir):
    # raw status request test
    req = StatusReq({'request': 'status'})
    req_clone = StatusReq(json.loads(req.toJSON()))
    assert req.toJSON() == req_clone.toJSON()

def test_request_notify(tmpdir):
    # raw notify request test
    req = NotifyReq({'request': 'notify', 'entity': 'job', 'params': { 'name': 'j1', 'state': 'FINISHED',
                                                                       'attributes': { 'a1': True }}})
    req_clone = NotifyReq(json.loads(req.toJSON()))
    assert req.toJSON() == req_clone.toJSON()

    m = LocalManager(['--wd', str(tmpdir), '--nodes', 2], {'wdir': str(tmpdir)})

    try:
        # missing 'entity' for notify request
        with pytest.raises(ConnectionError, match=r".*Wrong notify request - missing/unknown entity.*"):
            m.sendRequest({ 'request': 'notify'})

        # unknown 'entity' for notify request
        with pytest.raises(ConnectionError, match=r".*Wrong notify request - missing/unknown entity.*"):
            m.sendRequest({ 'request': 'notify', 'entity': 'task' })

        # missing params
        with pytest.raises(ConnectionError, match=r".*Wrong notify request - missing register parameters.*"):
            m.sendRequest({ 'request': 'notify', 'entity': 'job' })

        # missing key params
        with pytest.raises(ConnectionError, match=r".*Wrong notify request - missing key notify parameters.*"):
            m.sendRequest({ 'request': 'notify', 'entity': 'job', 'params': { 'name': 'j1' } })

        # missing key params
        with pytest.raises(ConnectionError, match=r".*Wrong notify request - missing key notify parameters.*"):
            m.sendRequest({ 'request': 'notify', 'entity': 'job', 'params': { 'name': 'j1', 'state': 'FINISHED' } })

        # missing key params
        with pytest.raises(ConnectionError, match=r".*Wrong notify request - missing key notify parameters.*"):
            m.sendRequest({ 'request': 'notify', 'entity': 'job', 'params': { 'state': 'FINISHED',
                                                                              'attributes': 'a1' } })

    finally:
        m.finish()


def test_request_register(tmpdir):
    # raw register request test
    req = RegisterReq({'request': 'register', 'entity': 'manager', 'params': { 'id': 'm1',
                                                                               'address': '0.0.0.0',
                                                                               'resources': { 'nodes': 2 }}})
    req_clone = RegisterReq(json.loads(req.toJSON()))
    assert req.toJSON() == req_clone.toJSON()

    m = LocalManager(['--wd', str(tmpdir), '--nodes', 2], {'wdir': str(tmpdir)})

    try:
        # missing 'entity' for register request
        with pytest.raises(ConnectionError, match=r".*Wrong register request - missing/unknown entity.*"):
            m.sendRequest({ 'request': 'register'})

        # unknown 'entity' for register request
        with pytest.raises(ConnectionError, match=r".*Wrong register request - missing/unknown entity.*"):
            m.sendRequest({ 'request': 'register', 'entity': 'job' })

        # missing params
        with pytest.raises(ConnectionError, match=r".*Wrong register request - missing register parameters.*"):
            m.sendRequest({ 'request': 'register', 'entity': 'manager' })

        # missing key params
        with pytest.raises(ConnectionError, match=r".*Wrong register request - missing key register parameters.*"):
            m.sendRequest({ 'request': 'register', 'entity': 'manager', 'params': { 'id': 'm1' } })

        # missing key params
        with pytest.raises(ConnectionError, match=r".*Wrong register request - missing key register parameters.*"):
            m.sendRequest({ 'request': 'register', 'entity': 'manager', 'params': { 'id': 'm1',
                                                                                    'address': '0.0.0.0' } })

        # missing key params
        with pytest.raises(ConnectionError, match=r".*Wrong register request - missing key register parameters.*"):
            m.sendRequest({ 'request': 'register', 'entity': 'manager', 'params': { 'resources': { 'nodes': 1 },
                                                                                    'address': '0.0.0.0' } })

    finally:
        m.finish()