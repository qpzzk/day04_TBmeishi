from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
import re
from pyquery import PyQuery as pq
from config import *
import pymongo

client=pymongo.MongoClient(MONGO_URL)
db=client[MONGO_DB]

browser=webdriver.Chrome()
wait=WebDriverWait(browser,10)   #设置好浏览器等待时间为10s

def search():
    try:
        browser.get('https://www.taobao.com')
        input=wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR,'#q'))
        )
        #选中标签后,直接右键css里面有css-select的选项,然后粘贴过来
        submit=wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#J_TSearchForm > div.search-button > button')))
        input.send_keys(KEYWORD)
        submit.click()
        #查看总共有多少页
        total=wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#mainsrp-pager > div > div > div > div.total')))
        get_products()
        return total.text  #会显示总共...页
    except TimeoutError:
        return search() #访问不到就得继续访问,此时会出现错误,所以得递归
#调转页码
def next_page(page_number):
    try:
        input=wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR,'#mainsrp-pager > div > div > div > div.form > input'))
        )  #选中转页框
        #点击跳转的按钮
        submit=wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#mainsrp-pager > div > div > div > div.form > span.btn.J_Submit')))
        input.clear()
        input.send_keys(page_number)
        submit.click()
        #验证是否跳转成功,要是跳转成功了,会转到相应的页码
        # 在浏览器选择那个高亮的选择器,将高亮的和前面当前页码相比较
        wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#mainsrp-pager > div > div > div > ul > li.item.active > span'),str(page_number)))
        get_products()
    except TimeoutError:
        return next_page(page_number)

#获取页面详细信息
def get_products():
    #判断页面是否加载成功
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#mainsrp-itemlist .items .item')))
    #用pyquery将其取出来
    html=browser.page_source
    doc=pq(html)
    items=doc('#mainsrp-itemlist .items .item').items()
    for item in items:
        #都是找最近的div模块的内容
        product = {
            'image':item.find('.pic .img').attr('src'),
            'price':item.find('.price.g_price.g_price-highlight').text(),
            'deal':item.find('.deal-cnt').text()[:-3],
            'title':item.find('.title').text(),
            'shop':item.find('.shop').text(),
            'local':item.find('.location').text()

        }
        print(product)
        save_to_mongo(product)

#保存MONGO_DB方法
def save_to_mongo(result):
    try:
        if db[MONGO_TABLE].insert(result):
            print("存储数据成功",result)
    except Exception:
        print("存储数据失败",result)

def main():
    try:
        total=search()
        total=int(re.compile('(\d+)').search(total).group(1))
        for i in range(2,total+1):
            next_page(i)
    except Exception:
        print("出错了")
    finally:  #无论结果怎么样,都要关闭浏览器
        browser.close()

if __name__=='__main__':
    main()

