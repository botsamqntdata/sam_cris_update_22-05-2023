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
from addon.bot_message.lib_bot import bot_linkedin



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

    log.printt('Linkedin Bot Cronjob: START')
    try:
        bot_linkedin = bot_linkedin()
        # bot_linkedin.authenticate(username, password)

    except:
        log.error(traceback.format_exc())
        raise

    #Checking data cronjob exist on Drive
    try:
        cronjob_id = '1KbchDDbWMBO_QUXzaMHClJwGxkAO_zSVahJ43ZTbTdw'
        worksheet_cronjob_data = util.gc.open_by_key(cronjob_id).worksheet_by_title('data_cron_linkedin')
        df_cronjob_data = worksheet_cronjob_data.get_as_df()
    except:
        log.error(traceback.format_exc())
        raise log.print('Linkedin Bot: Cronjob data not found')

    for folder_id in df_cronjob_data['FOLDER_ID'].tolist():
        try:
            if service == 'run_linkedin_message':
                log.printt('Linkedin Bot: Downloading data "cron_linkedin" from Drive')
                bot_linkedin.download_data_cron_from_drive(folder_id)

                log.printt('Linkedin Bot: START connecting via email..')
                try:
                    run_linkedin_message(username, password, filename='cron_linkedin_connect_via_email.xlsx', headless=True, num_run=0,
                            daily_quota=daily_quota_default, ignore_error=False, min_delay=min_delay_default, func='connect_via_email', num_export=50)
                except:
                    log.error(traceback.format_exc())

                if (datetime.now().weekday() == 1) or (datetime.now().weekday() == 3): #Check if today is Tuseday or Thursday
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

                log.printt('Linkedin Bot: Uploading data "cron_linkedin" to Drive')
                bot_linkedin.upload_data_cron_to_drive(folder_id)

            if service == 'backup_cron_linkedin':
                log.printt('Linkedin Bot: Creating backup data "cron_linkedin" on Drive')
                bot_linkedin.backup_data_cron(folder_id)

            if service == 'get_conversation':
                log.printt('Linkedin Bot: Login to Linkedin')
                bot_linkedin.authenticate(username, password)

                log.printt('Linkedin Bot: Creating data Linkedin conversation')
                _, path_output, filename = bot_linkedin.get_conversation(export=True, unread=False)

                log.printt('Linkedin Bot: Uploading data Linkedin conversation to Drive')
                conversation_folder_id = '1FchejLNU0z_IAldK3EqE5S01mMVK0Xxk'
                bot_linkedin.upload_file_to_drive(filename, path_output, conversation_folder_id)

        except:
            log.printt('Linkedin Bot: Error with service in folder %s' % folder_id)
            log.error(traceback.format_exc())
            pass

    log.printt('Linkedin Bot Cronjob: DONE')




