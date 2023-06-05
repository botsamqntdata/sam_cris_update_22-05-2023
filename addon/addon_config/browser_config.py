from addon import *



random_agent = get_latest_user_agents()[0]
USER_AGENT = {'User-Agent': random_agent}
#USER_AGENT = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) ' +
#    'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36'}
#random_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) ' + \
#    'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36'

implicit_time_default = 15
min_delay_default = 10


def init_browser(headless=False, user_agent=random_agent):
    option = Options()
    #linux only
    if sys.platform == 'linux':
        option.add_argument('no-sandbox')
        option.add_argument('disable-dev-shm-usage')
        option.add_argument('disable-gpu')
        option.add_argument('disable-features=NetworkService')
        option.add_argument('disable-features=VizDisplayCompositor')

    if headless is True:
        option.add_argument('headless')
    option.add_argument('window-size=1920,1080')
    option.add_argument('hide-scrollbars')
    #option.add_argument('start-maximized')
    option.add_experimental_option('excludeSwitches', ['load-extension', 'enable-automation'])
    option.add_experimental_option('useAutomationExtension', False)
    #Pass the argument 1 to allow and 2 to block
    option.add_experimental_option('prefs', {'profile.default_content_setting_values.notifications': 2})
    option.add_experimental_option('prefs', {'intl.accept_languages': 'en, en_US'})
    option.add_argument(f'user-agent={user_agent}')

#    #fix Exception: DevToolsActivePort file doesn't exist
#    option.add_argument('--remote-debugging-port=9222')

    if sys.platform == 'win32':
        browser = webdriver.Chrome(options = option, executable_path = util.path_browser + 'chromedriver_win.exe') #windows
    elif sys.platform == 'linux':
        browser = webdriver.Chrome(options = option, executable_path = util.path_browser + 'chromedriver_linux') #linux
    else:
        browser = webdriver.Chrome(options = option, executable_path = util.path_browser + 'chromedriver_mac') #mac

    browser.implicitly_wait(implicit_time_default)

    return browser


#def print_log(log, message):
#    log += message + '\n'
#    print(message)
#
#    return log


#def init_log():
#    log = ''
#    log = print_log(log, '\n======== %s __ %s ========\n' % (
#        sys._getframe(1).f_code.co_name, datetime.now().strftime('%d-%b-%y %H:%M:%S').upper())
#    )
#
#    return log


def save_canvas(browser, classname, path):
    canvas = browser.find_element_by_css_selector('#%s' % classname)
    canvas_base64 = browser.execute_script("return arguments[0].toDataURL('image/png').substring(21);", canvas)
    canvas_png = base64.b64decode(canvas_base64)

    with open(path, 'wb') as f:
        f.write(canvas_png)

    log.printt('Output: %s\n' % path)


def remove_element(browser, element_list):
    for elementID in element_list:
        browser.execute_script("""
            var element = arguments[0];
            element.parentNode.removeChild(element);
            """, elementID)

    return browser
