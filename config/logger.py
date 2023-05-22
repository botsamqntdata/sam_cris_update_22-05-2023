import logging

import util



formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt = '%Y-%m-%d %H:%M:%S')


def setup_logger(name, log_file, level = logging.INFO):
    """To setup as many loggers as you want"""

    handler = logging.FileHandler(log_file)        
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger

    
#Debugger
log_debugger = setup_logger('Debugger', util.path_log + 'debugger.log')

#TempoNote
log_temponote = setup_logger('TempoNote', util.path_log + 'temponote.log')

#TempoMonitor
log_tempomonitor = setup_logger('TempoMonitor', util.path_log + 'tempomonitor.log')