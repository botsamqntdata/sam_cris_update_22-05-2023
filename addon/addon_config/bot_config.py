from addon import *



def login_linkedin(browser, username, password):
    url = 'https://www.linkedin.com/uas/login'

    browser.get(url)
    time.sleep(5)

    try:
        elementID = browser.find_element_by_id('username')
        elementID.send_keys(username)

        elementID = browser.find_element_by_id('password')
        elementID.send_keys(password)

        elementID.submit()

    except:
        browser.quit()
        log.printt('Login to Linkedin: FAILED!')
        raise

    time.sleep(min_delay_default)

    #Minimizing Message Popup
    try:
        elementID = browser.find_element_by_xpath(
            '//section[@class="msg-overlay-bubble-header__controls display-flex"]')
        chevron_icon = elementID.find_elements_by_css_selector('li-icon')[-1].get_attribute('type')
        if chevron_icon == 'chevron-down-icon':
            elementID.find_elements_by_css_selector('button')[-1].click()

    except:
        pass

    log.printt('Login to Linkedin: OK.')


def login_facebook(browser, username, password):
    url = 'https://www.facebook.com/login'

    browser.get(url)
    time.sleep(5)

    try:
        elementID = browser.find_element_by_id('email')
        elementID.send_keys(username)

        elementID = browser.find_element_by_id('pass')
        elementID.send_keys(password)

        elementID.submit()

    except:
        browser.quit()
        return 'Login failed!'

    time.sleep(min_delay_default)


def get_path_from_filename(filename):
    if filename is None:
        path = lib_sys.get_filepath('xlsx')
        filename = os.path.basename(path)

        if len(path) == 0:
            return 'No file selected.'
    else:
        path = util.path_input + filename

    return path, filename


def import_file(filename):
    path, filename = get_path_from_filename(filename)
    data = pd.read_excel(path)
    output_name = filename.split('.xlsx')[0]

    log.printt('Input: %s' % path)
    log.printt('Total data: %s' % len(data))

    return data, output_name


def export_file(data, path):
    with pd.ExcelWriter(path) as writer:
        data.to_excel(writer, index = False)

    log.printt('Output: %s\n' % path)


def check_log_limit(username, service, num_run, daily_quota):
    limit_logdir = './addon/addon_config/limit_log.csv'
    log.printt('Usage quotas log: %s' % limit_logdir)

    df_limit = pd.read_csv(limit_logdir)
    df_log = df_limit[df_limit['SERVICE'] == service]

    try:
        df_templog = df_log[df_log['USERNAME'] == username].iloc[0]
        daily_used = df_templog['DAILY_USED']

        if daily_quota > 0:
            df_limit.loc[df_limit['USERNAME'] == username, 'DAILY_QUOTA'] = daily_quota
        else:
            daily_quota = df_templog['DAILY_QUOTA']

        last_modified_day = df_templog['DATE_MODIFIED']
        last_modified_day = datetime.strptime(last_modified_day, '%Y-%m-%d').date()
    except:
        if username not in df_log['USERNAME'].values:
            df_limit = df_limit.append(
                pd.DataFrame([{
                    'SERVICE': service,
                    'USERNAME': username,
                    'DATE_MODIFIED': datetime.today().date(),
                    'DAILY_USED': 0,
                    'DAILY_QUOTA': daily_quota,
                }]),
                ignore_index = True, sort = False
            )
        daily_used = 0
        last_modified_day = datetime.today().date()

    #Check limit message and connection per day
    if datetime.today().date() - last_modified_day >= timedelta(days = 1):
        daily_used = 0
    log.printt('Daily used: %s __ Daily quota: %s' % (daily_used, daily_quota))

    len_limit = daily_quota - daily_used
    if num_run != 0:
        len_limit = min(len_limit, num_run)

    if len_limit <= 0:
        log.printt('Account `%s` has reached the quota limit!' % username)

    return df_limit, daily_used, len_limit


def update_log_limit(df_limit, username, run_succeed, daily_used):
    try:
        df_limit.loc[df_limit['USERNAME'] == username, 'DAILY_USED'] = run_succeed + daily_used
        df_limit.loc[df_limit['USERNAME'] == username, 'DATE_MODIFIED'] = datetime.today().date()
        df_limit.drop_duplicates(inplace = True, ignore_index = True)
        df_limit.to_csv('./addon/addon_config/limit_log.csv', index = False)

        log.printt('Update limit_log. Daily used: %s' % (run_succeed + daily_used))

    except:
        log.printt('Update limit_log failed! Daily used: %s' % (run_succeed + daily_used))
        pass
#
#
#def read_data_message(username, path, service, num_run, ignore_error, daily_quota):
#    df_message = pd.read_excel(path, 'MESSAGE')
#    df_data = pd.read_excel(path, 'DATA')
#
#    log.printt('Activating account: %s' % username)
#
#    #Get latest data log
#    log.printt('Input: %s' % path)
#    df_limit, daily_usage, len_limit = check_log_limit(username, service, num_run, daily_quota)
#
#    #Get data not sent
#    if ignore_error is False:
#        df_notsent = df_data[pd.isnull(df_data['STATUS'])].head(len_limit)
#    else:
#        df_notsent = df_data[df_data['STATUS'] != 'sent'].head(len_limit)
#
#    log.printt('Total data: %s' % len(df_notsent))
#
#    return df_message, df_data, df_notsent, df_limit, daily_usage
#
#
#def export_data_message(path, df_message, df_data):
#    path_user = path.split('.xlsx')[0] + '__DONE.xlsx'
#    with pd.ExcelWriter(path_user) as writer:
#        df_message.to_excel(writer, sheet_name = 'MESSAGE', index = False)
#        df_data.to_excel(writer, sheet_name = 'DATA', index = False)
#
#    os.remove(path)
#    log.printt('Output: %s\n' % path_user)




