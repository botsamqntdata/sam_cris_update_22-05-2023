from addon import *



def run_trading_insider_info(insider_url=None, export=False, filename='trading_insider_info.xlsx'):
    import warnings
    warnings.filterwarnings('ignore')
    
    lib_sys.init_log()
    
    if insider_url is None:
        url = 'https://biv.com/search/site?keys=trading%20insider'
        response = requests.get(url, headers = USER_AGENT, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')
        result_block = soup.select('a[href*=biv.com/article/]')[0]
        
        insider_url = result_block['href']
        
    response = requests.get(insider_url, headers = USER_AGENT, verify=False)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    title = soup.find('span', 
                {'class': 'field field--name-title field--type-string field--label-hidden'}).text
    result_block = soup.find_all('p')[1:11]
    
    log.printt(title)

    df = pd.DataFrame(columns = ['Content'])    
    for idx, result in enumerate(result_block):
        df.loc[idx, 'Content'] = result.text
        log.printt(result.text)

    if export is True:
        path = util.path_output + filename
        with pd.ExcelWriter(path) as writer:  
            df.to_excel(writer, index = False)
        writer.close()


def crawl_barchart_ticker(browser, ticker, min_delay=min_delay_default):
    url = 'https://www.barchart.com/stocks/quotes/' + ticker + '/opinion'
    
    browser.get(url)
    time.sleep(min_delay)
    
    #Closing ads
    try:
        login_popup = browser.find_element_by_xpath('//div[@class="reveal-modal-bg fade in"]')
        browser.execute_script("""
        var element = arguments[0];
        element.parentNode.removeChild(element);
        """, login_popup)
        
    except:
        pass
    
    try:
        browser.find_element_by_xpath('//div[@class="adhesion_collapse"]').click()
        
        element = browser.find_element_by_xpath('//div[@class="bc-webinar-card no-print"]')
        browser.execute_script("""
        var element = arguments[0];
        element.parentNode.removeChild(element);
        """, element)

    except:
        pass
    
    #Overall Average
    elementID = browser.find_element_by_xpath('//div[@class="block-content clearfix"]')
    elementID.screenshot(util.path_output + ticker + '_overall-average.png')
    
    #Snapshot_Opinion
    elementID = browser.find_element_by_xpath('//div[@class="background-widget"]')
    elementID.screenshot(util.path_output + ticker + '_snapshot-opinion.png')
    
    #Barchart Opinion
    browser.find_elements_by_xpath('//div[@class="input-radio"]')[-1].click()
    elementID = browser.find_element_by_xpath('//div[@class="barchart-content-block ' + \
                    'bc-opinion-trading-performance"]')
    browser.execute_script("window.scrollTo(0, 450);")
    elementID.screenshot(util.path_output + ticker + '_barchart-opinion.png')
    
    
#    import base64
#    import io
#    from matplotlib import pyplot as plt
#    import matplotlib.image as mpimg
#    
#    browser.execute_script("window.scrollTo(0, 450);")
#    i = base64.b64decode(elementID.screenshot_as_base64)
#    i = io.BytesIO(i)
#    i = mpimg.imread(i, format='JPG')
#    
#    plt.imshow(i, interpolation='nearest')
#    plt.show()


def run_trading_crawl_barchart(list_ticker):
    if not isinstance(list_ticker, list):
        list_ticker = list(list_ticker)
        
    #Open link on chrome
    browser = init_browser(headless=True)
        
    for ticker in list_ticker:
        print(ticker)
        try:
            crawl_barchart_ticker(browser, ticker)
        except:
            pass
        
    browser.quit()
    
    
    
    
    


