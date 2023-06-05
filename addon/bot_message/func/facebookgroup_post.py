from addon import *
from addon.bot_message.lib_bot import *


daily_quota_default = 10


def post_facebookgroup(browser, url, subject, message, file, min_delay):
    browser.get(url)
    time.sleep(random.uniform(min_delay + 3, min_delay + 7))

    #Customize message
    try:
        name = browser.find_element_by_xpath('//div[@class="bi6gxh9e aov4n071"]/h1').text
    except:
        name = ''
        pass

    subject = subject.replace('@subject', name)
    message = message.replace('@name', name)

    try: #Sell group
        browser.find_element_by_xpath(
            '//div[(@aria-label="Sell Something" or @aria-label="Bán gì đó") and @role="button"]'
        ).click()
        time.sleep(2)

        #Click Item for Sale
        browser.find_element_by_xpath(
            '//span[text()="Item for Sale" or text()="Mặt hàng cần bán"]'
        ).click()
        time.sleep(2)

        #Attach file
        elementID = browser.find_element_by_xpath(
            '//input[@accept="image/*,image/heif,image/heic" and \
            @class="mkhogb32" and @multiple="" and @type="file"]'
        )
        elementID.send_keys(util.path_media + file[0])
        time.sleep(random.uniform(min_delay, min_delay + 3))

        browser.find_element_by_xpath('//div[@class="j83agx80 k4urcfbm"]/div/input').send_keys(subject)

        browser.find_element_by_xpath('//label[@aria-label="Price"]/div/div/input').send_keys('0')
        time.sleep(2)

        browser.find_element_by_xpath('//label[@aria-label="Description"]').click()

        actions = ActionChains(browser)
        for part in message.split('\n'):
            actions.send_keys(part)
            actions.key_down(Keys.SHIFT).send_keys(Keys.ENTER).key_up(Keys.SHIFT)
            time.sleep(1)

        actions.perform()
        time.sleep(2)

        next_button = browser.find_element_by_xpath('//div[(@aria-label="Next" or @aria-label="Tiếp") and @role="button"]')

        clickable = False
        while not clickable:
            cursor = next_button.value_of_css_property('cursor')
            if cursor != 'not-allowed':
                clickable = True
            break

        next_button.click()
        time.sleep(2)

        #Uncheck Marketplace
        try:
            browser.find_element_by_class_name('hu5pjgll.op6gxeva.sp_v8yz2528JQj.sx_3bb65f').click()
        except:
            pass
        time.sleep(2)

    except: #Discuss group
#        elementID = browser.find_element_by_xpath('//span[text() = "Discussion" or text() = "Thảo luận"]').click()
#        time.sleep(2)

        #Attach file
        elementID = browser.find_element_by_xpath(
            '//input[@accept="image/*,image/heif,image/heic,video/*,video/mp4,video/x-m4v,video/x-matroska,.mkv" and \
            @class="mkhogb32" and @multiple="" and @type="file"]'
        )

        elementID.send_keys(util.path_media + file[0])
        time.sleep(random.uniform(min_delay, min_delay + 3))

        browser.find_element_by_xpath('//div[@aria-label="Create a public post…"]').click()

        actions = ActionChains(browser)
        for part in message.split('\n'):
            actions.send_keys(part)
            actions.key_down(Keys.SHIFT).send_keys(Keys.ENTER).key_up(Keys.SHIFT)
            time.sleep(1)

        actions.perform()
        time.sleep(2)

    post_button = browser.find_element_by_xpath('//div[(@aria-label="Post" or @aria-label="Đăng") and @role="button"]')

    clickable = False
    while not clickable:
        cursor = post_button.value_of_css_property('cursor')
        if cursor != 'not-allowed':
            clickable = True
        break

    post_button.click()
    time.sleep(2)

    return name


def start_bot_facebookgroup(browser, output_name, run_succeed, df_message, df_data, df_notsent, min_delay, num_export):
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
            url = row['FACEBOOK_GROUP']
            status = row['STATUS']

            if status != 'sent':
                name = post_facebookgroup(browser, url, subject, message, file, min_delay)
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
            log.printt('[%s] %s: sent __ %s' % (idx, row['FACEBOOK_GROUP'], time.time() - time_start))
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


def run_facebookgroup_post(username, password, filename=None, headless=True, num_run=daily_quota_default,
        daily_quota=daily_quota_default, ignore_error=False, min_delay=min_delay_default, num_export=50):
    service = 'run_facebookgroup_post'
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

    log.printt('FacebookGroup Bot: START sending..\n')
    run_succeed, df_data = start_bot_facebookgroup(browser, output_name, run_succeed, df_message, df_data,
                           df_notsent, min_delay, num_export)

    #Switch content
    df_message = df_message.apply(np.roll, shift = 1)

    #Update data log
    update_log_limit(df_limit, username, run_succeed, daily_sent)

    #Update results
    export_data_message(filename, df_message, df_data)

    log.printt('FacebookGroup Bot: DONE.')




