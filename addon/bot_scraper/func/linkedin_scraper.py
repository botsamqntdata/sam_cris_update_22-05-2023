from addon import *



def run_company_scrape_info(filename=None, column_name=None, keyword='market cap | valuation billion',
        classname='div', att={'class': 'LGOjhe'}, num_run=30, num_export=10, method=1, min_delay=min_delay_default):
    lib_sys.init_log()

    data, output_name = import_file(filename)

    if column_name is None:
        col_index = 0
        column_name = data.columns[col_index]
    else:
        col_index = data.columns.get_loc(column_name)

    data_prune = data.dropna(subset=[column_name])
    data_prune = data_prune.drop_duplicates(subset=[column_name])

    if keyword not in data_prune.columns:
        data_prune[keyword] = np.nan
    else:
        data_exist = data_prune.dropna(subset=[keyword])
        data_prune = data_prune.drop(data_exist.index)

    data_prune = data_prune.iloc[:num_run]

    log.printt('Data processing: %s' % len(data_prune))

    first_result = True
    log.printt('Keyword: %s' % keyword)
    log.printt('Scraping Bot: START scraping..\n')

    if method == 1:
        for idx, row in data_prune.iterrows():
            t_start = time.time()
            print(idx)

            search_term = str(row[column_name])
            url = f'https://autocomplete.clearbit.com/v1/companies/suggest?query={search_term}'
            response = requests.get(url, headers=USER_AGENT)
            response.raise_for_status()

            result = json.loads(response.text)
            try:
                res = result[0]['domain'].split('//')[-1].split('/')[0]
                res = res.replace('www.', '')
                data.loc[idx, keyword] = res

            except:
                res = ''
                pass

            if first_result is True:
                log.printt('[%s] %s: %s __ %.2f seconds.' % (idx, row[column_name], res, time.time() - t_start))
                first_result = False

            if idx != data_prune.index[-1]:
                if (idx + 1) % num_export == 0:
                    [os.remove(os.path.join(util.path_output, f)) for f in os.listdir(util.path_output)
                        if f.find(output_name) != -1]
                    path_user = util.path_output + output_name + '__temp_%s.xlsx' % (idx + 1)
                    export_file(data, path_user)

            else:
                # remove all temp output
                log.printt('Remove all temporary outputs.')
                [os.remove(os.path.join(util.path_output, f)) for f in os.listdir(util.path_output)
                    if f.find(output_name) != -1]

                path_user = util.path_output + output_name + '__DONE.xlsx'
                export_file(data, path_user)

    else:
        for idx, row in data_prune.iterrows():
            t_start = time.time()
            print(idx)

            search_term = str(row[column_name]) + ' ' + keyword

            try:
                html = fetch_results(search_term)

            except requests.HTTPError as e:
                print(e)
                captcha_link = e.args[0].split('url: ')[-1]
                run_recaptcha_solver(captcha_link)

                html = fetch_results(search_term)
            time.sleep(min_delay)

            try:
                if classname is None or att is None:
                    result = parse_results(html)
                    res = result.loc[0, 'link'].split('//')[-1].split('/')[0]
                    res = res.replace('www.', '')
                    data.loc[idx, keyword] = res

                else:
                    soup = BeautifulSoup(html, 'html.parser')
                    result = soup.find(classname, attrs=att)
                    res = result.text
                    data.loc[idx, keyword] = res

                if first_result is True:
                    log.printt('[%s] %s: %s __ %.2f seconds.' % (idx, row[column_name], res, time.time() - t_start))
                    first_result = False

                if idx != data_prune.index[-1]:
                    if (idx + 1) % num_export == 0:
                        [os.remove(os.path.join(util.path_output, f)) for f in os.listdir(util.path_output)
                            if f.find(output_name) != -1]
                        path_user = util.path_output + output_name + '__temp_%s.xlsx' % (idx + 1)
                        export_file(data, path_user)

                else:
                    # remove all temp output
                    log.printt('Remove all temporary outputs.')
                    [os.remove(os.path.join(util.path_output, f)) for f in os.listdir(util.path_output)
                        if f.find(output_name) != -1]

                    path_user = util.path_output + output_name + '__DONE.xlsx'
                    export_file(data, path_user)

            except Exception as e:
                log.error('[%s] %s __ %s' % (idx, row[column_name], e))
                pass

    output_message = '\nScraping Bot: DONE.\nLog file: %slatest.log' % (util.path_log)
    log.printt(output_message)

    return output_message


def run_company_scrape_linkedin(filename=None, column_name=None, keyword='site:linkedin.com/in/ & linkedin ceo | founder',
        num_result=3, num_export=5, min_delay=60):
    lib_sys.init_log()

    data, output_name = import_file(filename)

    if column_name is None:
        col_index = 0
        column_name = data.columns[col_index]
    else:
        col_index = data.columns.get_loc(column_name)

    data_total = pd.DataFrame(columns=[column_name, 'link', 'title', 'info'])

    first_result = True
    log.printt('Keyword: %s' % keyword)
    log.printt('Scraping Bot: START scraping..\n')

    for idx, row in data.iterrows():
        t_start = time.time()
        print(idx)
        try:
            search_term = str(row.iloc[col_index]) + ' ' + keyword
            search_term = convert_ascii(search_term)

            results = scrape_google(search_term, num_result)
            results = results[[i.find('linkedin.com/in/') != -1 for i in results['link']]].reset_index(drop=True)
            results[column_name] = row[column_name]
            data_total = pd.concat([data_total, results], ignore_index=True)
            time.sleep(random.uniform(min_delay, min_delay + 10))

            if first_result is True:
                log.printt('[%s] %s:\n%s __ %.2f seconds.' % (idx, row[column_name], results.loc[0], time.time() - t_start))
                first_result = False

            if idx != data.index[-1]:
                if (idx + 1) % num_export == 0:
                    [os.remove(os.path.join(util.path_output, f)) for f in os.listdir(util.path_output)
                        if f.find(output_name) != -1]
                    path_user = util.path_output + output_name + '__temp_%s.xlsx' % (idx + 1)
                    data_temp = data_total.copy()
                    data_temp.columns = [column_name, 'LINKEDIN', 'title', 'info']
                    export_file(data_temp, path_user)
                    time.sleep(120)

            else:
                # remove all temp output
                log.printt('Remove all temporary outputs.')
                [os.remove(os.path.join(util.path_output, f)) for f in os.listdir(util.path_output)
                    if f.find(output_name) != -1]

                path_user = util.path_output + output_name + '__DONE.xlsx'
                data_temp = data_total.copy()
                data_temp.columns = [column_name, 'LINKEDIN', 'title', 'info']
                export_file(data_temp, path_user)

        except Exception as e:
            log.error('[%s] %s __ %s' % (idx, row[column_name], e))
            pass

    output_message = '\nScraping Bot: DONE.\nLog file: %slatest.log' % (util.path_log)
    log.printt(output_message)

    return output_message


def get_linkedin_info(browser, linkedin, min_delay):
    res = pd.Series()

    browser.get(linkedin)
    time.sleep(min_delay)

    try:
        element_list = browser.find_elements_by_xpath('//span[@class="visually-hidden"]')
        browser = remove_element(browser, element_list)
        element_list = browser.find_elements_by_xpath('//span[contains(@class, "dist-value")]')
        browser = remove_element(browser, element_list)

        profile = browser.find_element_by_xpath('//div[contains(@class, "ph5")]').text
        remove_dist = ['Connect\n', 'Message\n', 'More…\n', 'More']
        for x in remove_dist:
            profile = profile.replace(x, '')
        list_profile = profile.split('\n')

        fullname = list_profile[0].split(',')[0].split(' (')[0]
        #Remove special character
        fullname = re.sub('[^A-Za-z0-9]+ ', '', fullname)

        res['FULL_NAME'] = fullname
        res['FIRST_NAME'] = fullname.split(' ')[0]
        res['LAST_NAME'] = fullname.split(' ')[-1]

        job = list_profile[1]
        res['JOB_TITLE'] = job

    except:
        res['FULL_NAME'] = ''
        res['FIRST_NAME'] = ''
        res['LAST_NAME'] = ''
        res['JOB_TITLE'] = ''

    try:
        locality = [x for x in list_profile if 'Contact info' in x][0]
        locality = locality.replace(' Contact info', '')
        res['LOCALITY'] = locality
        locality_temp = locality.split(', ')
        res['CITY'] = locality_temp[0]
        try:
            res['STATE'] = locality_temp[1]
        except:
            res['STATE'] = ''
            pass
        res['COUNTRY'] = locality_temp[-1]

    except:
        res['LOCALITY'] = ''
        res['CITY'] = ''
        res['STATE'] = ''
        res['COUNTRY'] = ''

    try:
        company_name = list_profile[2]
        res['COMPANY_NAME'] = company_name

        connection = [x for x in list_profile if 'connection' in x][0]
        res['CONNECTION'] = str(connection)

    except:
        res['COMPANY_NAME'] = ''
        res['CONNECTION'] = ''

    try:
        # element_list = browser.find_elements_by_xpath('//a[@data-control-name="browsemap_profile"]')
        element_list = browser.find_elements_by_xpath('//li[contains(@class, "browsemap")]/a')
        list_href = [i.get_attribute('href').split('/in/')[-1] for i in element_list]
        res['ALSO_VIEWED'] = ', '.join(list_href).replace('/', '')

    except:
        res['ALSO_VIEWED'] = ''

    browser.get(linkedin + 'detail/contact-info/')
    time.sleep(5)

    try:
        twitter = browser.find_element_by_xpath('//a[contains(@href, "twitter.com/")]').text
        twitter = twitter.replace('twitter.com/', '')

    except:
        twitter = ''
    res['TWITTER'] = twitter

    try:
        email = browser.find_element_by_xpath('//a[contains(@href, "mailto")]').text

    except:
        email = ''
    res['EMAIL'] = email

    return res


def run_linkedin_crawl_info(username, password, filename=None, country=None, num_run=100, num_export=50,
    send=False, headless=True, min_delay=min_delay_default):
    import pytz, uuid
    import warnings
    warnings.filterwarnings('ignore')

    lib_sys.init_log()

    data, output_name = import_file(filename)

    data_temp = pd.DataFrame(
        columns = ['COMPANY_NAME', 'LINKEDIN', 'FIRST_NAME', 'LAST_NAME', 'FULL_NAME', 'JOB_TITLE',
                   'EMAIL', 'EMAIL_BACKUP', 'TWITTER', 'WEBSITE_URL', 'KEY', 'UNIQUE_ID', 'COUNTRY_CODE',
                   'LOCALITY', 'CITY', 'STATE', 'COUNTRY', 'CONNECTION', 'ALSO_VIEWED',
                   'DATE_ADDED', 'DATE_MODIFIED', 'TAGS', 'MEMBERSHIP_NOTES', 'FOLDER', 'CIVILITY',
                   'COMPANY_INDUSTRY', 'COMPANY_FOUNDED', 'COMPANY_SIZE', 'COMPANY_LINKEDIN']
        )

    data = pd.merge(data, data_temp, how='left')

    data_prune = data.dropna(subset=['LINKEDIN'])
    data_prune = data_prune.drop_duplicates(subset=['LINKEDIN'])
    data_exist = data_prune.dropna(subset=['FIRST_NAME'])
    data_prune = data_prune.drop(data_exist.index)
    data_prune = data_prune.iloc[:num_run]

    log.printt('Data processing: %s' % len(data_prune))

    browser = init_browser(headless=headless)
    try:
        login_linkedin(browser, username, password)
    except:
        return

    first_result = True
    log.printt('LinkedIn Bot: START crawling..\n')

    for idx, row in data_prune.iterrows():
        t_start = time.time()
        print(idx)
        try:
            linkedin = row['LINKEDIN']
            # Preprocessing url
            linkedin = 'https://www.linkedin.com' + linkedin.split('linkedin.com')[1]
            linkedin = linkedin.split('?')[0]
            linkedin = linkedin.replace('%2522', '')
            if linkedin[-1] != '/':
                linkedin += '/'

            res = get_linkedin_info(browser, linkedin, min_delay)

            if not pd.isnull(row['COMPANY_NAME']):
                company_name = row['COMPANY_NAME']
            else:
                company_name = res['COMPANY_NAME']

            if not pd.isnull(row['WEBSITE_URL']):
                website_url = row['WEBSITE_URL']
                website_url = website_url.replace('www.', '').replace('/', '')
            else:
                website_url = ''

            if country is None:
                try:
                    locality = res['LOCALITY'].split(', ')[-1]
                    country = [i for i in pytz.country_names if pytz.country_names[i] == locality][0]
                except:
                    try:
                        locality = res['LOCALITY'].split(', ')[0]
                        country = [i for i in pytz.country_names if pytz.country_names[i] == locality][0]
                    except:
                        country = 'NAN'

            uuid_str = uuid.uuid4().hex[:16]
            data.loc[idx, 'KEY'] = country + uuid_str
            data.loc[idx, 'UNIQUE_ID'] = uuid_str
            data.loc[idx, 'COUNTRY_CODE'] = country

            data.loc[idx, 'COMPANY_NAME'] = company_name
            data.loc[idx, 'LINKEDIN'] = linkedin
            data.loc[idx, 'WEBSITE_URL'] = website_url
            data.loc[idx, 'FULL_NAME'] = res['FULL_NAME']
            data.loc[idx, 'FIRST_NAME'] = res['FIRST_NAME']
            data.loc[idx, 'LAST_NAME'] = res['LAST_NAME']
            data.loc[idx, 'JOB_TITLE'] = res['JOB_TITLE']
            data.loc[idx, 'LOCALITY'] = res['LOCALITY']
            data.loc[idx, 'CITY'] = res['CITY']
            data.loc[idx, 'STATE'] = res['STATE']
            data.loc[idx, 'COUNTRY'] = res['COUNTRY']
            data.loc[idx, 'CONNECTION'] = res['CONNECTION']
            data.loc[idx, 'EMAIL'] = res['EMAIL']
            data.loc[idx, 'TWITTER'] = res['TWITTER']
            data.loc[idx, 'ALSO_VIEWED'] = res['ALSO_VIEWED']

#                if send is True:
#                    subject = 'Looking for a collaboration'
#                    message = "We're looking for intermediaries that support capital raising with btc/eth options for our clients. Let's connect for a strategic collaboration.\n\nHenry Duong, PhD, CFA, CAIA, PRM, ERP\nFounder, QT-Group\nPhone: +1 306 491 8799 | +1 236 458 7899\nWebsite: https://qntdata.com | https://qt-globalgroup.com"
#                    file = []
#
#                    send_linkedin(browser, linkedin, subject, message, file, min_delay)

            if first_result is True and res['FIRST_NAME'] != '':
                log.printt('[%s] %s:\n%s __ %.2f seconds.' % (idx, row['LINKEDIN'], data.loc[idx], time.time() - t_start))
                first_result = False

            if idx != data_prune.index[-1]:
                if (idx + 1) % num_export == 0:
                    [os.remove(os.path.join(util.path_output, f)) for f in os.listdir(util.path_output)
                        if f.find(output_name) != -1]
                    path_user = util.path_output + output_name + '__temp_%s.xlsx' % (idx + 1)
                    export_file(data, path_user)

            else:
                # remove all temp output
                log.printt('Remove all temporary outputs.')
                [os.remove(os.path.join(util.path_output, f)) for f in os.listdir(util.path_output)
                    if f.find(output_name) != -1]

                path_user = util.path_output + output_name + '__DONE.xlsx'
                export_file(data, path_user)

        except Exception as e:
            log.error('[%s] %s __ %s' % (idx, row[column_name], e))
            pass

    browser.quit()

    output_message = '\nLinkedIn Bot: DONE.\nLog file: %slatest.log' % (util.path_log)
    log.printt(output_message)

    return output_message


def run_linkedin_invitation_withdraw(username, password, page=10, headless=True, min_delay=min_delay_default):
    lib_sys.init_log()

    browser = init_browser(headless=headless)
    try:
        login_linkedin(browser, username, password)
    except:
        return

    sent_link = 'https://www.linkedin.com/mynetwork/invitation-manager/sent/?invitationType=&page=%s' % page
    browser.get(sent_link)
    time.sleep(min_delay)

    # Scroll to end of page
    browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(min_delay)

    log.printt('LinkedIn Bot: START removing..\n')

    element_list = browser.find_elements_by_xpath('//div[contains(@class, "display-flex ph2 pt1")]')
    for idx, elementID in enumerate(element_list):
        try:
            info_list = elementID.text.split('\n')
            time_invite = info_list[-2]

            if time_invite == '3 weeks ago' or time_invite == '4 weeks ago' or time_invite == '1 month ago':
                elementID.find_element_by_xpath('.//button[contains(@aria-label, "Withdraw")]').click()
                time.sleep(1)
                popup = browser.switch_to.active_element
                popup.find_element_by_xpath('//button[@class="artdeco-modal__confirm-dialog-btn ' +
                    'artdeco-button artdeco-button--2 artdeco-button--primary ember-view"]').click()

                name = info_list[1]
                log.printt('[%s] %s: %s' % (idx, name, time_invite))

            time.sleep(5)

        except:
            pass

    browser.quit()

    output_message = '\nLinkedIn Bot: DONE.\nLog file: %slatest.log' % (util.path_log)
    log.printt(output_message)

    return output_message




