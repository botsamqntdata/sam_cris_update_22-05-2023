from addon import *
from addon.bot_message.lib_bot import *



daily_quota_default = 100


def connect_linkedin(browser, url, email, subject, message, file, min_delay):
    browser.get(url)
    time.sleep(random.uniform(min_delay, min_delay + 3))

    #Customize message
    try:
        panel_left = browser.find_element_by_xpath('//div[contains(@class, "pv-text-details__left-panel")]').text
        name = panel_left.split('\n')[0]
        for i in [' (He/Him)', ' (She/Her)']:
            name = name.replace(i, '')

    except:
        name = ''
        pass

    subject = subject.replace('@subject', name)
    message = message.replace('@name', name)

    #Connect stay in More
    element_list = browser.find_elements_by_xpath('//button[contains(@aria-label, "More actions")]')
    for elementID in element_list:
        try:
            elementID.click()
            break
        except:
            pass

    #Clicks Connect button
    element_list = browser.find_elements_by_xpath('//*[text()="Connect"]')
    for elementID in element_list:
        try:
            elementID.click()
            break
        except:
            pass

    try:
        browser.find_element_by_xpath('//button[contains(@aria-label, "Connect")]').click()
    except:
        pass

    time.sleep(2)

    try:
        browser.find_element_by_xpath('//button[contains(@aria-label, "Add a note")]').click()
    except:
        pass

    actions = ActionChains(browser)
    for part in message.split('\n'):
        actions.send_keys(part)
        actions.key_down(Keys.SHIFT).send_keys(Keys.ENTER).key_up(Keys.SHIFT)
        time.sleep(2)

    actions.perform()
    time.sleep(2)

    # Add email to send
    try:
        browser.find_element_by_name('email').send_keys(email)
    except:
        pass

    send_button = browser.find_element_by_class_name('ml1')

    clickable = False
    time_wait = time.time()
    while not clickable and time.time() < time_wait + implicit_time_default:
        try:
            cursor = send_button.value_of_css_property('cursor')
            if cursor != 'not-allowed':
                clickable = True
            break
        except:
            continue

    if clickable:
        send_button.click()

    time.sleep(2)
    ActionChains(browser).send_keys(Keys.ESCAPE).perform()

    return name


def connect_linkedin_via_email(browser, email_list, min_delay):
    browser.get('https://www.linkedin.com/mynetwork/import-contacts/iwe/')
    time.sleep(random.uniform(min_delay, min_delay + 3))
    browser.find_element_by_xpath('//textarea[contains(@name, "message")]').click()

    actions = ActionChains(browser)
    actions.send_keys(email_list)
    actions.perform()
    time.sleep(2)

    browser.find_element_by_xpath('//button[contains(@id, "send-iwe")]').click()


def send_linkedin(browser, url, email, subject, message, file, min_delay):
    browser.get(url)
    time.sleep(random.uniform(min_delay, min_delay + 3))

    #Check if connected
    try:
        browser.find_element_by_xpath('//*[text()="Remove Connection"]')
    except:
        raise Exception('Contact is not connected.')

    #Customize message
    try:
        panel_left = browser.find_element_by_xpath('//div[contains(@class, "pv-text-details__left-panel")]').text
        name = panel_left.split('\n')[0]
    except:
        name = ''
        pass

    subject = subject.replace('@subject', name)
    message = message.replace('@name', name)

    elementID = browser.find_element_by_class_name('message-anywhere-button')
    if len(elementID.get_attribute('class').split()) > 1 \
        and elementID.get_property('href') != 'https://www.linkedin.com/premium/my-premium/':
        browser.get(elementID.get_property('href'))
        time.sleep(2)

        #Attach images
        try:
            elementID = browser.find_element_by_xpath(
                '//input[@accept="image/*,.ai,.psd,.pdf,.doc,.docx,.csv,.zip,.rar,.ppt,.pptx,.pps,.ppsx,'+
                '.odt,.rtf,.xls,.xlsx,.txt,.pub,.html,.7z,.eml"]'
            )
            for f in file:
                elementID.send_keys(util.path_media + f)
                time.sleep(2)
        except:
            pass

        try:
            browser.find_element_by_xpath('//input[@name="subject"]').send_keys(subject)
        except:
            pass

        browser.find_element_by_xpath('//div[@role="textbox" and @aria-multiline="true"]').click()

        actions = ActionChains(browser)
        for part in message.split('\n'):
            actions.send_keys(part)
            actions.key_down(Keys.SHIFT).send_keys(Keys.ENTER).key_up(Keys.SHIFT)
            time.sleep(2)

        actions.perform()
        time.sleep(2)

        send_button = browser.find_element_by_class_name('msg-form__send-button')

        clickable = False
        time_wait = time.time()
        while not clickable and time.time() < time_wait + implicit_time_default:
            try:
                cursor = send_button.value_of_css_property('cursor')
                if cursor != 'not-allowed':
                    clickable = True
                break
            except:
                continue

        if clickable:
            send_button.click()

    #If Follow is required
#        browser.find_element_by_class_name('pv-s-profile-actions--follow').click()

    # Connect
    # checkSentButton = browser.find_element_by_class_name('ml1')
    # if 'artdeco-button--disabled' in checkSentButton.get_attribute('class').split():
    #     browser.find_element_by_class_name('artdeco-modal__dismiss').click()
    #     browser.find_element_by_class_name('pv-s-profile-actions--message').click()
    #     if True == check_exists_class('msg-form__subject'):
    #         browser.find_element_by_class_name('msg-form__subject').send_keys(subject)
    #     if True == check_exists_class('msg-form__contenteditable'):
    #         browser.find_element_by_class_name('msg-form__contenteditable').send_keys(message)
    #     if True == check_exists_class('msg-form__send-button'):
    #         browser.find_element_by_class_name('msg-form__send-button').click()
    # else:
    #     checkSentButton.click()

    time.sleep(2)
    ActionChains(browser).send_keys(Keys.ESCAPE).perform()

    return name


def disconnect_linkedin(browser, url, min_delay):
    browser.get(url)
    time.sleep(random.uniform(min_delay, min_delay + 3))

    browser.find_element_by_class_name('pv-s-profile-actions__overflow-toggle').click()
    time.sleep(2)

    browser.find_element_by_class_name('pv-s-profile-actions--disconnect').click()
    time.sleep(2)


def start_bot_linkedin(browser, output_name, run_succeed, df_message, df_data, df_notsent, func, min_delay, num_export):
    df_subject = df_message['SUBJECT']
    df_content = df_message['CONTENT']
    len_message = len(df_message)
    ii = 0
    first_result = True

    try:
        df_file = df_message['FILE']
    except:
        df_file = pd.DataFrame()

    if func == 'connect_via_email':
        try:
            email_list = ', '.join(df_notsent['EMAIL'])
            connect_linkedin_via_email(browser, email_list, min_delay)
            df_data.loc[df_notsent.index, 'STATUS'] = 'email_sent'
            df_data.loc[df_notsent.index, 'NAME_MODIFIED'] = util.username
            df_data.loc[df_notsent.index, 'DATE_MODIFIED'] = datetime.now()

        except Exception as e:
            df_data.loc[0, 'STATUS'] = e
            log.error(f'Connect Linkedin via email __ {e}')
            pass

    else:
        for idx, row in df_notsent.iterrows():
            time_start = time.time()
            df_data.loc[idx, 'NAME_MODIFIED'] = util.username
            df_data.loc[idx, 'DATE_MODIFIED'] = datetime.now()

            subject = df_subject[ii]
            message = df_content[ii]
            try:
                file = df_file[ii].split(', ')
            except:
                file = []
                pass

            ii += 1
            if ii == len_message: #reset to first content
                ii = 0

            try:
                url = row['LINKEDIN']
                email = row['EMAIL']
                status = row['STATUS']

                if status != 'sent' and func == 'connect':
                    name = connect_linkedin(browser, url, email, subject, message, file, min_delay)
                    df_data.loc[idx, 'NAME'] = name
                    df_data.loc[idx, 'STATUS'] = 'sent'

                if status != 'sent' and func == 'send':
                    name = send_linkedin(browser, url, email, subject, message, file, min_delay)
                    df_data.loc[idx, 'NAME'] = name
                    df_data.loc[idx, 'STATUS'] = 'sent'

                if status != 'disconnected' and func == 'disconnect':
                    disconnect_linkedin(browser, url, min_delay)
                    df_data.loc[idx, 'STATUS'] = 'disconnected'

                run_succeed += 1

                #Sleep to make sure everything loads
                time.sleep(random.uniform(min_delay + 3, min_delay + 7))

            except Exception as e:
                df_data.loc[idx, 'STATUS'] = e
                log.error(f'[{idx}] {url} __ {e}')
                pass

            if first_result is True:
                log.printt('[%s] %s: %s __ %s' % (idx, row['LINKEDIN'], func, time.time() - time_start))
                first_result = False

            if idx != df_notsent.index[-1]:
                if (idx + 1) % num_export == 0:
                    [os.remove(os.path.join(util.path_output, f)) for f in os.listdir(util.path_output)
                        if f.find(output_name) != -1]
                    path_user = util.path_output + output_name + '__temp_%s.xlsx' % (idx + 1)
                    export_file(df_data, path_user)

            else:
                # remove all temp output
                log.printt('Remove all temporary outputs.')
                [os.remove(os.path.join(util.path_output, f)) for f in os.listdir(util.path_output)
                    if f.find(output_name) != -1]

    browser.quit()

    return run_succeed, df_data


def run_linkedin_message(username, password, filename=None, headless=True, num_run=daily_quota_default,
        daily_quota=daily_quota_default, ignore_error=False, min_delay=min_delay_default, func='connect_via_email', num_export=50):
    service = 'run_linkedin_message'
    run_succeed = 0

    lib_sys.init_log()
    path, filename = get_path_from_filename(filename)
    output_name = filename.split('.xlsx')[0]

    df_message, df_data, df_notsent, \
        df_limit, daily_sent = read_data_message(username, path, service, num_run, ignore_error, daily_quota)

    browser = init_browser(headless=headless)
    try:
        login_linkedin(browser, username, password)
    except:
        return

    if func == 'send':
        log.printt('Linkedin Bot: START sending..\n')
    elif func == 'disconnect':
        log.printt('Linkedin Bot: START disconnecting..\n')
    else:
        log.printt('Linkedin Bot: START connecting..\n')

    run_succeed, df_data = start_bot_linkedin(browser, output_name, run_succeed, df_message, df_data,
                               df_notsent, func, min_delay, num_export)

    #Switch content
    df_message = df_message.apply(np.roll, shift = 1)

    #Update data log
    update_log_limit(df_limit, username, run_succeed, daily_sent)

    #Update results
    export_data_message(path, df_message, df_data)

    log.printt('Linkedin Bot: DONE.')

    return '\nLog file: %slatest.log' % (util.path_log)
