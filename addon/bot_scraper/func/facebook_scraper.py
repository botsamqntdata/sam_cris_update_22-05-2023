from addon import *



class SearchGroup:
    def __init__(self, browser, search_link = 'https://www.facebook.com/search/groups/?q='):
        self.browser = browser
        self.FACEBOOK_SEARCH = search_link
        

    def insert_search(self, search_string):
        return self.FACEBOOK_SEARCH + search_string 
    
    
    def choose_public_group(self, browser):
        button = browser.find_element_by_xpath('//input[@aria-label="Public Groups" and @role="switch"]')
        if button.get_attribute('aria-checked') == 'false':
            button.click()
            
        time.sleep(5)
        return
    
    
    def get_group(self, browser, count=0):
        list_group = browser.find_elements_by_xpath('//div[@role="feed"]/div/div')[count:]
        group_id_list = []
        for group in list_group[:-1]:
            try:
                group_link = group.find_elements_by_css_selector('a')[0].get_attribute('href')
#                group_id = re.search('%s(.*)%s' % ('groups/', '/'), group_link).group(1)
                group_id_list.append(group_link)
            except:
                pass
    
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(10)
        
        return group_id_list
    
    
    def get_groupid(self, browser, min_group=20):
        total_id = []
        count = 0
        pageHeight = browser.execute_script("return document.body.scrollHeight")
        totalScrolledHeight = browser.execute_script("return window.pageYOffset + window.innerHeight")
        
        while count < min_group and (totalScrolledHeight + 15 < pageHeight or len(total_id) == 0):
            group_id_list = self.get_group(browser, count = count)
            count +=  len(group_id_list)
            total_id += group_id_list
            pageHeight = browser.execute_script("return document.body.scrollHeight")
            totalScrolledHeight = browser.execute_script("return window.pageYOffset + window.innerHeight")
            
        df_group = pd.DataFrame(total_id, columns = ['FACEBOOK_GROUP'])
            
        return df_group

    
    def search_group(self, search_string, location='None', choose_public_group=True, min_group=20):
        browser = self.browser
        search_string = urllib.parse.quote_plus(search_string)
        search_url = self.insert_search(search_string)
        
        browser.get(search_url)
        time.sleep(5)
        
        #Choose public group
        if choose_public_group is True:
            self.choose_public_group(browser)
        
        #Add location
        if location != 'None':
            elementID = browser.find_elements_by_xpath('//div[@class="rq0escxv j83agx80 cbu4d94t k4urcfbm"]/div/div/div/div')
            elementID[0].click()
            
            actions = ActionChains(browser)
            actions.send_keys(location)
            actions.perform()
            
            time.sleep(5)
            #Click first option
            browser.find_elements_by_xpath('//ul[@class="buofh1pr cbu4d94t j83agx80"]/li')[0].click()
        
        df_group = self.get_groupid(browser, min_group)
        
        return df_group
    
    
class GetMemberID:
    def __init__(self, browser, base_link='https://www.facebook.com'):
        self.browser = browser
        self.BASE_URL = base_link
        
        
    def get_placelived(self, browser, total_id):
        total_placelived = []
        for member_id in total_id:
            member_placelived = []
            try:
                if 'profile.php' in member_id:
                    browser.get(f"{member_id}&sk=about_places")
                else:
                    browser.get(f"{member_id}/about_places")
                
                list_place =  browser.find_elements_by_xpath('//div[@class="ii04i59q a3bd9o3v jq4qci2q oo9gr5id tvmbv18p"]/a')
                for place in list_place:
                    member_placelived.append(place.text)
            except:
                pass
            
            total_placelived.append(member_placelived)
            time.sleep(10)
            
        return total_placelived
        
        
    def get_member(self, browser, count=0):
        list_member = browser.find_elements_by_xpath('//div[@class="b20td4e0 muag1w35"]/div')[count:]
#        BASE_URL = self.BASE_URL
        member_id_list = []
        
        for member in list_member:
            member_id = member.find_elements_by_css_selector('a')[0].get_attribute('href')
#            if 'profile.php' in member_id:
#                member_id = re.findall(r'%s(\d+)' % 'id=', member_id)[0]
#            else:
#                member_id = member_id.partition("?")[0]
#                member_id = member_id[member_id.index(f"{BASE_URL}/") + len(f"{BASE_URL}/"):]

            member_id_list.append(member_id)
            
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(10)
        
        return member_id_list
    
    
    def get_memberid(self, group_id, min_member=200):
        browser = self.browser
        BASE_URL = self.BASE_URL
        
        browser.get(f"{BASE_URL}/groups/{group_id}/members")
        #Get number of members in group
        try:
            group_grid = browser.find_elements_by_xpath(
                '//span[@class="d2edcug0 hpfvmrgz qv66sw1b c1et5uql oi732d6d ik7dh3pa '
                + 'fgxwclzu jq4qci2q a3bd9o3v knj5qynh m9osqain"]'
            )
            group_member_number = group_grid[0].find_elements_by_css_selector('strong')[0].text
            group_member_number = int(group_member_number.split('· ')[-1].replace(',', ''))
            min_member = min(min_member, group_member_number)
        except:
            pass

        total_id = []
        count = 12
        min_member += count #Ignore admin, page, things in common
        pageHeight = browser.execute_script("return document.body.scrollHeight")
        totalScrolledHeight = browser.execute_script("return window.pageYOffset + window.innerHeight")

        while count < min_member and (totalScrolledHeight + 15 < pageHeight or len(total_id) == 0):
            member_id_list = self.get_member(browser, count = count)
            count +=  len(member_id_list)
            total_id += member_id_list
            pageHeight = browser.execute_script("return document.body.scrollHeight")
            totalScrolledHeight = browser.execute_script("return window.pageYOffset + window.innerHeight")
        
        total_placelived = self.get_placelived(browser, total_id)
        df_group = pd.DataFrame.from_dict({'FACEBOOK_LINK': total_id, 'PLACE_LIVED': total_placelived})
        
        return df_group
    
    
def run_facebook_scrape_group(username, password, search_string, headless=False, location='None', choose_public_group=True, min_group=20):
    lib_sys.init_log()
    
    log.printt('Login to Facebook.')
    browser = init_browser(headless=headless)
    try:
        login_facebook(browser, username, password)
    except:
        return
    
    log.printt('Facebook Bot: START scraping..\n')
    df_group = SearchGroup(browser).search_group(search_string, location, choose_public_group, min_group)
    df_group.to_csv('./output/scraper_group_{}_{}.csv'.format(search_string, location), index=False)
    
    browser.quit()
    log.printt('Facebook Bot: DONE.')


def run_facebook_scrape_member(username, password, groupid, headless=False, min_member = 20):
    lib_sys.init_log()
    
    log.printt('Login to Facebook.')
    browser = init_browser(headless=headless)
    try:
        login_facebook(browser, username, password)
    except:
        return
    
    log.printt('Facebook Bot: START scraping..\n')
    df_group = GetMemberID(browser).get_memberid(groupid, min_member)
    df_group.to_csv('./output/scraper_member_{}.csv'.format(groupid), index = False)
    
    browser.quit()
    log.printt('Facebook Bot: DONE.')




