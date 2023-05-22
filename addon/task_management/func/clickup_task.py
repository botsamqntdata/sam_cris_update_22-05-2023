from addon import *

from clickup_api import client



class bot_task:
    def __init__(self):
        self.api_key = util.clickup_api
        self.team_id = '25655819'
        self.monthly_space_id = '43781461'
        self.weekly_space_id = '43781605'
        self.daily_space_id = '43782982'
        self.bot_task = client.ClickUpClient(self.api_key)


    def run_task_management(self, username, password):
        lib_sys.init_log()

        try:
            browser = init_browser()
            browser.get('https://app.clickup.com/login')
            time.sleep(5)
            browser.find_element_by_id('login-email-input').send_keys(username)
            browser.find_element_by_id('login-password-input').send_keys(password)
            browser.find_element_by_xpath('//button[contains(@data-test, "login-submit")]').click()

        except:
            browser.quit()
            log.printt('Login to ClickUp: FAILED!')
            message_error = traceback.format_exc()
            log.error(message_error)

            return message_error


    def list_space(self, team_id=None):
        if team_id is None:
            team_id = self.team_id
        list_space = self.bot_task.get_spaces(team_id)
        list_space_name = []
        for space in list_space:
            list_space_name.append(space.name)

        return list_space_name


    def list_project(self, freq='weekly'):
        if freq == 'monthly':
            space_id = self.monthly_space_id
        if freq == 'weekly':
            space_id = self.weekly_space_id
        if freq == 'daily':
            space_id = self.daily_space_id

        server_project = self.bot_task.get_folderless_lists(space_id).dict()['lists']
        list_project = []
        for list in server_project:
            list_project.append({'id': list['id'], 'name': list['name']})

        return list_project


    def list_task(self, project_id):
        server_task = self.bot_task.get_tasks(project_id, subtasks=True).dict()['tasks']
        list_task = []
        for task in server_task:
            list_task.append({'id': task['id'], 'name': task['name'], 'url': task['url']})

        return list_task


    def list_all_task(self):
        all_task = {'monthly': '', 'weekly': '', 'daily': ''}

        for freq in ['monthly', 'weekly', 'daily']:
            temp_project = self.list_project(freq)
            temp_task = []
            for project in temp_project:
                temp_task.append(self.list_task(project['id']))
            all_task[freq] = temp_task

        return all_task


    def run_list_task(self, freq='weekly'):
        temp_project = self.list_project(freq)
        temp_task = []
        df = pd.DataFrame()

        for project in temp_project:
            df_temp = pd.DataFrame()
            temp_task = self.list_task(project['id'])

            for i in temp_task:
                df_temp = pd.concat([df_temp, pd.DataFrame([i])])
            df_temp['project'] = project['name']
            df = pd.concat([df, df_temp])

        return df.reset_index(drop=True)


    def run_list_everything():
        for freq in ['monthly', 'weekly', 'daily']:
            print('\n %s' % freq)
            print(self.run_list_task(freq))


    def get_comment(self, task_id):
        comments = self.bot_task.get_task_comments(task_id).dict()['comments']
        comment_list = []
        for i in comments:
            comment_list.append(i['comment_text'])
        return comment_list


    def get_data_from_task(self, task, subtasks=None):
        task_df = {}
        task_df['id'] = task['id']
        task_df['name'] = task['name']
        task_df['date'] = datetime.now().strftime('%Y-%m-%d')
        task_df['description'] = task['description']
        if subtasks is not None:
            task_df['task'] = '- ' + '\n- '.join(['%s_%s' % (i['id'], i['name']) for i in subtasks])
        task_df['team_comment'] = ''
        task_df['outcome'] = self.get_comment(task['id'])
        return task_df


    def create_proof_data(self, task_id='2ccy8b3'):
        task = self.bot_task.get_task(task_id, subtasks=True).dict()
        subtasks = []
        for i in task['subtasks']:
            subtask_description = self.bot_task.get_task(i['id']).dict()['description']
            subtasks.append({'id': i['id'], 'name': i['name'], 'description': subtask_description, 'url': i['url']})

        task_df = self.get_data_from_task(task, subtasks=subtasks)
        subtask_df = []
        for i in subtasks:
            subtask_df.append(self.get_data_from_task(i))

        task_df = pd.DataFrame(task_df).T
        subtask_df = pd.DataFrame(subtask_df).T

        return task_df, subtask_df


# def export_proof_data(task_df, subtask_df=None)
#     # create_spreadsheet(util.drive_service, '1jQcvvPndeRLTELJE6z6WT0NCKRdpLXDL', '%s_%s' % (task['id'], task['name']))
#     sh = util.gc.open_by_key('1nfLyO2tKN6RSukIcbOQdiH2JfDjwF7qiwAp_sVH94p4')
#
#     task_df = task_df.reset_index()
#     try:
#         worksheet = sh.worksheet_by_title('Summary')
#     except:
#         sh.add_worksheet('Summary')
#     lib_sys.insert_dataframe_to_googlesheet(spreadsheet_id='1nfLyO2tKN6RSukIcbOQdiH2JfDjwF7qiwAp_sVH94p4',
#         sheetname='Summary', data=task_df, start='A1', copy_head=False)
#
#     if subtask_df is not None:
# for col in subtask_df.columns:
#     temp_df = subtask_df[col].reset_index()
#     temp_sheetname = temp_df.loc[temp_df['index']=='name', col].values[0]
#     try:
#         worksheet = sh.worksheet_by_title(temp_sheetname)
#     except:
#         sh.add_worksheet(temp_sheetname)
#     lib_sys.insert_dataframe_to_googlesheet(spreadsheet_id='1nfLyO2tKN6RSukIcbOQdiH2JfDjwF7qiwAp_sVH94p4',
#         sheetname=temp_sheetname, data=temp_df, start_row='A1', copy_head=False)


# import requests
#
# headers = {
#   'Authorization': api_key,
#   'Content-Type': 'application/json'
# }
# response = requests.get('https://api.clickup.com/api/v2/task/2ccy473', headers=headers)
# response_json = response.json()
# print(response_json)
#




