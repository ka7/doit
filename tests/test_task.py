import os
import sys, StringIO

import nose

from doit import logger
from doit.task import BaseTask, CmdTask, PythonTask
from doit.task import InvalidTask, TaskError, TaskFailed

class TestBaseTask(object):

    # dependency must be a sequence. give proper error message when anything 
    # else is used.
    def test_dependencyNotSequence(self):
        filePath = os.path.abspath(__file__+"/../"+"data/dependency1")
        ff = open(filePath,"w")
        ff.write("part1")
        ff.close()
        nose.tools.assert_raises(InvalidTask,BaseTask,
                                 "Task X","taskcmd",dependencies=filePath)

    def test_title(self):
        t = BaseTask("MyName","MyAction")
        assert "MyName => MyAction" == t.title(), t.title()

    # BaseTask must be subclassed and define an execute method
    def test_mustSubclass(self):
        t = BaseTask("MyName","MyAction")
        nose.tools.assert_raises(InvalidTask,t.execute)



class TestCmdTask(object):

    # if nothing is raised it is successful
    def test_success(self):
        t = CmdTask("taskX",["ls","-1"])
        t.execute()

    def test_error(self):
        t = CmdTask("taskX","invalid_command asdf")
        nose.tools.assert_raises(TaskError,t.execute)

    def test_failure(self):
        t = CmdTask("taskX",["ls","I dont exist"])
        nose.tools.assert_raises(TaskFailed,t.execute)

    def test_str(self):
        t = CmdTask("taskX",["ls","-1"])
        assert "Cmd: ls -1" == str(t), str(t)

    def test_repr(self):
        t = CmdTask("taskX",["ls","-1"])
        assert "<CmdTask: taskX - 'ls -1'>" == repr(t), repr(t)





# it is also possible to pass any python callable
class TestPythonTask(object):

    def test_success(self):
        def success_sample():return True
        t = PythonTask("taskX",success_sample)
        t.execute() # nothing raised it was successful

    def test_error(self):
        def error_sample(): raise Exception("asdf")
        t = PythonTask("taskX",error_sample)
        nose.tools.assert_raises(TaskError,t.execute)

    def test_fail(self):
        def fail_sample():return False
        t = PythonTask("taskX",fail_sample)
        nose.tools.assert_raises(TaskFailed,t.execute)

    # any callable should work, not only functions
    def test_nonFunction(self):
        class CallMe:
            def __call__(self):
                return False

        t = PythonTask("taskX",CallMe())
        nose.tools.assert_raises(TaskFailed,t.execute)

    # helper to test callable with parameters
    def _func_par(self,par1,par2,par3=5):
        if par1 == par2 and par3 > 10:
            return True
        else:
            return False
        
    def test_functionParameters(self):
        t = PythonTask("taskX",self._func_par,
                       args=(2,),kwargs={'par2':2,'par3':25})
        t.execute()

    def test_functionParametersFail(self):
        t = PythonTask("taskX",self._func_par,
                       args=(2,3),kwargs={'par3':25})
        nose.tools.assert_raises(TaskFailed,t.execute)

    def test_str(self):
        def str_sample(): return True
        t = PythonTask("taskX",str_sample)
        assert "Python: function str_sample" == str(t), "'%s'"%str(t)

    def test_repr(self):
        def repr_sample(): return True
        t = PythonTask("taskX",repr_sample)
        assert "<PythonTask: taskX - '%s'>"%repr(repr_sample) == repr(t)



##############################################
class TestCmdVerbosityStderr(object):
    def setUp(self):
        # capture stderr
        self.oldErr = sys.stderr
        sys.stderr = StringIO.StringIO()
        logger.clear("stderr")

    def tearDown(self):
        sys.stderr.close()
        sys.stderr = self.oldErr

    # Capture stderr
    def test_capture(self):
        BaseTask.CAPTURE_ERR = True
        t = CmdTask("taskX",["ls","-2"])
        nose.tools.assert_raises(TaskFailed,t.execute)
        assert "" == sys.stderr.getvalue()
        logger.flush('stderr',sys.stderr)
        assert "ls: invalid option -- 2\nTry `ls --help' for more information.\n" == sys.stderr.getvalue(),sys.stderr.getvalue()

        
    # Do not capture stderr 
    #     
    # i dont know how to test this (in a reasonable easy way).
    # the stream is sent straight to the parent process from doit.
    def test_noCapture(self):
        BaseTask.CAPTURE_ERR = False
        t = CmdTask("taskX",["ls","-2"])
        nose.tools.assert_raises(TaskFailed,t.execute)
        assert "" == sys.stderr.getvalue(),sys.stderr.getvalue()
        logger.flush('stderr',sys.stderr)
        assert "" == sys.stderr.getvalue(),sys.stderr.getvalue()



class TestCmdVerbosityStdout(object):
    def setUp(self):
        # capture stdout
        self.oldOut = sys.stdout
        sys.stdout = StringIO.StringIO()
        logger.clear("stdout")

    def tearDown(self):
        sys.stdout.close()
        sys.stdout = self.oldOut

    # Capture stdout
    def test_capture(self):
        BaseTask.CAPTURE_OUT = True
        t = CmdTask("taskX",["echo","hi from stdout"])
        t.execute()
        assert "" == sys.stdout.getvalue()
        logger.flush('stdout',sys.stdout)
        assert "hi from stdout\n" == sys.stdout.getvalue(),sys.stdout.getvalue()

        
    # Do not capture stdout 
    #     
    # i dont know how to test this (in a reasonable easy way).
    # the stream is sent straight to the parent process from doit.
    def test_noCapture(self):
        BaseTask.CAPTURE_OUT = False
        t = CmdTask("taskX",["echo","hi from stdout"])
        t.execute()
        assert "" == sys.stdout.getvalue(),sys.stdout.getvalue()
        logger.flush('stdout',sys.stdout)
        assert "" == sys.stdout.getvalue(),sys.stdout.getvalue()





class TestPythonVerbosityStderr(object):
    def setUp(self):
        # capture stderr
        self.oldErr = sys.stderr
        sys.stderr = StringIO.StringIO()
        logger.clear("stderr")

    def tearDown(self):
        sys.stderr.close()
        sys.stderr = self.oldErr

    def write_and_error(self):
        sys.stderr.write("this is stderr E\n")
        raise Exception("Hi i am an exception")
        
    def write_and_success(self):
        sys.stderr.write("this is stderr S\n")
        return True

    def write_and_fail(self):
        sys.stderr.write("this is stderr F\n")
        return False

    ##### Capture stderr 
    #
    # success 
    def test_captureSuccess(self):
        BaseTask.CAPTURE_ERR = True
        t = PythonTask("taskX",self.write_and_success)
        t.execute()
        assert "" == sys.stderr.getvalue()
        logger.flush('stderr',sys.stderr)
        assert "this is stderr S\n" == sys.stderr.getvalue()

    # failure 
    def test_captureFail(self):
        BaseTask.CAPTURE_ERR = True
        t = PythonTask("taskX",self.write_and_fail)
        nose.tools.assert_raises(TaskFailed,t.execute)
        assert "" == sys.stderr.getvalue()
        logger.flush('stderr',sys.stderr)
        assert "this is stderr F\n" == sys.stderr.getvalue()

    # error 
    def test_captureError(self):
        BaseTask.CAPTURE_ERR = True
        t = PythonTask("taskX",self.write_and_error)
        nose.tools.assert_raises(TaskError,t.execute)
        assert "" == sys.stderr.getvalue()
        logger.flush('stderr',sys.stderr)
        assert "this is stderr E\n" == sys.stderr.getvalue()
        
    ##### Do not capture stderr 
    #
    # success
    def test_noCaptureSuccess(self):
        BaseTask.CAPTURE_ERR = False
        t = PythonTask("taskX",self.write_and_success)
        t.execute()
        assert "this is stderr S\n" == sys.stderr.getvalue()

    # failure
    def test_noCaptureFail(self):
        BaseTask.CAPTURE_ERR = False
        t = PythonTask("taskX",self.write_and_fail)
        nose.tools.assert_raises(TaskFailed,t.execute)
        assert "this is stderr F\n" == sys.stderr.getvalue()

    # error
    def test_noCaptureError(self):
        BaseTask.CAPTURE_ERR = False
        t = PythonTask("taskX",self.write_and_error)
        nose.tools.assert_raises(TaskError,t.execute)
        assert "this is stderr E\n" == sys.stderr.getvalue()


class TestPythonVerbosityStdout(object):
    def setUp(self):
        # capture stdout
        self.oldOut = sys.stdout
        sys.stdout = StringIO.StringIO()
        logger.clear("stdout")

    def tearDown(self):
        sys.stdout.close()
        sys.stdout = self.oldOut

    def write_and_error(self):
        sys.stdout.write("this is stdout E\n")
        raise Exception("Hi i am an exception")
        
    def write_and_success(self):
        sys.stdout.write("this is stdout S\n")
        return True

    def write_and_fail(self):
        sys.stdout.write("this is stdout F\n")
        return False

    ##### Capture stdout
    #
    # success 
    def test_captureSuccess(self):
        BaseTask.CAPTURE_OUT = True
        t = PythonTask("taskX",self.write_and_success)
        t.execute()
        assert "" == sys.stdout.getvalue()
        logger.flush('stdout',sys.stdout)
        assert "this is stdout S\n" == sys.stdout.getvalue()

    # failure 
    def test_captureFail(self):
        BaseTask.CAPTURE_OUT = True
        t = PythonTask("taskX",self.write_and_fail)
        nose.tools.assert_raises(TaskFailed,t.execute)
        assert "" == sys.stdout.getvalue()
        logger.flush('stdout',sys.stdout)
        assert "this is stdout F\n" == sys.stdout.getvalue()

    # error 
    def test_captureError(self):
        BaseTask.CAPTURE_OUT = True
        t = PythonTask("taskX",self.write_and_error)
        nose.tools.assert_raises(TaskError,t.execute)
        assert "" == sys.stdout.getvalue()
        logger.flush('stdout',sys.stdout)
        assert "this is stdout E\n" == sys.stdout.getvalue()
        
    ##### Do not capture stdout 
    #
    # success
    def test_noCaptureSuccess(self):
        BaseTask.CAPTURE_OUT = False
        t = PythonTask("taskX",self.write_and_success)
        t.execute()
        assert "this is stdout S\n" == sys.stdout.getvalue()

    # failure
    def test_noCaptureFail(self):
        BaseTask.CAPTURE_OUT = False
        t = PythonTask("taskX",self.write_and_fail)
        nose.tools.assert_raises(TaskFailed,t.execute)
        assert "this is stdout F\n" == sys.stdout.getvalue()

    # error
    def test_noCaptureError(self):
        BaseTask.CAPTURE_OUT = False
        t = PythonTask("taskX",self.write_and_error)
        nose.tools.assert_raises(TaskError,t.execute)
        assert "this is stdout E\n" == sys.stdout.getvalue()
