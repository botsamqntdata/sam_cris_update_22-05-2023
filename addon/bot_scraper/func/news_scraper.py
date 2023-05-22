from addon import *



def run_news_scraper(keyword, num_result=5):
    lib_sys.init_log()
    
    news_json = []
    directory = util.path_output + 'news_' + keyword
    if not os.path.exists(directory):
        log.printt('Creating output directory: %s' % directory)
        os.makedirs(directory)
        
    url = f'https://www.google.com/search?q={keyword}+news&tbm=nws&hl=en'
    
    response = requests.get(url, headers = USER_AGENT)
    soup = BeautifulSoup(response.text, 'html.parser')
    result_block = soup.find_all('a', {'class':'WlydOe'})
    
    link = []
    for result in result_block[:num_result]:
        link.append(result['href'])

    log.printt('Scraping Bot: START scraping..\n')
        
    #news-please
    try:
        article_newsplease = NewsPlease.from_urls(link)
        for i, v in article_newsplease.items():
            news_json.append(v.get_dict())
        
    except:
        pass

    #newspaper3k
    for i, v in enumerate(link):
        try:
            article_3k = Article(v)
            article_3k.download()
            article_3k.parse()
            article_3k.nlp()
            
            if len(news_json[i]) > 0:
                if len(article_3k.movies) > 0:
                    news_json[i]['movies'] = article_3k.movies
                
                if len(article_3k.keywords) > 0:
                    news_json[i]['nlp'] = article_3k.keywords
                    
                if len(article_3k.summary) > 0:
                    news_json[i]['summary'] = article_3k.summary
            
            with open(directory + '/' + news_json[i]['filename'], 'w') as outfile:
                json.dump(news_json[i], outfile, indent=4, sort_keys=True, default=str)
                
        except:
            pass
    
    log.printt('Output: %s\n' % directory)
    log.printt('Scraping Bot: DONE.')


def run_news_scraper_from_file(filename, num_result = 5):
    from newspaper import Article
    from newsplease import NewsPlease
    import nltk
    nltk.download('punkt')

    data, output_name = import_file(filename)
    log.printt('Scraping Bot: START scraping..\n')
    
    for keyword in data.iloc[:,0]:
        run_news_scraper(keyword, num_result)
    
    log.printt('Scraping Bot: DONE.')
    

#def push_news(directory):
#    #Get list file
#    from os import listdir
#    from os.path import isfile, join
#    
#    list_file = [file for file in listdir(directory) if isfile(join(directory, file))]
#    
#    #Create new folder for if not exist 
#    file_metadata = {
#        'name': directory,
#        'mimeType': 'application/vnd.google-apps.folder',
#        'parents': [tempodata_id]
#    }
#    tempo_id = drive_service.files().create(body = file_metadata, fields = 'id').execute()['id']
#    
#    push_file(filename, path, folder_id)


#run_news_scraper_from_file('news_scraper.xlsx', num_result=1)


