import argparse
import time
from datetime import datetime, timedelta
from subprocess import Popen, list2cmdline, PIPE
import sys
from os.path import dirname, abspath

sys.path.insert(0, dirname(dirname(abspath(__file__))))
from lib import lib_sys, lib_tempo
from lib.util import logger as log



def exec_commands(cmds, cpu=4):
    ''' Exec commands in parallel in multiple process
    (as much as we have CPU)
    '''
    if not cmds: return # empty list

    def done(p):
        return p.poll() is not None
    def success(p):
        return p.returncode == 0
    def fail():
        sys.exit(1)

    num_cpu = min(cpu, cpu_count() - 2)
    log.info(f'Number of CPU used: {num_cpu}')

    processes = []
    while True:
        while cmds and len(processes) < num_cpu:
            task = cmds.pop()
#            print(list2cmdline(task))
            p = Popen(task, stdout=PIPE, stderr=PIPE)
#            log.info('Process %s : %s' %(p.pid, str(task)))
            processes.append(p)

        for p in processes:
            if done(p):
                if success(p):
#                    log.info('Process Success %s' %(p.pid))
                    processes.remove(p)
                else:
                    log.error(p.stdout.read())
                    log.error(p.stderr.read())
                    processes.remove(p)

        if not processes and not cmds:
            break
        else:
            time.sleep(5)


def create_tempo_report(fromaddr, password, month=None):
    previous_date = (datetime.now() - timedelta(days=1)).strftime('%b-%y').upper()
    if month is not None:
        previous_month = month
    else:
        previous_month = previous_date[:3]

    try:
        lib_tempo.get_tempo(month=previous_month)
    except Exception as e:
        log.error(e)
        pass

    try:
        lib_tempo.get_tempo_server(month=previous_month)
    except Exception as e:
        log.error(e)
        pass

    try:
        lib_tempo.send_report(fromaddr, password, message_subject='TempoNote ' + previous_date,
                              toaddr='henry.duong.universes@gmail.com',
                              cc='aiden.smith@qntdata.com, ray.huynh@qntdata.com, chau.tran2015@qcf.jvn.edu.vn',
                              bcc='')
    except Exception as e:
        log.error(e)



if __name__ == '__main__':
    parser = argparse.ArgumentParser('bot SAM TempoNote report monthly', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-f', '--fromaddr', help='Email to sent from', default='')
    parser.add_argument('-p', '--password', help='Email password', default='')
    # parser.add_argument('-c', '--cpu', help='Number of CPUs used', default=1)

    args = parser.parse_args()
    fromaddr = args.fromaddr
    password = args.password
    # cpu = int(args.cpu)

# ================================================================
    lib_sys.init_log()

    log.printt('START bot SAM TempoNote report monthly')
    try:
        # Run at date 1 every month
        create_tempo_report(fromaddr, password)

    except Exception as e:
        log.error(e)

    log.printt('bot SAM TempoNote report monthly: DONE')





