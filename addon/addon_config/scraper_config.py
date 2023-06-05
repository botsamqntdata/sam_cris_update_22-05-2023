from addon import *



def convert_ascii(string):
    dict_ascii = {':':'%3A', '/':'%2F', '&':'%26', "'":'%27'}
    res = ''.join([dict_ascii.get(i, i) for i in string])

    return res


def fetch_results(search_term, num_result=None, language_code='en', sup_page=None, user_agent=USER_AGENT):
    assert isinstance(search_term, str), 'Search term must be a string'
#    assert isinstance(num_result, int), 'Number of results must be an integer'

    escaped_search_term = search_term.replace(' ', '+')
    if type(sup_page) == str:
        sup_page_term = sup_page.replace(' ', '+')
        escaped_search_term = escaped_search_term + '+' + sup_page_term

    if num_result is not None:
        url = f'https://www.google.com/search?q={escaped_search_term}&num={num_result}&hl={language_code}'
    else:
        url = f'https://www.google.com/search?q={escaped_search_term}'

    response = requests.get(url, headers=user_agent)
    response.raise_for_status()

    return response.text


def parse_results(html, classname='div', att={'class': 'fG8Fp uo4vr'}):
    soup = BeautifulSoup(html, 'html.parser')

    found_results = pd.DataFrame(columns=['link', 'title', 'info'])
    result_block = soup.find_all('div', attrs={'class': 'g'})
    for result in result_block:
        link = result.find('a', href=True)
        title = result.find('h3')
        info = result.find(classname, attrs=att)

        if link and title:
            link = link['href']
            title = title.text
            if info:
                info = info.text
            if link != '#':
                found_results = found_results.append(
                    {'link': link, 'title': title, 'info': info},
                    ignore_index = True
                )

    return found_results


def tag_visible(element):
    if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    return True


def text_from_html(body):
    #soup = BeautifulSoup(body, 'html.parser')
    texts = body.findAll(text = True)
    visible_texts = filter(tag_visible, texts)
    return u" ".join(t.strip() for t in visible_texts)


def get_fulltext(html,part = 'body'):
    texts = html.find(part)
    texts = text_from_html(texts)
    return texts


def scrape_google(search_term, num_result, language_code='en', sup_page=None):
    try:
        html = fetch_results(search_term, num_result, language_code, sup_page)
        results_list = parse_results(html, classname='div', att={'class': 'IsZvec'})
        return results_list

    except AssertionError:
        raise Exception("Incorrect arguments parsed to function")
    except requests.HTTPError:
        raise Exception("You appear to have been blocked by Google")
    except requests.RequestException:
        raise Exception("Appears to be an issue with your connection")


def run_url_crawler(url, classname, att, column = [], filename = None, method = 1, engine = 1):
    lib_sys.init_log()

    if engine == 2: #run with selenium
        log.printt('Run with Selenium.')

        #Open link on chrome
        browser = init_browser()
        browser.get(url)
        time.sleep(random.uniform(5, 10))

        html = browser.page_source
        browser.quit()
        soup = BeautifulSoup(html, 'html.parser')

    elif engine == 3: #run with selenium on server
        log.printt('Run with Selenium on server.')

    else: #run without selenium
        log.printt('Run without Selenium.')

        response = requests.get(url, headers = USER_AGENT)
        soup = BeautifulSoup(response.text, 'html.parser')

    log.printt('Crawling Bot: START crawling..\n')

    if column == []:
        column = [classname + ', ' + str(att)]

    data = pd.DataFrame(columns = column)
    if method == 1:
        result_block = soup.find_all(classname, attrs = att)
    else:
        result_block = soup.select(classname, att)

    for idx, result in enumerate(result_block):
        data.loc[idx, column[0]] = result.text

    log.printt('%s\n' % data[:5])

    if filename is None:
        filename = 'crawler_%s.xlsx' % (datetime.now().strftime('_%Y%m%d_%H%M%S'))

    path = util.path_output + filename
    export_file(data, path)

    log.printt('Crawling Bot: DONE.')


def run_url_crawler_multi(url, classname, att, start=0, end=1):
    lib_sys.init_log()
    log.printt('Run without Selenium.')

    column = [classname + ', ' + str(att)]
    data = pd.DataFrame(columns = column)
    log.printt('Crawling Bot: START crawling..\n')

    for i in range(start, end):
        try:
            data_temp = pd.DataFrame(columns = column)
            url_temp = url + str(i)
            response = requests.get(url_temp, headers = USER_AGENT)
            soup = BeautifulSoup(response.text, 'html.parser')
            result_block = soup.find_all(classname, attrs = att)

            for idx, result in enumerate(result_block):
                data_temp.loc[idx, column[0]] = result.text
#            log = print_log(log, '%s\n' % data_temp.loc[:5])
            data = pd.concat([data, data_temp], ignore_index=True)
            time.sleep(5)
        except:
            pass

    log.printt('%s\n' % data[:5])

    filename = 'crawler_%s.xlsx' % (datetime.now().strftime('_%Y%m%d_%H%M%S'))

    path = util.path_output + filename
    export_file(data, path)

    log.printt('Crawling Bot: DONE.')


def run_recaptcha_solver(captcha_link):
    import urllib
    import speech_recognition as sr

    print('Changing User Agent..')
    new_agent = {'User-Agent': get_latest_user_agents()[0]}
    print(new_agent)

    browser = init_browser(headless=False, user_agent=new_agent)

    browser.get(captcha_link)
#    browser.get('https://www.google.com/recaptcha/api2/demo')
    time.sleep(5)

    # switch to recaptcha frame
    frames = browser.find_elements_by_tag_name('iframe')
    browser.switch_to.frame(frames[0])
    time.sleep(1)

    browser.find_element_by_class_name('recaptcha-checkbox-border').click()
    browser.switch_to.default_content()
    frames = browser.find_element_by_xpath('/html/body/div[2]/div[4]').find_elements_by_tag_name('iframe')
    browser.switch_to.frame(frames[0])
    time.sleep(1)

    # click random images
    elements = browser.find_elements_by_xpath('//td[@role="button"]')
    for el in elements[:3]:
        el.click()
    time.sleep(1)

    browser.find_element_by_id('recaptcha-verify-button').click()
    time.sleep(1)

    browser.switch_to.default_content()
    button = browser.find_element_by_xpath('/html/body/div[1]')
    ActionChains(browser).move_to_element_with_offset(button, 20, 20).click().perform()

    # switch to recaptcha audio challenge frame
    frames = browser.find_elements_by_tag_name('iframe')
    browser.switch_to.frame(frames[0])
    time.sleep(1)

    browser.find_element_by_class_name('recaptcha-checkbox-border').click()
    browser.switch_to.default_content()
    frames = browser.find_element_by_xpath('/html/body/div[2]/div[4]').find_elements_by_tag_name('iframe')
    browser.switch_to.frame(frames[0])
    time.sleep(1)

    browser.find_element_by_id('recaptcha-audio-button').click()
    browser.switch_to.default_content()
    frames = browser.find_elements_by_tag_name('iframe')
    browser.switch_to.frame(frames[-1])
    time.sleep(1)

    # download the mp3 audio file
    try:
        mp3_src = browser.find_element_by_id('audio-source').get_attribute('src')
#            print('Audio source: %s' % mp3_src)
        urllib.request.urlretrieve(mp3_src, util.path_config +'sound/audio.mp3')
        time.sleep(1)
    except Exception as e:
        return "\nYour computer or network may be sending automated queries.\n" + \
            "To protect our users, we can't process your request right now."

    # convert downloaded mp3 audio file to wav
    browser_temp = init_browser(headless=False, user_agent=new_agent)
    browser_temp.get('https://www.freeconvert.com/mp3-to-wav')
    time.sleep(5)

    elementID = browser_temp.find_element_by_xpath('//input[@type="file"]')
    elementID.send_keys(util.path_config +'sound/audio.mp3')

    browser_temp.find_element_by_xpath('//button[@id="convert-btn"]').click()
    time.sleep(5)

    wav_src = browser_temp.find_element_by_xpath('//div[@class="btn btn-success"]/a').get_attribute('href')
    response = requests.get(wav_src, stream=True, headers=USER_AGENT)
    with open(util.path_config +'sound/audio.wav', 'wb') as f:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
    time.sleep(1)

    # translate audio to text with google voice recognition
    r = sr.Recognizer()
    with sr.AudioFile(util.path_config +'sound/audio.wav') as source:
        audio = r.record(source)
    key = r.recognize_google(audio)
    print('reCaptcha passcode: %s' % key)

    browser_temp.quit()

    # key in results and submit
    browser.find_element_by_id('audio-response').send_keys(key.lower())
    browser.find_element_by_id('audio-response').send_keys(Keys.ENTER)
    browser.switch_to.default_content()
    time.sleep(1)
    browser.find_element_by_id('recaptcha-demo-submit').click()
    time.sleep(1)

    return 'reCAPTCHA Bot: DONE.'
