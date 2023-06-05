import PySimpleGUI as sg
import os, sys
import traceback
import argparse
from datetime import datetime
import time
import json
import pyscreenshot as ImageGrab
import cv2
import base64
import imageio
from io import BytesIO
from PIL import Image, ImageTk
import shutil
import pandas as pd
import numpy as np
from random import randint
import textwrap

import util
from lib import lib_tempo, lib_sys
from config.logger import log_temponote, log_tempomonitor
from addon.task_management.func import clickup_task



def encode_b64(image_pil):
    if image_pil.mode != 'RGB':
        image_pil = image_pil.convert('RGB')
    buff = BytesIO()
    image_pil.save(buff, format = 'png')
    image_b64 = base64.b64encode(buff.getvalue()).decode('utf-8')

    return image_b64


def snapshot():
    #Grabbing images
    try:
        screen = ImageGrab.grab()
        screen = np.array(screen)
        try:
            if sys.platform == 'win32':
                video_capture = cv2.VideoCapture(0 + cv2.CAP_DSHOW)
            else:
                video_capture = cv2.VideoCapture(0)

            #Fix black screen issue
            video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

            ret, frame = video_capture.read()
            cv2.waitKey(30)
            video_capture.release()

            #Convert to PIL Image
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        except:
            frame = screen

    except:
        log_temponote.warning('Cannot capture images!')
        log_temponote.warning(traceback.format_exc())
        frame = 'None'
        screen = 'None'

    return frame, screen


def capture_images(timer_monitor, temp_id):
    monitor_start = time.time()
    popup_first_run = True
    date_filename = datetime.now().strftime('%d-%b-%y').upper()
    date_position = (10, 40)
    image_path = util.path_note + 'image_{}_{}.gif'.format(util.username, date_filename)
#    temp_image_path = util.path_note + 'temp_image_{}_{}.gif'.format(util.username, date)
    first_image = False
    if not os.path.exists(image_path):
        imageio.get_writer(image_path, duration = 1)
        first_image = True

    num_oraclecheck = 0
    while True:
        try:
            #Capture image
            if time.time() > monitor_start + timer_monitor or popup_first_run:
                monitor_start = time.time()
                popup_first_run = False

                now_temp = datetime.now()
                current_time = now_temp.strftime('%H:%M:%S')
                date = now_temp.strftime('%d-%b-%y').upper()
                date_server = now_temp.strftime('%Y-%m-%d %H:%M:%S')

                #Remove no use .gif
                try:
                    os.remove(util.path_note + 'new.gif')
                    os.remove(util.path_note + 'temp.gif')
                except:
                    pass

                webcam, screen = snapshot()

                with imageio.get_writer(util.path_note + 'new.gif') as writer_screen:
                    #crop webcame to overlay a webcame image on a screen image
                    crop_webcam = webcam[100:800, 350:1050]
                    crop_webcam = cv2.resize(crop_webcam, (300, 300))
                    x_offset = y_offset = 0
                    if screen.shape[2] == 4 and crop_webcam.shape[2] == 3: #reduce dimension
                        screen = np.delete(screen, 3, axis=2)
                    screen[y_offset:y_offset+crop_webcam.shape[0], x_offset:x_offset+crop_webcam.shape[1]] = crop_webcam
                    #concat_image = cv2.hconcat([crop_webcam, crop_webcam])
                    cv2.putText(
                        screen, #numpy array on which text is written
                        '{}'.format(date), #text
                        date_position, #position at which writing has to start
                        cv2.FONT_HERSHEY_SIMPLEX, #font family
                        1.3, #font size
                        (0, 0, 255), 3
                    )
                    #Image.save(image_path, save_all = True, append_images = screen)
                    writer_screen.append_data(screen)
                writer_screen.close()

                try:
                    #Create writer object temp.gif
                    temp_gif = imageio.get_writer(util.path_note + 'temp.gif', duration = 1)
                    #Load old gif
                    if not first_image:
                        old_gif = imageio.get_reader(image_path)
                        for im in old_gif:
                            temp_gif.append_data(im)

                    temp_gif.append_data(screen)
                    temp_gif.close()
                    #Replace current by temp
                    shutil.move(util.path_note + 'temp.gif', image_path)
                    first_image = False

                except:
                    log_tempomonitor.warning(traceback.format_exc())
                    pass

                if num_oraclecheck <= 3:
                    try:
                        #Upload latest image to Oracle database
                        screen = cv2.cvtColor(screen, cv2.COLOR_BGR2RGB)
                        is_success, im_buf_arr = cv2.imencode('.jpg', screen)
                        byte_im = im_buf_arr.tobytes()
                        util.oracle_db.open_conn().query(
                            "INSERT INTO {}(DATETIME, TIME, NAME, IMAGE) \
                            VALUES(TO_DATE(:datetime, 'yyyy-mm-dd hh24:mi:ss'), :time, :name, :image)".format(
                            util.tempomonitor),
                            {
                                'datetime': date_server,
                                'time': current_time,
                                'name': util.username,
                                'image': byte_im
                            }
                        )

                    except:
                        num_oraclecheck += 1
#                        #Store note in temp file if have issue
#                        tempmissed_gif = imageio.get_writer(util.path_note + 'tempmissed.gif', duration = 1)
#                        try:
#                            #Load old gif
#                            temp_old_gif = imageio.get_reader(temp_image_path)
#
#                            for frame_number in range(temp_old_gif.get_length()):
#                                img = temp_old_gif.get_next_data()
#                                tempmissed_gif.append_data(img)
#                            temp_old_gif.close()
#
#                        except:
#                            log_tempomonitor.warning(traceback.format_exc())
#                            pass
#
#                        new_gif = imageio.get_reader(util.path_note + 'new.gif')
#                        img = new_gif.get_next_data()
#                        tempmissed_gif.append_data(img)
#
#                        new_gif.close()
#                        tempmissed_gif.close()
#
#                        shutil.move(util.path_note + 'tempmissed.gif', temp_image_path)
                        pass
                else:
                    #Upload latest gif to temp folder on Drive
                    lib_tempo.push_file('new.gif', util.path_note + 'new.gif', temp_id)

#                    #Store note in temp file if have issue
#                    tempmissed_gif = imageio.get_writer(util.path_note + 'tempmissed.gif', duration = 1)
#                    try:
#                        #Load old gif
#                        temp_old_gif = imageio.get_reader(temp_image_path)
#
#                        for frame_number in range(temp_old_gif.get_length()):
#                            img = temp_old_gif.get_next_data()
#                            tempmissed_gif.append_data(img)
#                        temp_old_gif.close()
#
#                    except:
#                        log_tempomonitor.warning(traceback.format_exc())
#                        pass
#
#                    new_gif = imageio.get_reader(util.path_note + 'new.gif')
#                    img = new_gif.get_next_data()
#                    tempmissed_gif.append_data(img)
#
#                    new_gif.close()
#                    tempmissed_gif.close()
#
#                    shutil.move(util.path_note + 'tempmissed.gif', temp_image_path)

            time.sleep(max(0, timer_monitor - time.time() + monitor_start) + randint(0, 15))

        except:
            log_tempomonitor.warning(traceback.format_exc())
            pass


def update_sg_text(sg_text, text):
    sg_text.Widget.configure(wraplength=500)
    sg_text.update(text)
    sg_text.set_size((0, 0))
    # sg_text.set_tooltip(text)


def create_window_note():
    util.init_platform(fontsize = 15, theme = 'TanBlue')

    layout_note = [
        [sg.Text('Outcome', key='-LABEL1-')],
        [sg.InputText(key='-OUTCOME-', focus=True)],
        [sg.Text('Next Activity', key='-LABEL2-')],
        [sg.InputText(key='-NEXTACT-')],
    ]

    layout_action = [
        [sg.Text('Outcomes', key='-ACTION_LABEL1-')],
        [sg.Multiline(key='-OUTCOMES-', size=(60, 2), focus=True)],
        [sg.Text('Activities', key='-ACTION_LABEL2-')],
        [sg.Multiline(key='-ACTIVITIES-', size=(60, 2))],
        [sg.Text('Conclusion & Action', key='-TOPIC-')],
        [sg.Multiline(key='-ACTION-', size=(60, 10))],
    ]

    layout = [
        [sg.Text('Slogan', key='-SLOGAN-')],
        [sg.Text('Doing Task:\n{}'.format(util.task_doing), key='-TASK-'), sg.Button('Change')],
        [sg.Text(key='-TIME-', size=(20, 1))],
        [sg.Column(layout_note, key='-LAYOUT_NOTE-'), sg.Column(layout_action, visible=False, key='-LAYOUT_ACTION-')],
        [sg.Submit(key='-SUBMIT-', bind_return_key=True)]
    ]

    window = sg.Window(
        'TempoNote 5000',
        layout,
        disable_close = True,
        keep_on_top = True,
        finalize = True
    )

    #Update slogan
    try:
        slogan = lib_tempo.get_slogan()
        update_sg_text(window['-SLOGAN-'], slogan)

    except:
        pass

    #Update discussion topic
    try:
        df_topic = lib_tempo.get_topic(new=True)
        topic_new = df_topic['TOPIC']
        if len(topic_new) > 0:
            topic = topic_new.sample().values[0] + '\n\nConclusion & Action'
            update_sg_text(window['-TOPIC-'], topic)

    except:
        pass

    window.Element('-SUBMIT-').Update(visible=False)

    return window


def change_doingtask(window):
    bot_task = clickup_task.bot_task()
    df_task = bot_task.run_list_task('daily') #call function from addon task_management
    data = df_task.values.tolist()
    header = df_task.columns.tolist()
    window_task = lib_tempo.create_window_task(data, header)

    while True:
        try:
            event_task, values_task = window_task.read()
            if event_task == sg.TIMEOUT_KEY:
                pass
            if event_task == 'Choose':
                task_index = values_task.get('-TABLE-')[0]
                util.task_doing = data[task_index][1]
                update_sg_text(window['-TASK-'], 'Doing Task:\n{}'.format(util.task_doing))
                window_task.close()
                break

            if event == sg.WIN_CLOSED:
                window_task.close()
                break

        except UnicodeDecodeError:
            pass

        except KeyboardInterrupt:
            pass

        except:
            log_temponote.warning('Window Task error')
            log_temponote.warning(traceback.format_exc())
            window_task.close()
            break


def run_popup_note(timer_popup, timer_action, timer_exist, temp_id):
    #Init
    popup_start = time.time()
    action_start = time.time()
    timer_exist_default = timer_exist
    action_is_on = False
    popup_first_run = True
    date_filename = datetime.now().strftime('%d-%b-%y').upper()
    prev_act = ''
    prev_outcome = ''
    prev_action = ''

    action_path = util.path_note + 'action_{}_{}.json'.format(util.username, date_filename)
    if not os.path.exists(action_path):
        with open(action_path, 'w+') as file:
            json.dump([], file)
        json_action = []
    else:
        #Load json data
        with open(action_path, 'r') as file:
            json_action = json.load(file)

    note_path = util.path_note + 'note_{}_{}.json'.format(util.username, date_filename)
    if not os.path.exists(note_path):
        with open(note_path, 'w+') as file:
            json.dump([], file)
        json_note = []
    else:
        #Load json data
        with open(note_path, 'r') as file:
            json_note = json.load(file)

    temp_note_path = util.path_note + 'temp_note_{}_{}.json'.format(util.username, date_filename)
    if not os.path.exists(temp_note_path):
        with open(temp_note_path, 'w+') as file:
            json.dump([], file)
        json_tempnote = []
    else:
        #Load temp json data
        with open(temp_note_path, 'r') as file:
            json_tempnote = json.load(file)

    num_oraclecheck = 0
    while True:
        try:
            #Create note
            if time.time() > popup_start + timer_popup or popup_first_run:
                window = create_window_note()
                popup_start = time.time()
                popup_first_run = False

                now_temp = datetime.now()
                current_time = now_temp.strftime('%H:%M:%S')
                date = now_temp.strftime('%d-%b-%y').upper()
                date_server = now_temp.strftime('%Y-%m-%d %H:%M:%S')

                window.Element('-TIME-').Update('Time: {}'.format(current_time))

                if time.time() > action_start + timer_action:
                    action_is_on = True
                    action_start = time.time()
                    temp_start = time.time()

                    #Update layout action
                    window['-LAYOUT_NOTE-'].update(visible=False)
                    window['-LAYOUT_ACTION-'].update(visible=True)
                    window['-OUTCOMES-'].set_focus()
                    window['-SUBMIT-'].update(visible=True)

                    timer_exist = timer_exist_default * 3
                else:
                    timer_exist = timer_exist_default

                tp_act = 'None'
                tp_outcome = 'None'
                tp_action = 'None'

                while True:
                    event, values = window.read(timeout = 100)
                    if event == sg.TIMEOUT_KEY:
                        tp_outcome = values['-OUTCOME-']
                        tp_act = values['-NEXTACT-']
                        topic = window['-TOPIC-'].get().replace('\n\nConclusion & Action', '')

                        if action_is_on:
                            tp_outcome = values['-OUTCOMES-']
                            tp_act = values['-ACTIVITIES-']
                            tp_action = values['-ACTION-']
                        pass

                    if event == 'Change':
                        change_doingtask(window)
                        pass

                    if time.time() > popup_start + timer_exist:
                        window.Hide()
                        window.Close()
                        break

                    if action_is_on:
                        if time.time() > temp_start + timer_exist_default:
                            lib_tempo.append_note('Note Task 1h: outcomes, activities, conclusion & action.')
                            temp_start = time.time()

                        if tp_act is not None and tp_outcome is not None and tp_action is not None \
                        and len(tp_act) > 0 and len(tp_outcome) > 0 and len(tp_action) > 0 \
                        and event == '-SUBMIT-':
                            if topic != 'Conclusion & Action':
                                #Update action on Topic sheet
                                if len(tp_action) >= 300:
                                    lib_tempo.update_topic(topic, tp_action)

                                else:
                                    sg.popup('Action requires at least 300 characters with Proof. Current: {}.'.format(len(tp_action)),
                                        location = (500, 300),
                                        keep_on_top = True)
                                    continue

                            if prev_act != tp_act and prev_outcome != tp_outcome and prev_action != tp_action:
                                prev_act = tp_act
                                prev_outcome = tp_outcome
                                prev_action = tp_action
                                window.Hide()
                                window.Close()
                                break

                            else:
                                sg.popup('Note is duplicated. Please enter a new one.',
                                    location = (500, 300),
                                    keep_on_top = True)

                            # #Update action on Topic sheet
                            # if len(tp_action) >= 300:
                            #     topic = window['-TOPIC-'].get().replace('\n\nConclusion & Action', '')
                            #     if topic != 'Conclusion & Action':
                            #         lib_tempo.update_topic(topic, tp_action)
                            #
                            #     if prev_act != tp_act and prev_outcome != tp_outcome and prev_action != tp_action:
                            #         prev_act = tp_act
                            #         prev_outcome = tp_outcome
                            #         prev_action = tp_action
                            #         window.Hide()
                            #         window.Close()
                            #         break
                            #
                            #     else:
                            #         sg.popup('Action is duplicated. Please enter a new one.',
                            #             location = (500, 300),
                            #             keep_on_top = True)
                            #
                            # else:
                            #     sg.popup('Action requires at least 300 characters with Proof.',
                            #         location = (500, 300),
                            #         keep_on_top = True)

                    else:
                        if tp_act is not None and tp_outcome is not None \
                        and len(tp_outcome) > 0 and len(tp_act) > 0 \
                        and event == '-SUBMIT-':
                            if len(util.task_doing) == 0:
                                sg.popup('Click "Change" to select new task.',
                                    location = (500, 300),
                                    keep_on_top = True)
                                continue

                            if prev_act != tp_act and prev_outcome != tp_outcome:
                                prev_act = tp_act
                                prev_outcome = tp_outcome
                                window.Hide()
                                window.Close()
                                break

                            else:
                                sg.popup('Note is duplicated. Please enter a new one.',
                                    location = (500, 300),
                                    keep_on_top = True)

                #Create json file and upload
                if tp_act == '':
                    tp_act = 'SAM issue.'
                if tp_outcome == '':
                    tp_outcome = 'SAM issue.'
                if tp_action == '':
                    tp_action = 'SAM issue.'

                if action_is_on:
                    dict_action = {
                        'DATETIME': date,
                        'TIME': current_time,
                        'NAME': util.username,
                        'TASK': util.task_doing,
                        'ACTIVITIES': tp_act,
                        'OUTCOMES': tp_outcome,
                        'ACTION': tp_action,
                        # 'THUMBSUP': util.username
                    }

                    #Write to note file
                    json_action.append(dict_action)
                    with open(action_path, 'w') as file:
                        json.dump(json_action, file)

                    action_is_on = False

                dict_note = {
                    'DATETIME': date,
                    'TIME': current_time,
                    'NAME': util.username,
                    'TASK': util.task_doing,
                    'OUTCOME': tp_outcome,
                    'NEXTACT': tp_act
                }

                #Write to note file
                json_note.append(dict_note)
                with open(note_path, 'w') as file:
                    json.dump(json_note, file)

                if num_oraclecheck <= 3:
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
                                'outcome': tp_outcome,
                                'nextact': tp_act
                             }
                        )

                    except:
                        num_oraclecheck += 1
                        #Store note in temp file if have issue
                        json_tempnote.append(dict_note)
                        with open(temp_note_path, 'w') as fp:
                            json.dump(json_tempnote, fp)
                        pass
                else:
                    latest_note_path = util.path_note + 'temp_note.json'
                    with open(latest_note_path, 'w') as fp:
                        json.dump([dict_note], fp)

                    #Upload latest note to temp folder
                    lib_tempo.push_file('temp_note.json', util.path_note + 'temp_note.json', temp_id)

                    #Store note in temp file if have issue
                    json_tempnote.append(dict_note)
                    with open(temp_note_path, 'w') as fp:
                        json.dump(json_tempnote, fp)
                    pass

            time.sleep(max(0, timer_popup - time.time() + popup_start) + randint(0, 15))

        except UnicodeDecodeError:
            pass

        except KeyboardInterrupt:
            pass

        except:
            log_temponote.warning(traceback.format_exc())
            pass


def create_window_monitor(list_checkname):
    util.init_platform(fontsize = 13, theme = 'LightGreen')
    check_user = []

    for username in list_checkname:
        check_user.append([
            sg.Text(key = 'name_{}'.format(username), size = (25, 1))
        ])
        check_user.append([
            sg.Text('Task:', size = (5, 1)),
            sg.Text(key = 'task_{}'.format(username), size = (20, 1))
        ])
        check_user.append([
            sg.Text('Act:', size = (5, 1)),
            sg.Text(key = 'act_{}'.format(username), size = (20, 1))
        ])
        check_user.append([
            sg.Text('Outcome:', size = (8, 1)),
            sg.Text(key = 'outcome_{}'.format(username), size = (20, 1))
        ])
        check_user.append([
            sg.Image(key = 'image_{}'.format(username), size = (250, 160))
        ])
        check_user.append([
            sg.Button('zoom_{}'.format(username))
        ])

    if len(list_checkname) >= 2:
        layout = [
            [sg.Column(check_user, size = (300, 1000), vertical_scroll_only = True, scrollable = True)]
        ]
    else:
        layout = check_user

    window = sg.Window(
        'TempoMonitor',
        layout,
        location = (sg.Window.get_screen_size()[0] - 300, 0),
        keep_on_top = True,
        finalize = True,
        size = (300, 320),
        resizable = True
    )
    return window


def run_popup_monitor(timer_monitor = 30):
    try:
        list_checkname = get_list_checkname()
    except:
        sg.Popup('Error: list_checkname has no value.', title = 'Tempo Monitor', keep_on_top = True)

    window = create_window_monitor(list_checkname)
    monitor_start = time.time()
    popup_first_run = True
    num_oraclecheck = 0

    while True:
        try:
#            event, values = window.read(timeout = 1000 * timer_monitor)
            event, values = window.read(timeout = 100)
            if event == sg.TIMEOUT_KEY:
                if time.time() > monitor_start + timer_monitor or popup_first_run:
                    monitor_start = time.time()
                    popup_first_run = False

                    if num_oraclecheck <= 3:
                        try:
                            #Get list of latest image
                            q_string =  "select * from {} where to_char(NAME) in {} "\
                                "and DATETIME in (select max(DATETIME) from {} group by to_char(NAME))"\
                                .format(util.tempomonitor, '(%s)' % ', '.join(map(repr, list_checkname)), util.tempomonitor)
                            df_monitor = pd.DataFrame(util.oracle_db.open_conn().query(q_string))
                            df_monitor.columns = ['DATETIME', 'TIME', 'NAME', 'IMAGE']
                            df_monitor = df_monitor.drop_duplicates(subset = 'NAME', keep = 'last')

                            #Get list of latest note
                            q_string =  "select * from {} where to_char(NAME) in {} "\
                                "and DATETIME in (select max(DATETIME) from {} group by to_char(NAME))"\
                                .format(util.temponote, '(%s)' % ', '.join(map(repr, list_checkname)), util.temponote)
                            df_note = pd.DataFrame(util.oracle_db.open_conn().query(q_string))
                            df_note.columns = ['DATETIME', 'TIME', 'NAME', 'OUTCOME', 'NEXTACT']
                            df_note = df_note.drop_duplicates(subset = 'NAME', keep = 'last')

                            for username in list_checkname:
                                user_path = util.path_monitor + username + '/'
                                if not os.path.exists(user_path):
                                    os.makedirs(user_path)

                                try:
                                    pre_image = BytesIO(df_monitor.loc[df_monitor['NAME'] == username, 'IMAGE'].values[0])
                                    image = Image.open(pre_image)
                                    image.save(user_path + 'new.gif')

                                except:
                                    pass

                                try:
                                    dict_note = {
                                        'NAME': df_note.loc[df_note['NAME'] == username, 'NAME'].values[0],
                                        'OUTCOME': df_note.loc[df_note['NAME'] == username, 'OUTCOME'].values[0],
                                        'NEXTACT': df_note.loc[df_note['NAME'] == username, 'NEXTACT'].values[0]
                                    }
                                    with open(user_path + 'temp_note.json', 'w') as fp:
                                        json.dump(dict_note, fp)

                                except:
                                    pass

                        except:
                            num_oraclecheck += 1
                            for username in list_checkname:
                                try:
                                    lib_tempo.get_current_status(username)
                                except:
                                    continue

                    else:
                        for username in list_checkname:
                            try:
                                lib_tempo.get_current_status(username)
                            except:
                                continue

                    for username in list_checkname:
                        user_path = util.path_monitor + username + '/'
                        try:
                            task = 'None'

                            with open(user_path + 'temp_note.json', 'r') as file:
                                json_note = json.load(file)
                            act = json_note['NEXTACT']
                            outcome = json_note['OUTCOME']

                            window.Element('name_{}'.format(username)).Update(username)
                            window.Element('task_{}'.format(username)).Update(task)
                            window.Element('act_{}'.format(username)).Update(act)
                            window.Element('outcome_{}'.format(username)).Update(outcome)

                        except:
                            pass

                        try:
                            image = Image.open(user_path + 'new.gif')
                            image = image.resize((250, 160), Image.ANTIALIAS)
                            window.Element('image_{}'.format(username)).Update(data = ImageTk.PhotoImage(image))

                        except:
                            continue

                continue

            for username in list_checkname:
                if event == 'zoom_{}'.format(username):
                    Image.open(util.path_monitor + username + '/' + 'new.gif').show()
                    break

            if event == sg.WIN_CLOSED:
                window.Close()
                break

        except UnicodeDecodeError:
            pass

        except KeyboardInterrupt:
            pass

        except:
            log_tempomonitor.warning(traceback.format_exc())
            window.Close()
            break


def create_window_member(data, header):
    util.init_platform(fontsize = 13, theme = 'LightGreen')

    layout = [
        [sg.Button('Add'), sg.Button('Remove')],
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
        )],
        [sg.Output(key = '-OUT-', size = (29, 20))],
    ]

    window = sg.Window(
        'List of Members',
        layout,
        keep_on_top = True,
        size = (290, 500),
        resizable = True
    )

    return window


def get_list_checkname():
    df_checkname = pd.DataFrame(columns = ['CODE'])
    list_username = lib_sys.list_folder_by_folderid(util.tempodata_id)
    list_username = [i for i in list_username if i['name'].find('backup') == -1]
    for idx, val in enumerate(list_username):
        df_checkname.loc[idx, 'CODE'] = val['name']

    data = df_checkname.values.tolist()
    header = df_checkname.columns.tolist()
    window = create_window_member(data, header)
    list_checkname = []

    while True:
        try:
            event, values = window.read()
            if event == 'Add':
                member_index = values.get('-TABLE-')[0]
                list_checkname.append(df_checkname.loc[member_index, 'CODE'])
                list_checkname = list(set(list_checkname))
                window.Element('-OUT-').update('{}\n'.format(list_checkname))

            if event == 'Remove':
                member_index = values.get('-TABLE-')[0]
                try:
                    list_checkname.remove(df_checkname.loc[member_index, 'CODE'])
                except:
                    pass
                window.Element('-OUT-').update('{}\n'.format(list_checkname))

            if event == sg.WIN_CLOSED:
                window.close()
                break

        except UnicodeDecodeError:
            pass

        except KeyboardInterrupt:
            pass

        except:
            log_temponote.warning(traceback.format_exc())
            window.Close()
            break

    return list_checkname



if __name__ == '__main__':
    parser = argparse.ArgumentParser('Tempo Popup')
    parser.add_argument('-c', '--capture-images', help = 'Capture images', default = 'off')
    parser.add_argument('-n', '--popup-note', help = 'Run Tempo Note', default = 'off')
    parser.add_argument('-m', '--popup-monitor', help = 'Run Tempo Monitor', default = 'off')
    args = parser.parse_args()

# ================================================================
    if args.capture_images == 'on':
        capture_images(util.timer_monitor, util.temp_id)

    if args.popup_note == 'on':
        run_popup_note(util.timer_popup, util.timer_action, util.timer_exist, util.temp_id)

    if args.popup_monitor == 'on':
        run_popup_monitor(timer_monitor=30)




