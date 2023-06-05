from os import listdir
from os.path import isfile, join

from addon import *
from linkedin_api import Linkedin, settings



def read_data_message(username, path, service, num_run, ignore_error, daily_quota):
    df_message = pd.read_excel(path, 'MESSAGE')
    df_data = pd.read_excel(path, 'DATA')

    log.printt('Activating account: %s' % username)

    #Get latest data log
    log.printt('Input: %s' % path)
    df_limit, daily_used, len_limit = check_log_limit(username, service, num_run, daily_quota)

    #Get data not sent
    if ignore_error is False:
        df_notsent = df_data[pd.isnull(df_data['STATUS'])].head(len_limit)
    else:
        df_notsent = df_data[df_data['STATUS'] != 'sent'].head(len_limit)

    log.printt('Total data: %s' % len(df_notsent))

    return df_message, df_data, df_notsent, df_limit, daily_used


def export_data_message(path, df_message, df_data):
    filename = os.path.basename(path)
    path_output = util.path_output + filename.split('.xlsx')[0] + '__DONE.xlsx'
    with pd.ExcelWriter(path) as writer:
        df_message.to_excel(writer, sheet_name = 'MESSAGE', index = False)
        df_data.to_excel(writer, sheet_name = 'DATA', index = False)

    # os.remove(path)
    shutil.copy2(path, path_output)
    log.printt('Output: %s\n' % path_output)


class bot_linkedin:
    def authenticate(self, email, password):
        #Remove cookies
        for f in os.listdir(settings.COOKIE_PATH):
            os.remove(os.path.join(settings.COOKIE_PATH, f))

        self.api_service = Linkedin(email, password)
        self.username = email
        self.password = password


    def download_data_cron_from_drive(self, folder_id):
        list_excel = lib_sys.list_file_by_folderid(folder_id)
        list_cron_file = [i for i in list_excel if 'cron_linkedin_' in i['name']]

        for file in list_cron_file:
            try:
                spreadsheet = util.gc.open_by_key(file['id'])
                spreadsheet.export(file_format='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet:.xlsx',
                                   path=util.path_input,
                                   filename=file['name'])

            except Exception as e:
                log.error('%s __ %s' % (file, e))
                pass


    def upload_data_cron_to_drive(self, folder_id):
        list_file = [file for file in listdir(util.path_input) if isfile(join(util.path_input, file))]
        list_cron_file = [file for file in list_file if file.find('cron_linkedin_') == 0]

        for filename in list_cron_file:
            try:
                lib_tempo.push_file(filename, util.path_input + filename, folder_id)
            except Exception as e:
                log.error('%s __ %s' % (filename, e))
                pass

    def upload_file_to_drive(self, filename, from_path, folder_id):
        try:
            lib_tempo.push_file(filename, from_path + filename, folder_id)
        except Exception as e:
            log.error('%s __ %s' % (filename, e))
            pass


    def backup_data_cron(self, folder_id):
        #Get folder name
        folder = lib_sys.get_folder_by_folderid(folder_id)

        list_spreadsheet = lib_sys.list_spreadsheet_by_folderid(folder_id)
        list_cron_file = [i for i in list_spreadsheet if i['name'].find('cron_linkedin_') == 0]

        for file in list_cron_file:
            #Create new name
            current_date = datetime.today().strftime('%Y%m%d')
            filename_copy = '_'.join([current_date, file['name'], folder['name']])

            lib_sys.copy_file(file, folder_id, filename=filename_copy)

            #Remove data sent
            worksheet_data = util.gc.open_by_key(file['id']).worksheet_by_title('DATA')
            df_data = worksheet_data.get_as_df()
            df_data = df_data[df_data['STATUS'] != 'sent']

            lib_sys.insert_dataframe_to_googlesheet(file['id'], 'DATA', df_data, start='A1')


    def check_connection(self, filename, headless=True, status=None, min_delay=min_delay_default, num_export=50):
        lib_sys.init_log()
        path, filename = get_path_from_filename(filename)
        output_name = filename.split('.xlsx')[0]

        try:
            df_message = pd.read_excel(path, 'MESSAGE')
        except:
            df_message = pd.DataFrame()
        df_data = pd.read_excel(path, 'DATA')
        if 'CONNECT' not in df_data.columns:
            df_data['CONNECT'] = 0

        if status is not None:
            df_run = df_data[df_data['STATUS'] == status]

        log.printt('Total data: %s' % len(df_notsent))

        browser = init_browser(headless=headless)
        try:
            login_linkedin(browser, self.username, self.password)
        except:
            return

        log.printt('Linkedin Bot: START checking connection..\n')

        browser.get('https://www.linkedin.com/mynetwork/invite-connect/connections/')
        time.sleep(random.uniform(min_delay, min_delay + 3))

        for idx, row in df_run.iterrows():
            name = row['NAME']

            if not pd.isna(name):
                browser.find_element_by_xpath('//input[@placeholder="Search by name"]').click()

                actions = ActionChains(browser)
                actions.key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL)
                actions.send_keys(name)
                actions.perform()

                time.sleep(2)

                try:
                    browser.find_element_by_xpath('//li[@class="mn-connection-card artdeco-list"]')
                    df_data.loc[idx, 'CONNECT'] = 1
                except:
                    pass

            if idx != df_run.index[-1]:
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

        #Update results
        export_data_message(path, df_message, df_data)

        log.printt('Linkedin Bot: DONE.')

        return '\nLog file: %slatest.log' % (util.path_log)


    def get_conversation(self, export=False, unread=False):
        import warnings
        warnings.filterwarnings('ignore')

        api = self.api_service
        conversation_dict = api.get_conversations()
        df_conversation = pd.DataFrame(conversation_dict['elements'])

        df_temp = df_conversation[['entityUrn', 'read']]
        df_temp['entityUrn'] = [i.replace('urn:li:fs_conversation:', '') for i in df_temp['entityUrn']]

        if unread is True:
            df_temp = df_temp[df_temp['read'] == False]

        df_res = pd.DataFrame(columns =['createdAt', 'read', 'entityUrn', 'fromName', 'fromId', 'fromUrn', 'eventContent'])
        ii = 0
        for jj, urn in enumerate(df_temp['entityUrn']):
            chat_dict = api.get_conversation(urn)
            df_chat = pd.DataFrame(chat_dict['elements'])

            for idx, row in df_chat.iterrows():
                try:
                    df_res.loc[ii, 'createdAt'] = datetime.fromtimestamp(row['createdAt']/1000).strftime('%Y-%m-%d %H:%M:%S')
                    df_res.loc[ii, 'read'] = df_temp.loc[jj, 'read']
                    df_res.loc[ii, 'entityUrn'] = row['entityUrn'].split(',')[0].replace('urn:li:fs_event:(', '')
                    from_data = row['from']['com.linkedin.voyager.messaging.MessagingMember']
                    df_res.loc[ii, 'fromName'] = from_data['miniProfile']['firstName']
                    df_res.loc[ii, 'fromId'] = from_data['miniProfile']['publicIdentifier']
                    df_res.loc[ii, 'fromUrn'] = from_data['entityUrn'].split(',')[1].replace(')', '')
                    chat = row['eventContent']
                    df_res.loc[ii, 'eventContent'] = chat['com.linkedin.voyager.messaging.event.MessageEvent']['attributedBody']['text']
                    ii += 1

                except:
                    log.error(traceback.format_exc())
                    pass

        if export is True:
            path_output = util.path_output + 'Linkedin_conversation/'
            if not os.path.exists(path_output):
                os.makedirs(path_output)
                
            current_date = datetime.today().strftime('%Y%m%d')
            filename = '_'.join([current_date, 'Linkedin_conversation.xlsx'])
            df_res.to_excel(path_output + filename, index = False)

        return df_res, path_output, filename










#def init_paras_test():
#    daily_quota_default = 20
#    headless = False
#    num_run = daily_quota_default
#    daily_quota = daily_quota_default
#    ignore_error = False
#    min_delay = min_delay_default
#    func = 'send'
#    method = 2
#    num_export = 50
