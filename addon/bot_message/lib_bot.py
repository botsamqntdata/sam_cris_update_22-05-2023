from addon import *



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





