import argparse
import time
import traceback
from datetime import datetime
from subprocess import Popen, list2cmdline, PIPE
import sys
from os.path import dirname, abspath

sys.path.insert(0, dirname(dirname(dirname(abspath(__file__)))))
from lib import lib_sys
from lib.util import logger as log
from addon.bot_message.func.linkedin_message import *



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



if __name__ == '__main__':
    parser = argparse.ArgumentParser('Linkedin Bot Cronjob', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-s', '--service', help='Service name', default='')
    # parser.add_argument('-func', '--func', help='Function to run in service', default='')
    parser.add_argument('-u', '--username', help='Linkedin email', default='')
    parser.add_argument('-p', '--password', help='Linkedin password', default='')
    # parser.add_argument('-file', '--filename', help='File name', default='')
    # parser.add_argument('-c', '--cpu', help='Number of CPUs used', default=1)

    args = parser.parse_args()
    service = args.service
    # func = args.func
    username = args.username
    password = args.password
    # filename = args.filename
    # cpu = int(args.cpu)

# ================================================================
    lib_sys.init_log()

    log.printt('START Linkedin Bot Cronjob')
    if service == 'run_linkedin_message':
        log.printt('Linkedin Bot: START connecting via email..')
        try:
            run_linkedin_message(username, password, filename='cron_linkedin_connect_via_email.xlsx', headless=True, num_run=50,
                    daily_quota=daily_quota_default, ignore_error=False, min_delay=min_delay_default, func='connect_via_email', num_export=50)
        except:
            log.error(traceback.format_exc())

        if datetime.now().weekday() == 2: #Check if today is Wednesday
            time.sleep(60)
            log.printt('Linkedin Bot: START connecting with message..')
            try:
                run_linkedin_message(username, password, filename='cron_linkedin_connect.xlsx', headless=True, num_run=50,
                        daily_quota=daily_quota_default, ignore_error=False, min_delay=min_delay_default, func='connect', num_export=50)
            except:
                log.error(traceback.format_exc())

        time.sleep(60)
        log.printt('Linkedin Bot: START sending message UP..')
        try:
            run_linkedin_message(username, password, filename='cron_linkedin_UP.xlsx', headless=True, num_run=50,
                    daily_quota=daily_quota_default, ignore_error=False, min_delay=min_delay_default, func='send', num_export=50)
        except:
            log.error(traceback.format_exc())

    log.printt('Linkedin Bot Cronjob: DONE')



