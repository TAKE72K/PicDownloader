# -*- coding: utf-8 -*-
MODE=2
"""
1:Download from number
2:Download from mongodb
"""

from string import Template
import os
from urllib.request import urlretrieve,urlopen
from urllib.error import HTTPError,URLError

# Process Bar
from tqdm import tqdm


folder='SavePic'
def ensure_dir(file_path):
    if not os.path.exists(file_path):
        os.makedirs(file_path)
ensure_dir(folder)

# ---MongoDB
import pymongo
from pymongo import MongoClient

url = "mongodb://$dbuser:$dbpassword@ds149732.mlab.com:49732/heroku_jj2sv6sm"
mongo_us = 'admin'
mongo_ps = os.environ['MONGO_PSW']
temp=Template(url)
mongo_url=temp.substitute(dbuser=mongo_us,dbpassword=mongo_ps)
client = MongoClient(mongo_url)
db = client['heroku_jj2sv6sm']

# ---error log setting
import logging
logging.basicConfig(format='[%(asctime)s](%(levelname)s) %(name)s - %(message)s',
                    level=logging.INFO,
                    filename="SavePic/SavePIC_LOG.txt")
logger = logging.getLogger(__name__)



# first_link='https://news.walkerplus.com/article/161893/940070_615.jpg'
# last_link='https://news.walkerplus.com/article/161893/940101_615.jpg'

first='https://news.walkerplus.com/article/161893/940'
last='_615.jpg'
setup_num=70
end_num=101



def twitter_pic_detecter(link):
    if link.find("twitter")==-1:
        return False
    tw_link=""

    try:
        f=urlopen(link)
    except HTTPError:
        logger.warning("Bad Request:%s",link)
        return False
    except:
        logger.warning("Unknown error:%s",link)
        return False

    try:
        for i in f:
            if str(i).find('https://pbs.twimg.com/media/')!=-1:
                start=str(i).find('https://pbs.twimg.com/media/')
                end=str(i).find('.jpg')
                index=start
                while(index<end):
                    tw_link+=str(i)[index]
                    index+=1
                if tw_link!='':
                    tw_link+=".jpg:large"
                    logger.info("URL detected susessful:%s",link)
                    break
                else:
                    logger.warning("URL detected failed:%s",link)
                    logger.info("Retrying")
    except UnboundLocalError:
        logger.warning("Unknown url:%s",link)
        return False
    return tw_link

################################################
#                   main                       #
################################################
def main():
    links=[]
    if MODE==1:
        for i in range(setup_num,end_num+1):

            if i<100:
                num='0'+str(i)
            else:
                num=str(i)
            links.append(first + num + last)
    elif MODE==2:
        pic_db=db['ml_idol_pic_colle']
        ins=pic_db.find()
        total_data=pic_db.count_documents({})
        print("  Analysis Twitter Link...")
        pbar1 = tqdm(total=total_data)
        for data in ins:
            tw_url=data['url']
            pic_url=twitter_pic_detecter(tw_url)
            if pic_url!=False:
                links.append(pic_url)
            pbar1.update(1)
        pbar1.close()

    x=1
    link_num=len(links)
    print("  Downloading picture...")
    pbar2 = tqdm(total=link_num)
    for link in links:
        ensure_dir(folder)
        name='%s.jpg'
        PATH=folder+'/'+name
        local = os.path.join(PATH % x)  #檔案儲存位置
        try:
            urlretrieve(link,local)
            logger.info("(%d)Download susessful:%s",x,link)
        except HTTPError as e:
            logger.error("(%d)HTTPError at:%s",x,link)
            x-=1
        except URLError:
            logger.error("(%d)URLError at:%s",x,link)
        except ValueError:
            logger.error("(%d)ValueError at:%s",x,link)
        except:
            logger.error("(%d)UnknownError at:%s",x,link)

        finally:
            x+=1
        pbar2.update(1)
    pbar2.close()

################################################
#                   program                    #
################################################
if __name__ == '__main__':
    main()
