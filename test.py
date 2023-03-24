# 爬虫主文件
import threading
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium import webdriver
from selenium.common import exceptions  # selenium异常模块
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import csv
import os
import time
import json
import django
import pandas as pd
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', '就业数据分析.settings')
django.setup()
from myApp.models import JobInfo


class spider(object):
    def __init__(self, type):
        self.type = type  # 岗位关键字
        self.spiderUrl = "https://www.ncss.cn/student/jobs/index.html"

    def startBrowser(self):
        # FireFox
        # selenium对firefox的支持组件操作由webdriver中的FirefoxOptions实现
        # 如果时Chrome浏览器则使用webdriver.ChromeOptions()
        # edge没有option！！
        options = webdriver.FirefoxOptions()
        # options.add_argument('--headless')    # 无窗口
        driver = webdriver.Firefox(
            executable_path=r"D:\PYYYYY\pythonProject\就业数据分析\spider\geckodriver.exe",  # 这里必须要是绝对路径
            firefox_binary=r"C:\Program Files\Mozilla Firefox\firefox.exe",  # firefox执行文件的绝对路径
            options=options)
        return driver

    def main(self):
        driver = self.startBrowser()

        driver.get(self.spiderUrl)
        driver.implicitly_wait(10)
        driver.maximize_window()  # 最大化窗口
        time.sleep(random.uniform(1, 3))  # 随机休眠

        # 主窗口
        mainWindow = driver.current_window_handle
        # 点击全国
        driver.find_element(by=By.XPATH, value='/html/body/div[2]/div[1]/div/div[2]/div[5]/ul[1]/li[1]').click()
        time.sleep(1)
        # 输入要搜索的职位
        driver.find_element(by=By.XPATH, value='//*[@id="searchBar"]/div[4]/input').send_keys(self.type)
        driver.find_element(by=By.XPATH, value='//*[@id="jobSearch"]').click()
        time.sleep(1)
        # 在页数输入99999获取最大页数//*[@id="page"]/input
        driver.find_element(by=By.XPATH, value='//*[@id="page"]/input').send_keys('99999')
        time.sleep(1)
        driver.find_element(by=By.XPATH, value='//*[@id="page"]/a[last()]').click()
        time.sleep(1)
        pageMax = driver.find_element(by=By.XPATH, value='//*[@id="page"]/span').text

        time.sleep(1)
        # driver.find_element(by=By.XPATH, value='//*[@id="page"]/input').send_keys('1')
        # driver.find_element(by=By.XPATH, value='//*[@id="page"]/a[last()]').click()
        # 返回第一页
        driver.find_element(by=By.XPATH, value='//*[@id="jobSearch"]').click()
        time.sleep(1)

        # 根据总页数开始爬取数据
        for i in range(0, int(pageMax)):

            if i != 0:
                # 找到下一页
                el = driver.find_elements(By.CSS_SELECTOR, '.next')[0]
                if not el:
                    break
                el.click()

            print('正在爬取第{}页数据'.format(i + 1))
            try:
                # 查找福利（福利与职位信息不在同一个list里，有些职位信息没有福利的元素）
                time.sleep(0.1)
                companyTags = []
                # 存储福利的信息
                tagsrow = driver.find_elements(By.CSS_SELECTOR, '.job-list-box .tagsrow')
                # 每页10条职位信息，10条福利信息（但可能少于10条福利信息）
                for div in tagsrow:
                    welfare = div.find_element(By.CSS_SELECTOR, '.comtags').text
                    # 判断是否有福利信息的元素
                    # 有福利信息元素
                    if welfare:
                        if welfare.find('-') != -1:
                            companyTags.append('无')
                        else:
                            companyTags.append(welfare)
                    # 没有找到福利信息元素
                    else:
                        companyTags.append("无")

                # 获取页面招聘信息LIST，10条
                jobList = driver.find_elements(By.CSS_SELECTOR, '.job-list-box .jobList')

                # 循环从joblist中获取职位信息
                for x, div in enumerate(jobList):
                    try:
                        time.sleep(0.01)
                        print('正在爬取第{}条数据'.format(x + 1))
                        job_Data = []
                        # 工作名
                        title = div.find_element(By.CSS_SELECTOR, '.first-ul h5 a').text
                        # 省份、专业（未处理）
                        province_major = div.find_element(By.CSS_SELECTOR, '.first-ul li:nth-last-child(1)').text
                        # 公司类型、人数、招聘人数（未处理）
                        find_type = div.find_element(By.CSS_SELECTOR,
                                                     '.job-list-mid .company-ul li:nth-last-child(1) span').text
                        # 学历、薪资（未处理）
                        educational = div.find_element(By.CSS_SELECTOR, '.first-ul li').text
                        # 头像
                        companyAvatar = div.find_element(By.CSS_SELECTOR, '.fl .img-box img').get_attribute('src')
                        # 招聘详情页
                        detailUrl = div.find_element(By.CSS_SELECTOR, '.first-ul h5 a').get_attribute('href')
                        # 公司详情页
                        companyUrl = div.find_element(By.CSS_SELECTOR, '.company-ul h5 a').get_attribute('href')

                        # 公司名称
                        companyTitle = div.find_element(By.CSS_SELECTOR, '.job-list-mid .company-ul li h5 a').text
                        # 薪资（未处理）
                        salarys = div.find_element(By.CSS_SELECTOR, '.job-list-left .first-ul li span').text
                        # 发布时间
                        createTime = div.find_element(By.CSS_SELECTOR, '.btns .time-sp').text.split(" ")[0]

                        # 初步处理公司类型、人数、招聘人数
                        arg = find_type.split(" | ")
                        # 页面上存在三个信息时：公司类型、公司人数、招聘人数
                        if len(arg) == 3:
                            # 公司类型
                            companyNature = arg[0]
                            # 招聘人数
                            if arg[2].find('招聘人数不限') != -1:
                                numberPeople = 0
                            else:
                                numberPeople = arg[2].replace('招聘', '').replace('人', '')

                            # 企业人数
                            if arg[1].find('以上') != -1:
                                companyPeople = []
                                if arg[1].find('人以上') != -1:
                                    companyPeople.append(int(arg[1].replace('人以上', '')))
                                    companyPeople.append(int(arg[1].replace('人以上', '')))
                                else:
                                    companyPeople.append(int(arg[1].replace('以上', '')))
                                    companyPeople.append(int(arg[1].replace('以上', '')))
                            elif arg[1].find('员工数量') != -1:
                                companyPeople = [0, 0]
                            else:
                                companyPeople = list(map(lambda x: int(x), arg[1].replace('人', '').split('-')))

                        # 页面上存在一个信息时：招聘人数
                        elif len(arg) == 1:
                            # 公司类型
                            companyNature = '未知'
                            # 公司人数
                            companyPeople = [0, 0]
                            # 招聘人数
                            if arg[0].find('招聘人数不限') != -1:
                                numberPeople = 0
                            else:
                                numberPeople = arg[0].replace('招聘', '').replace('人', '')

                        # 页面上存在两个信息时，可能出现： 公司类型、招聘人数  公司人数、招聘人数
                        elif len(arg) == 2:
                            # arg[0]处理：企业人数/公司类型
                            if arg[0].find('人') != -1 or arg[0].find('以上') != -1:
                                if arg[0].find('以上') != -1:
                                    companyPeople = []
                                    if arg[0].find('人以上') != -1:
                                        companyPeople.append(int(arg[0].replace('人以上', '')))
                                        companyPeople.append(int(arg[0].replace('人以上', '')))
                                    else:
                                        companyPeople.append(int(arg[0].replace('以上', '')))
                                        companyPeople.append(int(arg[0].replace('以上', '')))

                                elif arg[0].find('员工数量') != -1:
                                    companyPeople = [0, 0]
                                else:
                                    companyPeople = list(map(lambda x: int(x), arg[0].replace('人', '').split('-')))
                                # 公司类型
                                companyNature = '未知'
                            else:
                                # 公司类型
                                companyNature = arg[0]
                                companyPeople = [0, 0]
                            # 招聘人数
                            if arg[1].find('招聘人数不限') != -1:
                                numberPeople = 0
                            else:
                                numberPeople = arg[1].replace('招聘', '').replace('人', '')

                        # 获取处理薪资
                        if salarys.find('面议') != -1:
                            salary = [0, 0]  # 面议
                        else:
                            salary = list(map(lambda x: float(x) * 1000, salarys.replace('K/月', '').split('-')))

                        # 省份
                        province = province_major.split(' | ')[0]

                        # 学历
                        educational = educational.split(' | ')[0]

                        # 专业
                        major = province_major.split(' | ')[1]

                        # 福利
                        welfare = companyTags[x]

                        driver.implicitly_wait(5)

                        # 点击进入招聘信息详情页
                        div.find_element(By.CSS_SELECTOR, '.first-ul h5 a').send_keys(Keys.ENTER)
                        time.sleep(0.01)
                        # 切换窗口
                        for handle in driver.window_handles:
                            # 先切换到该窗口
                            driver.switch_to.window(handle)
                            # 得到该窗口的标题栏字符申，判断是不是我们要操作的那个窗口
                            if title in driver.title:
                                # 如果是，那么这时候ebDriver对象就是对应的该该窗口，正好，跳出循环
                                break
                            # wd.title属性是当前窗口的标题栏文本
                        # 行业初始化
                        industry = ''
                        # 领域初始化
                        field = ''

                        time.sleep(0.02)
                        # 找到省份城市元素
                        citys = driver.find_element(By.XPATH,
                                                    value='//*[@id="content"]/div/div[1]/div[1]/ul[4]/li/div').text
                        # 行业和领域的元素可能不存在
                        try:
                            field = driver.find_element(By.XPATH, value='//*[@id="industrySectors"]').text
                            industry = driver.find_element(By.XPATH, value='//*[@id="mainindustries"]').text
                        except:
                            pass
                        # 城市初始化
                        city = ''
                        # 城市处理
                        if citys.find('广西') != -1 or citys.find('宁夏') != -1 or citys.find('内蒙古') != -1 or citys.find(
                                '西藏') != -1 or citys.find('新疆') != -1:
                            if citys.find('广西') != -1:
                                city = citys.replace('广西', '')
                            if citys.find('宁夏') != -1:
                                city = citys.replace('宁夏', '')
                            if citys.find('内蒙古') != -1:
                                city = citys.replace('内蒙古', '')
                            if citys.find('西藏') != -1:
                                city = citys.replace('西藏', '')
                            if citys.find('新疆') != -1:
                                city = citys.replace('新疆', '')
                        elif citys.find('北京') != -1 or citys.find('天津') != -1 or citys.find('上海') != -1 or citys.find(
                                '重庆') != -1:
                            if citys.find('北京') != -1:
                                city = '北京市'
                            if citys.find('天津') != -1:
                                city = '天津市'
                            if citys.find('上海') != -1:
                                city = '上海市'
                            if citys.find('重庆') != -1:
                                city = '重庆市'
                        elif citys.find('香港') != -1 or citys.find('澳门') != -1:
                            if citys.find('香港') != -1:
                                city = '香港'
                            if citys.find('澳门') != -1:
                                city = '澳门'
                        elif citys.find('全国') != -1:
                            city = ''
                        elif citys.find('省') != -1:
                            city = citys.split('省')[1]

                        # 关闭当前窗口并回到原本窗口

                        print('岗位名字:', title, '省份:', province, '城市', city, '学历:', educational, '专业:', major)
                        print('公司名字:', companyTitle, '创建时间:', createTime, '公司头像:', companyAvatar, '招聘详情地址:', detailUrl,
                              '公司详情地址:', companyUrl)
                        print('公司性质:', companyNature, '招聘人数:', numberPeople, '公司人数:', companyPeople, '薪资:', salary,
                              '公司福利:', welfare)
                        print('行业:', industry, '领域:', field)

                        # 处理过的信息添加到job_Data
                        job_Data.append(title)
                        job_Data.append(province)
                        job_Data.append(city)
                        job_Data.append(educational)
                        job_Data.append(major)
                        job_Data.append(salary)
                        job_Data.append(welfare)
                        job_Data.append(companyTitle)
                        job_Data.append(companyAvatar)
                        job_Data.append(companyNature)
                        job_Data.append(industry)
                        job_Data.append(field)
                        job_Data.append(companyPeople)
                        job_Data.append(numberPeople)
                        job_Data.append(detailUrl)
                        job_Data.append(companyUrl)
                        job_Data.append(createTime)

                        # 信息保存到数据库
                        self.save_to_csv(job_Data)
                        # 关闭driver
                        driver.close()
                        # 切换到主窗口
                        driver.switch_to.window(mainWindow)

                    except:
                            print(" 、算术异常之一")
                            # 切换到主窗口
                            driver.switch_to.window(mainWindow)
                    finally:
                            continue

            except:
                print("程序发生了数字格式异常、算术异常之一")
                            # 切换到主窗口
                driver.switch_to.window(mainWindow)
                continue

    # 清理数据
    def clear_csv(self):
        df = pd.read_csv('./temp.csv')
        df.dropna(inplace=True)  # 更改源数据
        df.drop_duplicates(inplace=True)  # 删除数据
        # df['salaryMonth'] = df['salaryMonth'].map(lambda x: x.replace('薪', ''))
        print("总数据为%d" % df.shape[0])
        return df.values

    # 数据保存到数据库
    def save_to_sql(self):
        data = self.clear_csv()
        for job in data:
            JobInfo.objects.create(
                title=job[0],
                province=job[1],
                city=job[2],
                educational=job[3],
                major=job[4],
                salary=job[5],
                welfare=job[6],
                companyTitle=job[7],
                companyAvatar=job[8],
                companyNature=job[9],
                industry=job[10],
                field=job[11],
                companyPeople=job[12],
                numberPeople=job[13],
                detailUrl=job[14],
                companyUrl=job[15],
                createTime=job[16]
            )

    # 数据保存到本地
    def save_to_csv(self, rowData):
        with open('./temp.csv', 'a', newline='', encoding='utf8') as wf:
            writer = csv.writer(wf)
            writer.writerow(rowData)

    def init(self):
        if not os.path.exists('./temp.csv'):
            with open('./temp.csv', 'a', newline='', encoding='utf8') as wf:
                writer = csv.writer(wf)
                writer.writerow(
                    ["title", "province", "city", "educational", "major", "salary", "welfare", "companyTitle",
                     "companyAvatar",
                     "companyNature", 'industry', 'field', "companyPeople", "numberPeople", "detailUrl", "companyUrl",
                     "createTime"])


if __name__ == '__main__':
    spiderObj = spider("")
    spiderObj.init()
    spiderObj.main()
    spiderObj.save_to_sql()
