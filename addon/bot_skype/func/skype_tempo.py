from addon import *

from skpy import Skype, SkypeMsg



def login_skype(username, password):
    return Skype(username, password)


def convert_time(time):
    return time + timedelta(hours=7) #Convert to GMT+7


class bot_skype:
    def __init__(self):
        self.username = 'tech.qtdata@gmail.com'
        self.password = 'qtdata@2020'
        self.spreadsheet_skype_data_id = '1XMrOTkyY2TipDB0oJAsnP3PR4P9QRNWbJMYInMDKGZU'
        self.sk = login_skype(self.username, self.password)


    def send_group_message(self, group_id, message):
        channel = self.sk.chats[group_id]
        channel.sendMsg(message, rich=True)


    def get_group_message(self, group_id, num_day=1, sorted=False, update=False):
        skype = login_skype(self.username, self.password)
        channel = skype.chats[group_id]

        date_temp = datetime.today()
        date_previous = (datetime.today() - timedelta(days=num_day)).replace(hour=0, minute=0, second=0)

        list_message = []
        while date_temp >= date_previous:
            list_message += channel.getMsgs()
            date_temp = convert_time(list_message[-1].time)

        df_data = pd.DataFrame(columns=['USERID', 'DATETIME', 'NAME', 'CONTENT'])
        for idx, message in enumerate(list_message):
            message_time = convert_time(message.time)
            if (message_time >= date_previous) and (message_time < date_previous + timedelta(days=num_day)):
                df_data.loc[idx, 'USERID'] = message.userId
                df_data.loc[idx, 'DATETIME'] = convert_time(message.time).strftime('%Y-%m-%d %H:%M:%S')
                df_data.loc[idx, 'NAME'] = message.user.name
                df_data.loc[idx, 'CONTENT'] = message.content

        if sorted is True:
            df_data = df_data.sort_values('DATETIME')

        #Update data google sheet
        if update is True:
            spreadsheet = util.gc.open_by_key(self.spreadsheet_skype_data_id)
            sheetname = channel.topic.split(': ')[0] # Get sheetname
            try:
                spreadsheet.worksheet_by_title(sheetname)
            except:
                spreadsheet.add_worksheet(sheetname) # Create new sheet if not exist

            lib_sys.insert_dataframe_to_googlesheet(self.spreadsheet_skype_data_id, sheetname, df_data)

        return df_data


    def get_info(self, userid):
        return self.sk.contacts[userid].raw


    def convert_userid_to_name(self, list_userid):
        list_name = []

        for userid in list_userid:
            info = self.get_info(userid)
            try:
                list_name.append(info['displayname'])
            except:
                try:
                    list_name.append(info['display_name'])
                except:
                    list_name.append(info['firstname'])

        return list_name


    def get_listgroup(self, update=False):
        skype = login_skype(self.username, self.password)
        df_dict = {'GROUPID':[], 'TOPIC':[], 'MEMBER':[]}

        while True:
            for group_id, value in skype.chats.recent().items():
                if group_id[:2] == '19':
                    df_dict['GROUPID'].append(group_id)
                    df_dict['TOPIC'].append(value.topic)
                    member = self.convert_userid_to_name(value.userIds)
                    df_dict['MEMBER'].append(member)

            else: # No more chats returned
                break

        df_data = pd.DataFrame(df_dict)

        #Update data google sheet
        if update is True:
            lib_sys.insert_dataframe_to_googlesheet(self.spreadsheet_skype_data_id, 'List_group', df_data, start='A1')

        return df_data


    def update_skype_data(self, num_day=1):
        df_group = self.get_listgroup(update=True)
        for group_id in df_group['GROUPID']:
            self.get_group_message(group_id, num_day=num_day, sorted=True, update=True)





    # def get_skype_message():
    #     list_message = []
    #     for i in range(10):
    #         list_message += ch.getMsgs()
    #
    #     userId = 'thanhtrum'
    #     user_message = []
    #     for message in list_message:
    #         if message.userId == userId:
    #             user_message += [{'time': message.time,
    #                               'content': message.content,
    #                               'noquote_content': message.content.split('/quote>')[-1]}]
    #
    #     df = pd.DataFrame(user_message)
    #     df.to_excel('%s.xlsx' % ch.topic)
