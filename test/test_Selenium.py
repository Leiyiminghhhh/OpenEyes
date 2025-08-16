# -*- coding: utf-8 -*-

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService

# 设置正确的驱动路径
service = ChromeService(executable_path="D:\code\OpenEyes\chromedriver-win64\chromedriver.exe")

options = webdriver.ChromeOptions()
driver = webdriver.Chrome(service=service, options=options)


# 打开一个网站
# driver.get("https://www.163.com/news/article/K6UT4SHK000189FH.html")
driver.get("https://cn.nytimes.com/world/20250814/yalta-trump-putin-meeting-alaska/")


# 获取页面标题
print(driver.title)

# 关闭浏览器
driver.quit()