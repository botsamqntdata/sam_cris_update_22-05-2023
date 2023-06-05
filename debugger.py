import PySimpleGUI as sg
import sys
import traceback

import util
from lib import *
from addon import *
from config.logger import log_debugger



def create_window_debugger():
    sg.theme('LightGreen')
    
    #Comment next 2 lines or change the number if window size is too big/small
    if sys.platform != 'win32':
        sg.set_options(font = ('Helvetica', 11))
    
    layout = [
        [
            sg.Text('>>>'),
            sg.Input(key = '-IN-', size = (798, 15))
        ],
        [sg.Output(key = '-OUT-', size = (800, 800))],
        [sg.Submit(key = '-SUBMIT-', bind_return_key = True)]
    ]

    window = sg.Window(
    'SAM_Server',
    layout,
    size = (800, 500),
#    keep_on_top = True,
    resizable = True,
    finalize = True
    )
    window.Element('-SUBMIT-').Update(visible = False)
    
    return window

    
def run_popup_debugger():
    window = create_window_debugger()
    cmd = ''
    
    while True:
        try:
            event, values = window.Read(timeout = 100)
            if event == sg.TIMEOUT_KEY:
                cmd = values['-IN-']
                pass
            
            if cmd is not None and len(cmd) > 0 and event == '-SUBMIT-':
                    window.Element('-IN-').update('')
                    result = '>>> {}\n'.format(cmd)
                    
                    try:             
                        result += '{}'.format(eval('{}'.format(cmd)))               
                    except Exception as e:
                        if sys.version_info[0] < 3:
                            result += '{}'.format('Not available in Python 2')
                        else:
                            try:
                                result += '{}'.format(exec('{}'.format(cmd)))
                            except Exception as e:
                                result += '{}'.format('Exception {}'.format(e))
                                
                    window.Element('-OUT-').update('{}\n'.format(result))
                      
            if event == sg.WIN_CLOSED:
                lib_tempo.checkout(append=False)
                window.Close()
                break
         
        except UnicodeDecodeError:
            pass     
        
        except KeyboardInterrupt:
            pass
        
        except:
            log_debugger.warning(traceback.format_exc())
            lib_tempo.checkout()
            window.Close()
            break


        
if __name__ == '__main__':
    run_popup_debugger()
    
    
    
    
    