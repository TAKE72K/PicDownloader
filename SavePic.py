# -*- coding: utf-8 -*-
#=================================#

#             USER                #

#=================================#

IDOL="nansu"
# 留空白的話就是全載

"""

請只更改以上區域。

"""


MODE=2

# first_link='https://news.walkerplus.com/article/161893/940070_615.jpg'
# last_link='https://news.walkerplus.com/article/161893/940101_615.jpg'

first='https://news.walkerplus.com/article/161893/940'
last='_615.jpg'
setup_num=70
end_num=101
mode_3_url='https://www.pixiv.net/member_illust.php?mode=medium&illust_id=68987922'
"""
1:Download from number
2:Download from mongodb
3:Download single
"""

from string import Template
import os
from urllib.request import urlretrieve,urlopen
from urllib.error import HTTPError,URLError

# Process Bar
from tqdm import tqdm

if IDOL=="":
    folder='SavePic'
else:
    folder='SavePic_'+IDOL
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
                    filename=folder+"/SavePIC_LOG.txt")
logger = logging.getLogger(__name__)


def delreplist(list):
    newlist=[]
    for i in list:
        if i not in newlist:
            newlist.append(i)
    return newlist

PIXIV_headers={
    'User-Agent':'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)',
    'Referer':'https://www.pixiv.net'
}

def pic_detecter(link):
    logger.info("URL detecting:%s",link)
    link_type=""
    tw_link=[]
    type=""

    # detect link type
    if link.find("twitter.com")!=-1:
        link_type="twitter"
    elif link.find("pbs.twimg.com")!=-1:
        tw_link.append(link)
        return tw_link
    elif link.find("www.pixiv.net")!=-1:
        link_type="pixiv"
    else:
        return False

    # open url
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
            newlink=""
            if link_type=="twitter":
                start=str(i).find('https://pbs.twimg.com/media/')
            elif link_type=="pixiv":
                #logger.info("PIXIV URL(Not support now):%s",link)
                #return
                start=str(i).find('https://embed.pixiv.net/')

            if start!=-1:
                # test if jpg or png
                if link_type=="twitter":
                    if str(i).find('.jpg')!=-1:
                        end=str(i).find('.jpg')
                        type="JPG"
                    elif str(i).find('.png')!=-1:
                        end=str(i).find('.png')
                        type="PNG"
                    else:
                        logger.error("Unknown file type:%s",link)
                        type="Unknown"
                        return False
                elif link_type=="pixiv":
                    end=str(i).find('">')
                    type="JPG"

                index=start
                while(index<end):
                    newlink+=str(i)[index]
                    index+=1
                if newlink!='':
                    if link_type=="twitter":
                        if type=="JPG":
                            newlink+=".jpg:large"
                        elif type=="PNG":
                            newlink+=".png:large"
                    elif link_type=="pixiv":
                        pass
                    tw_link.append(newlink)
                else:
                    logger.warning("URL detected failed:%s",link)
                    logger.info("Retrying")
    except UnboundLocalError:
        logger.warning("Unknown url:%s",link)
        return False
    new_link=delreplist(tw_link)
    for i in new_link:
        logger.info("URL detected susessful(%s):%s",type,i)
    return new_link

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
        if IDOL=="":
            colle={}
        else:
            colle={"name":IDOL}
        ins=pic_db.find(colle)
        total_data=pic_db.count_documents(colle)+1
        print("  Analysis Link...")
        pbar1 = tqdm(total=total_data)
        for data in ins:
            tw_url=data['url']
            pic_url=pic_detecter(tw_url)
            if pic_url!=False:
                for i in pic_url:
                    links.append(i)
            pbar1.update(1)
        temp=links
        links=delreplist(temp)
        pbar1.update(1)
        pbar1.close()

    elif MODE==3:
        pic_url=pic_detecter(mode_3_url)
        if pic_url!=False:
            for i in pic_url:
                links.append(i)

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
            if link.find('https://i.pximg.net/')!=-1:
                urlretrieve(link,local,data=PIXIV_headers)
            else:
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
