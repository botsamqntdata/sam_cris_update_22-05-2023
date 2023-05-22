from addon import *



def run_notebook():
    lib_sys.init_log()
    
    try:
        browser = init_browser()
        browser.get('http://' + '118.69.153.38' + ':8888')
        
    except:
        message_error = traceback.format_exc()
        log.error(message_error)
        
        return message_error


def run_logo_maker(text_logo):
    lib_sys.init_log()
    
    try:
        browser = init_browser()
        url = 'https://editor.freelogodesign.org/?lang=en&companyname=%s' % text_logo
        browser.get(url)
        
    except:
        message_error = traceback.format_exc()
        log.error(message_error)
        
        return message_error


def run_coin_maker():
    lib_sys.init_log()
    
    if hasattr(util, 'temp_browser'):
        util.temp_browser.quit()
        delattr(util, 'temp_browser')
        
    log.printt('SAM Bot: Starting..\n')
    
    try:
        browser = init_browser()
        util.temp_browser = browser
        log.printt('Creating browser session.\n')
        
        url = 'https://www.gs-jj.com/make-your-own-coins/'
        browser.get(url)
        
        log.printt('SAM Bot: DONE.')
        
    except:
        message_error = traceback.format_exc()
        log.error(message_error)
        
        return message_error


def run_coin_maker_export():
    lib_sys.init_log()
    
    if hasattr(util, 'temp_browser'):
        try:
            browser = util.temp_browser
            log.printt('SAM Bot: Starting..\n')
            
            #front
            path_user = util.path_output + 'coin_logo_front.png'
            save_canvas(browser, 'fabricFrontCanvas', path_user)
            
            #back
            path_user = util.path_output + 'coin_logo_back.png'
            save_canvas(browser, 'fabricBackCanvas', path_user)
            
            browser.quit()
            
        except:
            util.temp_browser.quit()
            delattr(util, 'temp_browser')
            log.printt('Browser session has expired!\n')
        
        log.printt('SAM Bot: DONE.')

    else:
        log.printt('No browser session!')


def run_banner_maker(heading, subtitle, sel):
    lib_sys.init_log()
    
    try:
        browser = init_browser()
        url = 'https://placeit.net/online-banner-maker?heading=%s&subtitle=%s&sel=%s' % (heading, subtitle, sel)
        browser.get(url)
        
    except:
        message_error = traceback.format_exc()
        log.error(message_error)
        
        return message_error


def run_googletrend(search_term, geo='US'):
    lib_sys.init_log()
    
    try:
        browser = init_browser()
        url = 'https://trends.google.com/trends/explore?q=%s&geo=%s' % (search_term, geo)
        browser.get(url)
        browser.refresh()
        
    except:
        message_error = traceback.format_exc()
        log.error(message_error)
        
        return message_error


def run_goodfirms():
    lib_sys.init_log()
    
    try:
        browser = init_browser()
        url = 'https://www.goodfirms.co/directories/software/'
        browser.get(url)

    except:
        message_error = traceback.format_exc()
        log.error(message_error)
        
        return message_error


def run_keyword(keyword, method=1):    
    lib_sys.init_log()
    
    try:
        if method == 1:
            url = "http://google.com/complete/search?hl=en&output=toolbar&q=%s" % keyword
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            suggest_list = soup.find_all('suggestion')
            suggest_list = [i.get('data') for i in suggest_list]
            
        else:
            url = "https://www.google.com/search?hl=en&tbm=isch&q=%s" % keyword
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            suggest_list = soup.find_all('a', {'class' : 'TwVfHd'})
            suggest_list = [i.contents[0] for i in suggest_list]
            
        suggest_output = '\n'.join(suggest_list)
        log.printt(suggest_output)
        
        return suggest_output

    except:
        message_error = traceback.format_exc()
        log.error(message_error)
        
        return message_error
        

def run_tineye(keyword):    
    lib_sys.init_log()
    
    try:
        browser = init_browser()
        
        size = browser.get_window_size()
        browser.minimize_window()
        url_google = "https://www.google.com/search?tbm=isch&q=%s" % keyword
        browser.get(url_google)
        time.sleep(2)
        src = browser.find_elements_by_xpath('//img[@class="rg_i Q4LuWd"]')[0].get_attribute('src')
        img_path = os.getcwd() + '/output/temp_%s.png' % keyword
        urllib.request.urlretrieve(src, img_path)
        time.sleep(2)
        
        url_tineye = 'https://tineye.com/'
        browser.get(url_tineye)
        time.sleep(2)
        
        elementID = browser.find_elements_by_xpath('//input[@type="file"]')[0]
        elementID.send_keys(img_path)
        time.sleep(2)
        
        os.remove(img_path)
        browser.set_window_size(size['width'], size['height'])
        
    except:
        message_error = traceback.format_exc()
        log.error(message_error)
        
        return message_error




