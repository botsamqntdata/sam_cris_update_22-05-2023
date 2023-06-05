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
from config.logger import log_debugger



def checkin():
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
    
    return 'Start TempoNote: {}\nStart Capture Images: {}'.format(util.temponote_pid, util.capimgs_pid)


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
    
    return 'Reset {} - {}: DONE.'.format(
        datetime.fromtimestamp(time_start).strftime('%H:%M:%S'),
        datetime.fromtimestamp(time_end).strftime('%H:%M:%S')
    )


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
            "INSERT INTO {}(DATETIME, TIME, NAME, OUTCOME, NEXTACT) \
            VALUES(TO_DATE(:datetime, 'yyyy-mm-dd hh24:mi:ss'), :time, :name, :outcome, :nextact)".format(
            util.temponote),
            {
                'datetime': date_server,
                'time': current_time,
                'name': util.username,
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




