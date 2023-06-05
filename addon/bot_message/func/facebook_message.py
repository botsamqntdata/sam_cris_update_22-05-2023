from addon import *
from addon.bot_message.lib_bot import *


daily_quota_default = 20


def send_facebook(browser, url, subject, message, file, min_delay):
    browser.get(url)
    time.sleep(random.uniform(min_delay, min_delay + 3))

    #Customize message
    try:
        name = browser.find_element_by_xpath('//div[@class="bi6gxh9e aov4n071"]/span/h1').text
    except:
        name = ''
        pass

    message = message.replace('@name', name)

    try:
        list_elementID = browser.find_elements_by_xpath('//div[@aria-label="Add Friend" or @aria-label="Thêm bạn bè"]')
        for elementID in list_elementID:
            try:
                if elementID.is_displayed():
                    elementID.click()
                    time.sleep(2)
            except:
                pass
    except:
        pass

    browser.find_element_by_xpath('//div[@aria-label="Message" or @aria-label="Gửi tin nhắn"]').click()
    time.sleep(2)

    #Get focused text input
    element_text = browser.switch_to.active_element

    #Attach file
    elementID = browser.find_element_by_xpath(
        '//input[@accept="image/*,image/heif,image/heic,video/*" and \
        @class="mkhogb32" and @multiple="" and @type="file"]'
    )
    for f in file:
        elementID.send_keys(util.path_media + f)
        time.sleep(2)

    element_text.click()
    actions = ActionChains(browser)
    for part in message.split('\n'):
        actions.send_keys(part)
        actions.key_down(Keys.SHIFT).send_keys(Keys.ENTER).key_up(Keys.SHIFT)
        time.sleep(2)

    actions.perform()
    time.sleep(2)

    ActionChains(browser).send_keys(Keys.ESCAPE).perform()

    return name


def start_bot_facebook(browser, output_name, run_succeed, df_message, df_data, df_notsent, min_delay, num_export):
    df_subject = df_message['SUBJECT']
    df_content = df_message['CONTENT']
    len_message = len(df_message)
    ii = 0
    first_result = True

    try:
        df_file = df_message['FILE']
    except:
        df_file = pd.DataFrame()

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
            url = row['FACEBOOK']
            status = row['STATUS']

            if status != 'sent':
                name = send_facebook(browser, url, subject, message, file, min_delay)
                df_data.loc[idx, 'NAME'] = name
                df_data.loc[idx, 'STATUS'] = 'sent'
                run_succeed += 1

            #Sleep to make sure everything loads
            time.sleep(random.uniform(min_delay + 3, min_delay + 7))

        except Exception as e:
            df_data.loc[idx, 'STATUS'] = e
            log.error(f'[{idx}] {url} __ {e}')
            pass

        if first_result is True:
            log.printt('[%s] %s: sent __ %s' % (idx, row['FACEBOOK'], time.time() - time_start))
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


def run_facebook_message(username, password, filename=None, headless=True, num_run=daily_quota_default,
        daily_quota=daily_quota_default, ignore_error=False, min_delay=min_delay_default, num_export=50):
    service = 'run_facebook_message'
    run_succeed = 0

    lib_sys.init_log()
    path, filename = get_path_from_filename(filename)
    output_name = filename.split('.xlsx')[0]

    df_message, df_data, df_notsent, \
        df_limit, daily_sent = read_data_message(username, path, service, num_run, ignore_error, daily_quota)

    browser = init_browser(headless=headless)
    try:
        login_facebook(browser, username, password)
    except:
        return

    log.printt('Facebook Bot: START sending..\n')
    run_succeed, df_data = start_bot_facebook(browser, output_name, run_succeed, df_message, df_data,
                               df_notsent, min_delay, num_export)

    #Switch content
    df_message = df_message.apply(np.roll, shift = 1)

    #Update data log
    update_log_limit(df_limit, username, run_succeed, daily_sent)

    #Update results
    export_data_message(filename, df_message, df_data)

    log.printt('Facebook Bot: DONE.')




