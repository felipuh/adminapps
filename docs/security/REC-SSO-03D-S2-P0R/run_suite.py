"""Record method origins and results without altering historical suites."""
import inspect, json, pathlib, runpy, sys, unittest
output, script, *args = sys.argv[1:]
entries = {}; runners = []
original_run = unittest.TextTestRunner.run

def record_run(self, suite):
    original_class = self.resultclass
    class Recorded(original_class):
        def startTest(self, test):
            method = getattr(test, test._testMethodName)
            entries[test.id()] = {'id': test.id(), 'method': test._testMethodName,
                'source': inspect.getsourcefile(method), 'line': getattr(getattr(method, '__code__', None), 'co_firstlineno', None),
                'qualname': getattr(method, '__qualname__', ''), 'status': 'RUNNING'}
            super().startTest(test)
        def addSuccess(self, test):
            entries[test.id()]['status'] = 'PASS'; super().addSuccess(test)
        def addFailure(self, test, err):
            entries[test.id()]['status'] = 'FAIL'; super().addFailure(test, err)
        def addError(self, test, err):
            entries[test.id()]['status'] = 'ERROR'; super().addError(test, err)
        def addSkip(self, test, reason):
            entries[test.id()]['status'] = 'SKIP'; super().addSkip(test, reason)
        def addSubTest(self, test, subtest, err):
            if err is not None:
                entries[test.id()]['status'] = 'FAIL' if issubclass(err[0], test.failureException) else 'ERROR'
            super().addSubTest(test, subtest, err)
    self.resultclass = Recorded
    result = original_run(self, suite)
    runners.append({'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors), 'skipped': len(result.skipped)})
    return result
unittest.TextTestRunner.run = record_run
sys.argv = [script, *args]
sys.path.insert(0, str(pathlib.Path(script).resolve().parent))
try:
    runpy.run_path(script, run_name='__main__')
finally:
    pathlib.Path(output).write_text(json.dumps({'runners': runners, 'methods': list(entries.values())}, indent=2))
