from uwtools.logger import Logger

level = 'debug'
logfile_path = './demo.log'
number_of_log_msgs = 5
reference = {'debug':"Logging demo has started",
             'info':"Logging to 'demo.log' in the script dir",
             'warning':"This is my last warning, take heed",
             'error':"This is an error",
             'critical':"He's dead, She's dead.  They are all dead!"}

def test_logger():
    '''Test log file'''

    # Log to stream and file
    try:
        log = Logger('demo', level=level, logfile_path=logfile_path)
        log.debug(reference['debug'])
        log.info(reference['info'])
        log.warning(reference['warning'])
        log.error(reference['error'])
        log.critical(reference['critical'])
    except Exception as e:
        raise AssertionError('logging failed as %s' % e)

    # Make sure log to file created messages
    try:
        with open(logfile_path, 'r') as fh:
            logfile = fh.readlines()
    except Exception as e:
        raise AssertionError('failed reading log file as %s' % e)

    # Ensure number of messages are same
    log_msgs_in_logfile = len(logfile)
    assert log_msgs_in_logfile == number_of_log_msgs

    # Ensure messages themselves are same
    for count, line in enumerate(logfile):
        lev = line[line.find("[")+1:line.find("]")]
        message = line.split(':')[-1].strip()
        assert reference[lev.lower()] == message
