import PySimpleGUI as sg
import os, sys, io
import subprocess, psutil, signal,shutil
import pydoc
from apiclient.http import MediaIoBaseDownload
from datetime import datetime, timedelta
import time

import util
from lib.util import logger as log
from lib.util.systool import makedirs



def hello(text = 'Hello, world!'):
    return text


def hi():
    return 'Hi there!'


def init_log(log_type='print', logdir=None):
    if logdir is None:
        LOGDIR = util.path_log + '/'
    else:
        LOGDIR = logdir

    if log_type == 'print':
        PRINT_VERBOSITY = 'info'
        # Create log file
        log.set_print_verbosity(PRINT_VERBOSITY)
    else:
        LOG_VERBOSITY   = 'debug'
        log.set_log_verbosity(LOG_VERBOSITY)

    log.enable_colors()
    log.enable_logging()
    makedirs(LOGDIR)
    log.set_logdir(LOGDIR)

    log.printt('======== %s __ %s ========' % (
        sys._getframe(1).f_code.co_name, datetime.now().strftime('%d-%b-%y %H:%M:%S').upper())
    )


def delete_oldbackup(num_day = 30):
    log = ''

    try:
        for dirpath, dirnames, filenames in os.walk(util.path_note):
           for file in filenames:
              curpath = os.path.join(dirpath, file)
              file_modified = datetime.fromtimestamp(os.path.getmtime(curpath))
              if (datetime.now() - file_modified > timedelta(days = num_day)) and (curpath.split('.')[-1] in ['json', 'gif']):
                  os.remove(curpath)
                  log += "'{}': removed\n".format(curpath)
        log += 'DONE.'
    except:
        log += "'{}': error\n".format(curpath)

    return log


def get_filepath(filename_extension = 'all'):
    try:
        if filename_extension == 'xlsx':
            path = sg.PopupGetFile(
                       'Choose File to Upload',
                       no_window = True,
                       default_extension = '.xlsx',
                       file_types = (('Excel Files', '*.xlsx'),)
                   )
        elif filename_extension == 'py':
            path = sg.PopupGetFile(
                       'Choose File to Upload',
                       no_window = True,
                       multiple_files = True,
                       default_extension = '.py',
                       file_types = (('Python Files', '*.py'),)
                   )
        else:
            if sys.platform == 'win32':
                path = sg.PopupGetFile(
                    'Choose File to Upload',
                    no_window = True,
                    multiple_files = True,
                    default_extension = '*.*',
                    file_types = (('ALL Files', '*.*'),)
                )
            else:
                path = sg.PopupGetFile(
                    'Choose File to Upload',
                    no_window = True,
                    multiple_files = True,
                    default_extension = '*.*',
                    file_types = (
                        ('RTF Files', '*.rtf'),
                        ('Text Files', '*.txt'),
                        ('Python Files', '*.py'),
                        ('Excel Files', '*.xlsx'),
                    )
                )
    except:
        path = None
    return path


def get_folderpath():
    try:
        path = sg.PopupGetFolder('Select a Destination', no_window = True)
    except:
        path = None
    return path


def whatis(module):
    return pydoc.render_doc(module, 'help(%s)', renderer = pydoc.plaintext)


def list_spreadsheet_by_folderid(folder_id):
    results = util.drive_service.files().list(q = "mimeType='application/vnd.google-apps.spreadsheet' and parents in '"\
        + folder_id + "' and trashed = false", fields = "nextPageToken, files(id, name)").execute()
    items = results.get('files', [])

    return items


def list_file_by_folderid(folder_id):
    results = util.drive_service.files().list(q = "mimeType!='application/vnd.google-apps.folder' and parents in '"\
        + folder_id + "' and trashed = false", fields = "nextPageToken, files(id, name)", pageSize = 400).execute()
    items = results.get('files', [])

    return items


def list_folder_by_folderid(folder_id):
    results = util.drive_service.files().list(q = "mimeType='application/vnd.google-apps.folder' and parents in '"\
        + folder_id + "' and trashed = false", fields = "nextPageToken, files(id, name)", pageSize = 400).execute()
    items = results.get('files', [])

    return items


def get_file_by_fileid(file_dict, path):
    request = util.drive_service.files().get_media(fileId = file_dict['id'])
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()

    with io.open(path + file_dict['name'], 'wb') as f:
        fh.seek(0)
        f.write(fh.read())


def create_folder(service, parent_id, filename):
    file_metadata = {
        'name': filename,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_id]
    }

    folder_id = service.files().create(body=file_metadata, fields='id').execute()['id']

    return folder_id


def create_spreadsheet(service, parent_id, filename):
    file_metadata = {
        'name': filename,
        'mimeType': 'application/vnd.google-apps.spreadsheet',
        'parents': [parent_id]
    }

    spreadsheet_id = service.files().create(body=file_metadata, fields='id').execute()['id']

    return spreadsheet_id


def search_folderid(parent_id, keyword):
    folder_id = ''
    try:
        list_folder = list_folder_by_folderid(parent_id)
        folder_id = [item['id'] for item in list_folder if item['name'].find(keyword) != -1][0]
    except:
        pass

    return folder_id


def trash_file(folder_id, keyword=None):
    def trash_func(request_id, response, exception):
        if exception is not None:
            # Do something with the exception
            pass
        else:
            # Do something with the response
            pass

    list_file = list_file_by_folderid(folder_id)
    if keyword is not None:
        list_file = [file for file in list_file if file['name'].find(keyword) != -1]

    batch = util.service_v2.new_batch_http_request(callback=trash_func)
    for idx, file in enumerate(list_file):
        batch.add(util.service_v2.files().trash(fileId=file['id']))

        if ((idx + 1) % 100 == 0) or ((idx+1) == len(list_file)):
            batch.execute()
            time.sleep(5)
            batch = util.service_v2.new_batch_http_request(callback=trash_func)


def move_file(from_folder_id, to_folder_id, keyword=None, copy=False):
    def move_func(request_id, response, exception):
        if exception is not None:
            # Do something with the exception
            pass
        else:
            # Do something with the response
            pass

    list_file = list_file_by_folderid(from_folder_id)
    if keyword is not None:
        list_file = [file for file in list_file if file['name'].find(keyword) != -1]

    batch = util.drive_service.new_batch_http_request(callback=move_func)

    print('start')
    for idx, file in enumerate(list_file):
        previous_parents = from_folder_id
        new_parents = to_folder_id
        file_id = file['id']
#        file = util.drive_service.files().get(fileId=file_id, fields='parents').execute()
#        to_folder_id = file.get('parents')
        if copy:
            new_parents = ','.join([previous_parents, new_parents])

        batch.add(
            util.drive_service.files().update(
                fileId=file_id,
                addParents=new_parents,
                removeParents=previous_parents,
                fields='id, parents'
            )
        )

        if ((idx + 1) % 100 == 0) or ((idx+1) == len(list_file)):
            batch.execute()
            print('batch')
            time.sleep(5)
            batch = util.drive_service.new_batch_http_request(callback=move_func)


def backup_tempo(to_folder_name):
    '''
    to_folder_name is used as keyword to search tempo data.
    '''
    backup_tempodata_id = search_folderid(util.tempodata_id, 'backup_tempodata')
    backup_id = search_folderid(backup_tempodata_id, util.username)

    to_folder_id = search_folderid(backup_id, to_folder_name)
    if to_folder_id == '':
        to_folder_id = create_folder(util.drive_service, backup_id, to_folder_name)

    print('move')
    move_file(util.tempo_id, to_folder_id, keyword=to_folder_name, copy=False)


def insert_dataframe_to_googlesheet(spreadsheet_id, sheetname, data, start=None, copy_head=True):
    sheet = util.gc.open_by_key(spreadsheet_id).worksheet_by_title(sheetname)

    if start is None:
        #Get first empty row
        cells = sheet.get_all_values(include_tailing_empty_rows=False, include_tailing_empty=False, returnas='matrix')
        last_row = len(cells)
        start = 'A' + str(last_row)
        copy_head = False #Remove header if append

    sheet.set_dataframe(data, start, copy_head=copy_head, extend=True, escape_formulae=True)


def cpu_count():
    ''' Returns the number of CPUs in the system
    '''
    num = 1
    if sys.platform == 'win32':
        try:
            num = int(os.environ['NUMBER_OF_PROCESSORS'])

        except (ValueError, KeyError):
            pass

    elif sys.platform == 'darwin':
        try:
            num = int(os.popen('sysctl -n hw.ncpu').read())

        except ValueError:
            pass

    else:
        try:
            num = os.sysconf('SC_NPROCESSORS_ONLN')

        except (ValueError, OSError, AttributeError):
            pass

    return num


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
    print(f'Number of CPU used: {num_cpu}')

    processes = []
    while True:
        while cmds and len(processes) < num_cpu:
            task = cmds.pop()
#            print(list2cmdline(task))
            p = subprocess.Popen(task, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#            print('Process %s : %s' %(p.pid, str(task)))
            processes.append(p)

        for p in processes:
            if done(p):
                if success(p):
#                    print('Process Success %s' %(p.pid))
                    processes.remove(p)
                else:
                    print(p.stdout.read())
                    print(p.stderr.read())
                    processes.remove(p)

        if not processes and not cmds:
            break
        else:
            time.sleep(5)
#        else:
#            # Quit if currentTime is in working hours and weekday
#            currentTime = datetime.datetime.now()
#            if((currentTime-start_time).seconds/3600+(currentTime-start_time).days*24>maxhour):
#                log.info("It is work out maxhour1")
#                if (currentTime.isoweekday() in [0,1,2,3,4,6]) and  currentTime.hour in range(5, 19):
#                    log.info("It is in working hours and weekday1")
#                    run_time=datetime.datetime(currentTime.year,currentTime.month,currentTime.day,19,5)
#                    deltatime=run_time-currentTime
#                    time.sleep(deltatime.seconds)
#                else:
#                    time.sleep(5)


def execute_command(display_name, command, *args, communicate = False):
    try:
#        print(command + ' ' + ' '.join(list(args)))
        p = psutil.Popen(
            command + ' ' + ' '.join(list(args)),
            shell = True, stdout = subprocess.PIPE, stderr = subprocess.PIPE
        )

        if communicate:
            out, err = p.communicate()
            if out:
                print(out.decode('utf-8'))
            if err:
                print(err.decode('utf-8'))

        print('{} start: {}'.format(display_name, p.pid))

    except Exception as e:
        print(e)
        pass

    return p.pid


def kill_processtree(display_name, pid, sig = signal.SIGTERM, include_parent = True, timeout = None, on_terminate = None):
    """
    Kill a process tree (including grandchildren) with signal "sig".
    "on_terminate", if specified, is a callabck function which is called as soon as a child terminates.
    """
    try:
        if pid == os.getpid():
            raise RuntimeError("I refuse to kill myself")
        parent = psutil.Process(pid)
        children = parent.children(recursive = True)
        if include_parent:
            children.append(parent)
        for p in children:
            p.send_signal(sig)

        print('{} kill: {}'.format(display_name, pid))

    except Exception as e:
        print(e)
        pass




