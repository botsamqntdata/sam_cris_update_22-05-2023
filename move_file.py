import os, sys
import shutil
from os import listdir
from os.path import isfile, join
import json
from datetime import datetime, timedelta



path = '/home/qtdata/Desktop/hr01.qtdata_Uchiha/'
list_file = [file for file in listdir(path) if isfile(join(path, file))]
year = 21

for i in range(1, 13):        
    month = datetime(1900, i, 1).strftime('%b').upper()
    directory = f'{path}{month}-{year}'
    if not os.path.exists(directory):
        os.makedirs(directory)
    files = [file for file in list_file if file.find(f'{month}-{year}') != -1]
    for file in files:
        source = path + file
        destination = directory + '/' + file
        shutil.move(source, destination)
    
