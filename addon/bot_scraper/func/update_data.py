from addon import *
from selenium.webdriver.common.by import By
import os
from selenium import webdriver
import json
import time
import datetime
import pandas as pd
import random


program_dir = os.path.dirname(os.path.abspath(__file__))
 
folder_input_path=os.path.join(program_dir,"..\\..\\..\\","user_data\\")

folder_output_path=os.path.join(program_dir,"..\\..\\..\\","output\\")
json_name=folder_output_path+"update_info.json"

def write_json(new_data, filename=json_name):
    with open(filename,'r+') as file:
        # First we load existing data into a dict.
        file_data = json.load(file)
        # Join new_data with file_data inside emp_details
        file_data.append(new_data)
        # Sets file's current position at offset.
        file.seek(0)
        # convert back to json.
        json.dump(file_data, file, indent = 10)
def auto_update_data(username='',password='',list_file=[],start=None,num_row=1,min_delay=10):
    file_name="file_update.xlsx"
    file_path = os.path.join(folder_output_path+ file_name)
    data_excel=pd.read_excel(file_path)
    num_ro=data_excel.shape[0]
    start=num_ro

    all_files =list_file
    df_list=[]
    for  filename in all_files:
        print(filename)
        filename=folder_input_path + filename
        df =pd.read_excel(filename)
        df_list.append(df)
    merged_df = pd.concat(df_list, axis=0, ignore_index=True)
    print("merged")
    linkedin_index=int(merged_df.columns.get_loc('canonical_url'))
    data_list=merged_df.iloc[start:start+num_row,linkedin_index].values.tolist()

    with open(json_name, "w") as f:
        json.dump([], f)

    
    browser = init_browser(headless=True)

    url = 'https://www.linkedin.com/home'
    browser.get(url)
    browser.maximize_window()
    time.sleep(3)
    input_username=browser.find_element(By.ID,'session_key')
    input_username.send_keys (username)# enter username
    input_pass= browser.find_element(By.ID,'session_password')
    input_pass.send_keys(password)# enter password
    button= browser.find_element(By.XPATH,'//*[@id="main-content"]/section[1]/div/div/form[1]/div[2]/button').click()
    time.sleep(5)
    n=len(data_list)
    for i in range(n): 
        try: 
            browser.get(f'{data_list[i]}')
            val = random.randint(min_delay,min_delay + 10 )
            time.sleep(val)
            try:
                name= browser.find_element(By.TAG_NAME,'h1').text
            except:
                name=""
            try:
                job_type=browser.find_element(By.CLASS_NAME,'text-body-medium').text
            except:
                job_type=""
            try:
                location=browser.find_element(By.XPATH,"//span[contains(@class, 'text-body-small') and contains(@class, 'inline') and contains(@class, 't-black--light') and contains(@class, 'break-words')]").text
            except:
                location=""
            try:
                company=browser.find_element(By.XPATH,"//div[contains(@class, 'inline-show-more-text') and contains(@class, 'inline-show-more-text--is-collapsed') and contains(@class, 'inline-show-more-text--is-collapsed-with-line-clamp')]")
                company=company.get_attribute('textContent').replace('"', '').strip()
            except:
                company=""
            now =str(datetime.datetime.now())
            print(f"name: {name}")
            print('\n')
            
            write_json({
                "link":data_list[i],
                "fullname":name,
                "headline":job_type,
                "locality":location,
                "company":company,
                "dateupdate":now
            })
        except:
            continue

    with open("./output/update_info.json") as f:
        data= pd.read_json(f)
    new_row =pd.DataFrame(data)
    
    
    data_excel=data_excel.append(new_row,ignore_index=True)
    data_excel.to_excel(file_path,index=False)
    print(f"DONE, file path:{file_path}")

# if __name__ == '__main__': 
    # auto_update_data(username='',password='',list_file=[''],num_row=3,min_delay=10)      