import PySimpleGUI as sg
import traceback
import os, sys
from os import listdir
from os.path import isfile, join
import json
from datetime import datetime, timedelta
from googleapiclient.http import MediaFileUpload
import pandas as pd
import psutil
import shutil
import time
import cv2
import imageio

import util
from lib import lib_sys
from lib.util import logger as log
from config.logger import log_debugger



def checkin():
    server_notice = ''
    with open(util.path_config + 'server.txt', 'r') as f:
        server = f.readline()
        server = server.replace('\n', '').replace(' ', '').replace('server=', '')

    if server == 'backup':
        server_notice = "WARNING: You are connecting to server 'backup'. Please switch to 'main' in /config/server.txt.\n"

    if util.temponote_pid is not None:
        lib_sys.kill_processtree('TempoNote', util.temponote_pid)
        util.temponote_pid = None
    util.temponote_pid = lib_sys.execute_command(
                        'TempoNote',
                        'python', './popup_tempo.py', '-n on')
    if util.capimgs_pid is not None:
        lib_sys.kill_processtree('Capture Images', util.capimgs_pid)
        util.capimgs_pid = None
    util.capimgs_pid = lib_sys.execute_command(
                        'Capture Images',
                        'python', './popup_tempo.py', '-c on')

    return '%sStart TempoNote: %s\nStart Capture Images: %s' % (server_notice, util.temponote_pid, util.capimgs_pid)


def checkout(append=True):
    try:
        lib_sys.kill_processtree('TempoNote', util.temponote_pid)
        lib_sys.kill_processtree('Capture Images', util.capimgs_pid)
        if util.tempomonitor_pid is not None:
            lib_sys.kill_processtree('TempoMonitor', util.tempomonitor_pid)
    except:
        pass

    if append is True:
        append_note('SAM stop.')

    return 'Stop TempoNote: {}\nStop Capture Images: {}'.format(util.temponote_pid, util.capimgs_pid)


def reset(minutes = 15):
    time_start = time.time()
    time_end = time_start + minutes*60

    print('Reset: {} - {}.'.format(
        datetime.fromtimestamp(time_start).strftime('%H:%M:%S'),
        datetime.fromtimestamp(time_end).strftime('%H:%M:%S')
        ))

    append_note('SAM reset.')

    if util.temponote_pid is not None and util.capimgs_pid is not None:
        p_temponote = psutil.Process(util.temponote_pid)
        p_capimgs = psutil.Process(util.capimgs_pid)

        p_temponote.suspend()
        p_capimgs.suspend()

        while time.time() < time_end:
            continue

        p_temponote.resume()
        p_capimgs.resume()

    return 'Reset: DONE.'


def append_note(text):
    now_temp = datetime.now()
    current_time = now_temp.strftime('%H:%M:%S')
    date = now_temp.strftime('%d-%b-%y').upper()
    date_server = now_temp.strftime('%Y-%m-%d %H:%M:%S')
    note_path = util.path_note + 'note_{}_{}.json'.format(util.username, date)

    if not os.path.exists(note_path):
        with open(note_path, 'w+') as file:
            json.dump([], file)
        json_note = []
    else:
        #Load json data
        with open(note_path, 'r') as file:
            json_note = json.load(file)

    dict_note = {
        'DATETIME': date,
        'TIME': current_time,
        'NAME': util.username,
        'TASK': util.task_doing,
        'OUTCOME': text,
        'NEXTACT': text
    }

    #Write to note file
    json_note.append(dict_note)
    with open(note_path, 'w') as file:
        json.dump(json_note, file)

    try:
        #Upload latest note to Oracle database
        util.oracle_db.open_conn().query(
            "INSERT INTO {}(DATETIME, TIME, NAME, TASK, OUTCOME, NEXTACT) \
            VALUES(TO_DATE(:datetime, 'yyyy-mm-dd hh24:mi:ss'), :time, :name, :task, :outcome, :nextact)".format(
            util.temponote),
            {
                'datetime': date_server,
                'time': current_time,
                'name': util.username,
                'task': util.task_doing,
                'outcome': text,
                'nextact': text
             }
        )

    except:
        pass


def run_monitor():
    if util.tempomonitor_pid is not None:
        lib_sys.kill_processtree('TempoMonitor', util.tempomonitor_pid)
        util.tempomonitor_pid = None
    util.tempomonitor_pid = lib_sys.execute_command(
                        'TempoMonitor',
                        'python', './popup_tempo.py', '-m on')

    return 'Start TempoMonitor: {}'.format(util.tempomonitor_pid)


def create_window_todo():
    sg.theme('TanBlue')
    if sys.platform != 'win32':
        sg.set_options(font = ('Helvetica', 15))

    layout = [
        [sg.Text('Today Outcomes')],
        [sg.Multiline(key = '-OUTCOMES-', size = (45, 5))],
        [sg.Text('To Do')],
        [sg.Multiline(key = '-TODO-', size = (45, 5))],
        [sg.Submit(key = '-SUBMIT-')]
    ]

    window = sg.Window(
        'To Do List',
        layout,
        keep_on_top = True,
        finalize = True
    )

    return window


def update_todo(dict_todo):
    sh = util.gc.open_by_key(util.review_id)

    try:
        worksheet = sh.worksheet_by_title(util.username)
    except:
        sh.add_worksheet(util.username)
        worksheet = sh.worksheet_by_title(util.username)
        worksheet.update_row(1,
            values = ['DATETIME', 'TIME', 'NAME', 'OUTCOMES', 'TODO', 'BOD_NOTE', 'GGL_NOTE', 'STAFF_NOTE']
        )
        worksheet.delete_rows(2, 1000)

    data = pd.DataFrame([dict_todo]).values[0].tolist()
    worksheet.insert_rows(1, values = data, inherit = True)


def add_todo():
    window = create_window_todo()

    while True:
        try:
            event, values = window.read(timeout = 100)
            if event == sg.TIMEOUT_KEY:
                tp_outcomes = values['-OUTCOMES-']
                tp_todo = values['-TODO-']
                pass

            if len(tp_outcomes.replace('\n','')) > 0 and len(tp_todo.replace('\n','')) > 0 and event == '-SUBMIT-':
                todo_path = util.path_note + 'todo_{}_{}.json'\
                    .format(util.username, datetime.now().strftime('%d-%b-%y').upper())
                if not os.path.exists(todo_path):
                    with open(todo_path, 'w+') as file:
                        json.dump([], file)
                    json_todo = []
                else:
                    #Load json data
                    with open(todo_path, 'r') as file:
                        json_todo = json.load(file)
                dict_todo = {
                    'DATETIME': datetime.now().strftime('%d-%b-%y').upper(),
                    'TIME': datetime.now().strftime('%H:%M:%S'),
                    'NAME': util.username,
                    'OUTCOMES': tp_outcomes,
                    'TODO': tp_todo
                }

                #Update daily review
                update_todo(dict_todo)

                #Write to json
                json_todo.append(dict_todo)
                with open(todo_path, 'w') as file:
                    json.dump(json_todo, file)

                window.Hide()
                window.Close()

                return 'Todo list submitted successfully.'

            if event == sg.WIN_CLOSED:
                window.Close()
                break

        except UnicodeDecodeError:
            pass

        except KeyboardInterrupt:
            pass

        except:
            log_debugger.warning(traceback.format_exc())
            window.Close()
            return 'Todo list submitted failed!'


def get_tempo_folder(username = util.username):
    tempo_id = ''
    temp_id = ''

    list_folder = lib_sys.list_folder_by_folderid(util.tempodata_id)
    for idx, val in enumerate(list_folder):
        if val['name'] == username:
            tempo_id = val['id']
            break

    list_user_folder = lib_sys.list_folder_by_folderid(tempo_id)
    for idx, val in enumerate(list_user_folder):
        if val['name'] == 'temp_{}'.format(username):
            temp_id = val['id']
            break

    return tempo_id, temp_id


def push_file(filename, path, folder_id):
    try:
        exist_flag = 0

        #Create metadata and content
        file_metadata = {'name': filename,
                         'parents': [folder_id]}
        media = MediaFileUpload(path,
                                mimetype = '*/*',
                                resumable = True)
        #Check if file is exist
        list_file = lib_sys.list_file_by_folderid(folder_id)
        for idx, val in enumerate(list_file):
            if val['name'] == filename:
                file_id = val['id']
                exist_flag = 1
                break

        if exist_flag == 1:
            util.drive_service.files().update(fileId = file_id, media_body = media).execute()
        else:
            util.drive_service.files().create(body = file_metadata, media_body = media, fields = 'id').execute()
    except:
        raise


def push_tempo(username = util.username, today = True):
    log = ''
    try:
        if today:
            filename = '{}_{}'.format(username, datetime.now().strftime('%d-%b-%y').upper())
        else:
            filename = '{}_{}'.format(username, today)
        note_file = 'note_' + filename + '.json'
        action_file = 'action_' + filename + '.json'
        todo_file = 'todo_' + filename + '.json'
        image_file = 'image_' + filename + '.gif'

        tempo_id = util.tempo_id
        if username != util.username:
            tempo_id, temp_id = get_tempo_folder(username)

        #Push note
        try:
            push_file(note_file, util.path_note + note_file, tempo_id)
            log += 'Uploading note.\n'
        except:
            log += 'Note uploaded failed!\n'

        #Push action
        try:
            push_file(action_file, util.path_note + action_file, tempo_id)
            log += 'Uploading action.\n'
        except:
            log += 'Action uploaded failed!\n'

        #Push todo
        try:
            push_file(todo_file, util.path_note + todo_file, tempo_id)
            log += 'Uploading todo.\n'
        except:
            log += 'Todo uploaded failed!\n'

        #Push image
        try:
            push_file(image_file, util.path_note + image_file, tempo_id)
            log += 'Uploading image.\n'
        except:
            log += 'Image uploaded failed!\n'
        log += 'DONE.'

        #Push missing note to oracle server
        try:
            list_file = [file for file in listdir(util.path_note) if isfile(join(util.path_note, file))]
            list_file = [file for file in list_file if file.find('temp_note_') != -1]

            if len(list_file) > 0:
                for filename in list_file:
                    temp_note_path = util.path_note + filename
                    try:
                        with open(temp_note_path, 'r', encoding = 'latin-1') as f:
                            json_tempnote = json.load(f)
                    except:
                        with open(temp_note_path, 'r', encoding = 'utf-8-sig') as f:
                            json_tempnote = json.load(f)
                    f.close()

                    try:
                        if len(json_tempnote) == 0:
                            os.remove(temp_note_path) #Remove tempnote if empty
                        else:
                            for idx, note in enumerate(json_tempnote):
                                util.oracle_db.open_conn().query(
                                    "INSERT INTO {}(DATETIME, TIME, NAME, OUTCOME, NEXTACT) \
                                    VALUES(TO_DATE(:datetime, 'yyyy-mm-dd hh24:mi:ss'), :time, :name, :outcome, :nextact)".format(
                                    util.temponote),
                                    {
                                        'datetime': datetime.strptime(note['DATETIME'], '%d-%b-%y').\
                                            strftime('%Y-%m-%d') + ' ' + note['TIME'],
                                        'time': note['TIME'],
                                        'name': note['NAME'],
                                        'outcome': note['OUTCOME'],
                                        'nextact': note['NEXTACT']
                                     }
                                )
                            #Remove tempnote if uploading successful
                            os.remove(temp_note_path)
                    except:
                        pass

        except:
            pass

        #Push missing image to oracle server
#        try:
#            list_file = [file for file in listdir(util.path_note) if isfile(join(util.path_note, file))]
#            list_file = [file for file in list_file if file.find('temp_image_') != -1]
#
#            if len(list_file) > 0:
#                for filename in list_file:
#                    temp_image_path = util.path_note + filename
#                    image_gif = imageio.get_reader(temp_image_path)
#
#                    try:
#                        if len(image_gif) == 0:
#                            os.remove(temp_image_path) #Remove tempimage if empty
#                        else:
#                            for idx in range(0, len(image_gif)):
#                                img = image_gif.get_data(idx)
#                                is_success, im_buf_arr = cv2.imencode('.jpg', img)
#                                byte_im = im_buf_arr.tobytes()
#                                util.oracle_db.open_conn().query(
#                                    "INSERT INTO {}(DATETIME, TIME, NAME, IMAGE) \
#                                    VALUES(TO_DATE(:datetime, 'yyyy-mm-dd hh24:mi:ss'), :time, :name, :image)".format(
#                                    util.tempomonitor),
#                                    {
#                                        'datetime': datetime.strptime(filename[-13:-4], '%d-%b-%y').\
#                                            strftime('%Y-%m-%d') + ' ' + note['TIME'],
#                                        'time': note['TIME'],
#                                        'name': note['NAME'],
#                                        'image': byte_im
#                                    }
#                                )
#
#                            #Remove tempimage if uploading successful
#                            os.remove(temp_image_path)
#                    except:
#                        pass
#
#        except:
#            pass

    except:
        pass

    return log


def get_current_status(username):
    _, temp_id = get_tempo_folder(username)
    list_file = lib_sys.list_file_by_folderid(temp_id)
    monitor_path = util.path_monitor + username + '/'
    if not os.path.exists(monitor_path):
        os.makedirs(monitor_path)

    for val in list_file:
        lib_sys.get_file_by_fileid(val, monitor_path)


def get_listfile(list_file, data_path, output_file, filetype = None):
    try:
        writer = pd.ExcelWriter(output_file)
        df = pd.DataFrame()

        for file in list_file:
            try:
                lib_sys.get_file_by_fileid(file, data_path)
                file_path = data_path + file['name']
                try:
                    with open(file_path, 'r', encoding = 'latin-1') as f:
                        json_file = json.load(f)
                except:
                    with open(file_path, 'r', encoding = 'utf-8-sig') as f:
                        json_file = json.load(f)

                temp_df = pd.DataFrame(json_file)
                if filetype == 'note':
                    temp_df['DELTA_TIME'] = [datetime.strptime(i, '%H:%M:%S') for i in temp_df['TIME']]
                    temp_df['DELTA_TIME'] = temp_df['DELTA_TIME'].diff().fillna(timedelta(0))
                    temp_df['DELTA_TIME'] = [i.seconds / 60 for i in temp_df['DELTA_TIME']]
                    temp_df['NOTE_MISSED'] = [int(i/8) for i in temp_df['DELTA_TIME']]

                df = pd.concat([df, temp_df], sort = False)
                name_sheet = file['name'][5:-15]
                df.to_excel(writer, sheet_name = name_sheet, index = False)

                os.remove(file_path)
            except Exception as e:
                log.error('%s __ %s' % (file, e))
                pass

        writer.save()
    except:
        pass


def combine_file(list_file, output_file):
    writer = pd.ExcelWriter(output_file)

    for file in list_file:
        try:
            df = pd.read_excel(file)
            if len(df) != 0:
                name_sheet = df['NAME'][0]
                df.to_excel(writer, sheet_name = name_sheet, index = False)

            os.remove(file)

            folder = os.path.dirname(file)
            if len(os.listdir(folder)) == 0:
                shutil.rmtree(folder)

        except Exception as e:
            log.error('%s: %s' % (file, e))
            pass

    writer.save()


def combine_tempo():
    list_note = []
    list_action = []
    list_todo = []
    for root, dirs, files in os.walk(util.path_output):
        for file in files:
            if file.find('total') == -1 and file.find('server') == -1:
                if file.endswith(".xlsx") and file.find('note') != -1:
                    list_note.append(os.path.join(root, file))
                if file.endswith(".xlsx") and file.find('action') != -1:
                    list_action.append(os.path.join(root, file))
                if file.endswith(".xlsx") and file.find('todo') != -1:
                    list_todo.append(os.path.join(root, file))

    output_path = util.path_output + 'total_'
    combine_file(list_note, output_path + 'note.xlsx')
    combine_file(list_action, output_path + 'action.xlsx')
    combine_file(list_todo, output_path + 'todo.xlsx')


def get_tempo(username = 'all', month = None):
    list_folder = lib_sys.list_folder_by_folderid(util.tempodata_id)
    if username != 'all':
        list_folder = [i for i in list_folder if i['name'].find('backup') == -1
            and i['name'].find(username) != -1]
    else:
        list_folder = [i for i in list_folder if i['name'].find('backup') == -1]

    for idx, val in enumerate(list_folder):
        output_path = util.path_output + val['name'] + '/'
        if not os.path.exists(output_path):
            os.makedirs(output_path)

        list_file = lib_sys.list_file_by_folderid(val['id'])

        if month is None:
            last_day = datetime.now() - timedelta(days=1)
            month = last_day.strftime('%b').upper()

        if month != 'all':
            list_note = [i for i in list_file if i['name'].find('note') != -1
                and i['name'].find('temp') == -1 and i['name'].find(month) != -1]
            list_action = [i for i in list_file if i['name'].find('action') != -1 and i['name'].find(month) != -1]
            list_todo = [i for i in list_file if i['name'].find('todo') != -1 and i['name'].find(month) != -1]

        else:
            list_note = [i for i in list_file if i['name'].find('note') != -1 and i['name'].find('temp') == -1]
            list_action = [i for i in list_file if i['name'].find('action') != -1]
            list_todo = [i for i in list_file if i['name'].find('todo') != -1]

        get_listfile(list_note, util.path_output, output_path + 'note_{}.xlsx'.format(val['name']), filetype = 'note')
        get_listfile(list_action, util.path_output, output_path + 'action_{}.xlsx'.format(val['name']))
        get_listfile(list_todo, util.path_output, output_path + 'todo_{}.xlsx'.format(val['name']))

    combine_tempo()


def get_tempo_server(username = 'all', month = None):
    list_folder = lib_sys.list_folder_by_folderid(util.tempodata_id)
    if username != 'all':
        list_folder = [i for i in list_folder if i['name'].find('backup') == -1
            and i['name'].find(username) != -1]
    else:
        list_folder = [i for i in list_folder if i['name'].find('backup') == -1]

    list_username = [val['name'] for val in list_folder]

    if month is None:
        last_day = datetime.now() - timedelta(days=1)
        month = last_day.strftime('%b').upper()
        q_string =  "select * from {} where to_char(NAME) in {} "\
            "and to_char(DATETIME, 'MON') = '{}'"\
            .format(util.temponote, '(%s)' % ', '.join(map(repr, list_username)), month)

    elif month != 'all':
        q_string =  "select * from {} where to_char(NAME) in {} "\
            "and to_char(DATETIME, 'MON') = '{}'"\
            .format(util.temponote, '(%s)' % ', '.join(map(repr, list_username)), month)

    else:
        q_string =  "select * from {} where to_char(NAME) in {} "\
            .format(util.temponote, '(%s)' % ', '.join(map(repr, list_username)))

    df_note = pd.DataFrame(util.oracle_db.open_conn().query(q_string))
    df_note.columns = ['DATETIME', 'TIME', 'NAME', 'OUTCOME', 'NEXTACT']

    for name in list_username:
        output_path = util.path_output + name + '/'
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        try:
            writer = pd.ExcelWriter(output_path + 'note_server_{}.xlsx'.format(name))
            temp_df = df_note[df_note['NAME'] == name].sort_values('DATETIME')

            temp_df['DELTA_TIME'] = [datetime.strptime(i, '%H:%M:%S') for i in temp_df['TIME']]
            temp_df['DELTA_TIME'] = temp_df['DELTA_TIME'].diff().fillna(timedelta(0))
            temp_df['DELTA_TIME'] = [i.seconds / 60 for i in temp_df['DELTA_TIME']]
            temp_df['NOTE_MISSED'] = [int(i/8) for i in temp_df['DELTA_TIME']]

            temp_df.to_excel(writer, sheet_name = name, index = False)
            writer.save()

        except:
            pass

    #Combine tempo server
    list_note = []
    for root, dirs, files in os.walk(util.path_output):
        for file in files:
            if file.endswith(".xlsx") and file.find('note_server') != -1 and file.find('total') == -1:
                list_note.append(os.path.join(root, file))

    output_path = util.path_output + 'total_'
    combine_file(list_note, output_path + 'note_server.xlsx')


#def get_image_server():
#    from io import BytesIO
#    from PIL import Image
#    import numpy as np
#
#    list_name = ['tech07.qtdata_Ray', 'hr01.qtdata_Uchiha', 'law16.qtdata_Hannah', 'sale01.ahlq_Paul',
#        'onlinebusiness01_Cris', 'tech36.qtdata_Wayne', 'bot_MAL'
#    ]
#    date = '18-JAN-21'
#    for name in list_name:
#        try:
#            q_string =  "select * from {} where DATETIME like '{}' and NAME like '{}'".format(
#                util.tempomonitor, date, name)
#            df_monitor = pd.DataFrame(util.oracle_db.open_conn().query(q_string))
#            df_monitor.columns = ['DATETIME', 'TIME', 'NAME', 'IMAGE']
#            df_monitor.sort_values('DATETIME', inplace = True, ignore_index = True)
#
#            agif = imageio.get_writer('image_{}_{}.gif'.format(name, date), duration = 1)
#
#            for idx in df_monitor.index:
#                try:
#                    pre_image = BytesIO(df_monitor.loc[idx, 'IMAGE'])
#                    image = Image.open(pre_image)
#                    img = np.asarray(image)
#                    agif.append_data(img)
#                except:
#                    pass
#            agif.close()
#
#        except:
#            pass


def send_report(fromaddr, password, message_subject, toaddr='henry.duong.universes@gmail.com', cc='davidvo68.hp@gmail.com, chau.tran2015@qcf.jvn.edu.vn', bcc=''):
    import smtplib, ssl
    from email import encoders
    from email.mime.base import MIMEBase
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    port = 465  # For SSL
    smtp_server = 'mail.cmtdragon.com'
    toaddrs = [toaddr] + cc.split(',') + bcc.split(',')
    toaddrs = [s for s in toaddrs if s != '']
    # message_subject = 'TempoNote JUL-21'

    message = MIMEMultipart()
    message['Subject'] = message_subject
    message['From'] = fromaddr
    message['To'] = toaddr
    message['Cc'] = cc

    # Create the plain-text and HTML version of your message
    body = f'''
    {message_subject}
    '''

    # Add body to email
    message.attach(MIMEText(body, 'plain'))

    list_file = ['total_note.xlsx', 'total_action.xlsx', 'total_todo.xlsx', 'total_note_server.xlsx']

    for filename in list_file:
        path = util.path_output + filename

        # Open file in binary mode
        with open(path, 'rb') as attachment:
            # Add file as application/octet-stream
            # Email client can usually download this automatically as attachment
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())

        # Encode file in ASCII characters to send by email
        encoders.encode_base64(part)

        # Add header as key/value pair to attachment part
        part.add_header(
            'Content-Disposition',
            'attachment; filename=%s' % filename,
        )

        # Add attachment to message and convert message to string
        message.attach(part)

    text = message.as_string()

    # Create a secure SSL context
    context = ssl.create_default_context()

    # Try to log in to server and send email
    try:
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(fromaddr, password)
            server.sendmail(fromaddr, toaddrs, text)

        print('Email has been sent successfuly.')
    except Exception as e:
        print(e)


def add_slogan(text):
    worksheet = util.gc.open_by_key(util.spreadsheet_community_id).worksheet_by_title('Slogan')
    #Get first empty row
    cells = worksheet.get_all_values(include_tailing_empty_rows=False, include_tailing_empty=False, returnas='matrix')
    last_row = len(cells)

    new_row = [datetime.now().strftime('%Y-%m-%d %H:%M:%S'), util.username, text]
    worksheet.insert_rows(last_row, values=new_row, inherit=True)


def get_slogan():
    df_slogan = util.gc.open_by_key(util.spreadsheet_community_id).worksheet_by_title('Slogan').get_as_df()
    return df_slogan['SLOGAN'].sample().values[0]


def add_topic(text):
    worksheet = util.gc.open_by_key(util.spreadsheet_community_id).worksheet_by_title('Topic')
    #Get first empty row
    cells = worksheet.get_all_values(include_tailing_empty_rows=False, include_tailing_empty=False, returnas='matrix')
    last_row = len(cells)

    new_row = [datetime.now().strftime('%Y-%m-%d %H:%M:%S'), util.username, text]
    worksheet.insert_rows(last_row, values=new_row, inherit=True)


def get_topic(new=True):
    df_topic = util.gc.open_by_key(util.spreadsheet_community_id).worksheet_by_title('Topic').get_as_df(include_tailing_empty=True)

    if new is True:
        topic_done = df_topic[df_topic['NAME'].str.contains(util.username) == True]['TOPIC']
        # Remove topic DONE
        df_topic = df_topic[~df_topic['TOPIC'].isin(topic_done)]

    return df_topic


def update_topic(topic, tp_action):
    worksheet = util.gc.open_by_key(util.spreadsheet_community_id).worksheet_by_title('Topic')
    #Get first empty row
    cells = worksheet.get_all_values(include_tailing_empty_rows=False, include_tailing_empty=False, returnas='matrix')
    last_row = len(cells)

    new_row = [datetime.now().strftime('%Y-%m-%d %H:%M:%S'), util.username, topic, tp_action]
    worksheet.insert_rows(last_row, values=new_row, inherit=True)


def create_window_task(data, header):
    util.init_platform(fontsize = 13, theme = 'LightGreen')

    layout = [
        [sg.Button('Choose'), sg.Button('Modify')],
        [sg.Table(
            key = '-TABLE-',
            values = data,
            headings = header,
            max_col_width = 25,
            auto_size_columns = True,
            display_row_numbers = True,
            justification = 'left',
            num_rows = 10,
            alternating_row_color = 'white',
            row_height = 35
        )]
    ]

    window = sg.Window(
        'List of Tasks',
        layout,
        size = (720, 420),
        resizable = True,
        keep_on_top = True,
        finalize = True
    )

    return window






