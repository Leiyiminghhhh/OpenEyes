import datetime
import time

from util.logger import get_logger
from util.store_util import Record
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By

TEST_MODE="test"

class Collector:
    def __init__(self, config):
        self.url = config.get("url")
        self.source = config.get("source")
        self.type = config.get("type")
        self.logger = get_logger("collection_" + self.source +".log")
        self.mode = config.get("mode")
        self.interval = config.get("interval", 1)

    def __repr__(self) -> str:
        return "<Collector url=%s, source=%s, type=%s>" % (self.url, self.source, self.type)

    # 收集数据
    def Collect(self):
        self.logger.info(
            "--------------------------- Collecting data ---------------------------")

class SimpleCollector(Collector):
    def __init__(self, config):
        super().__init__(config)
        self.data = {}

    def Collect(self):
        super().Collect()
        self.logger.info("使用Selenium收集URL: %s" % self.url)

        try:
            # 设置驱动路径
            service = ChromeService(
                executable_path="D:\\code\\OpenEyes\\chromedriver-win64\\chromedriver.exe")
            options = webdriver.ChromeOptions()
            # options.add_argument('--headless')  # 无头模式
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')

            driver = webdriver.Chrome(service=service, options=options)
            driver.get(self.url)
            time.sleep(5)

            # 收集页面上的所有链接
            links = driver.find_elements(By.TAG_NAME, "a")
            idx = 0
            for link in links:
                href = link.get_attribute("href")
                title = link.get_attribute("title")
                inner_title = ""
                try:
                    title_elements = link.find_elements(By.CSS_SELECTOR, "[title]")
                    if title_elements:
                        inner_title = title_elements[0].get_attribute("title")
                except:
                    pass
                effective_title = title or inner_title

                if self.is_useful(href, effective_title) and href not in self.data:
                    if self.mode == TEST_MODE and idx > 5:
                        break
                    idx += 1
                    self.data[href] = Record(
                        time=datetime.datetime.now(),
                        title=effective_title,
                        source=self.source,
                        content=self.get_content(driver, href),
                        tags="[]",
                        type=self.type,
                        url=href)

            self.logger.info("成功收集到 %d 个URL" % len(self.data))
            for i, key in enumerate(self.data):
                self.logger.info("%d: %s" % (i, self.data[key]))
            driver.quit()
        except Exception as e:
            self.logger.error("使用Selenium收集URL时出错: %s" % str(e))
        finally:
            return self.data

    def is_useful(self, url, title):
        # 检查基础条件
        if not url:
            return False
        if not title:
            return False
        # 过滤简单url
        if len(url[len("https://"):].split('/')) < 3:
            return False
        # 过滤掉长度过短的标题或文本
        if len(title) < 5:
            return False
            
        # 过滤掉明显是导航性质的链接
        # 包含特定关键词的导航链接
        nav_keywords = [
            "英文", "西班牙语", "移动应用", "Apps", "ENGLISH", "ESPAÑOL",
            "导航", "更多", "查看", "浏览", "首页", "主页", "首页",
            "comments", "评论", "分享", "收藏", "点赞", "喜欢",
            "app", "下载", "注册", "登录", "关注", "订阅",
            "关于我们", "联系我们", "隐私政策", "服务条款", "版权声明",
            "广告", "推广", "商务合作", "招聘信息", "帮助中心"
        ]
        
        # 检查链接文本或标题是否包含导航关键词
        full_text = title.lower()
        for keyword in nav_keywords:
            if keyword in full_text:
                return False
                
        # 过滤特定的无意义模式
        if title and title.endswith("|"):
            return False

        # 检查链接文本或标题是否包含URL关键词
        url_useless_keywords = [
            "slideshow", "video"
        ]
        for keyword in url_useless_keywords:
            if keyword in url:
                return False
            
        # 过滤掉JavaScript链接
        if url.startswith("javascript:"):
            return False
            
        # 过滤掉锚点链接（页面内跳转）
        if url.startswith("#"):
            return False
            
        # 过滤掉邮件链接
        if url.startswith("mailto:"):
            return False
            
        return True

    def get_content(self, driver, url):
        """
        获取网页正文的文字内容
        
        Args:
            driver: WebDriver实例
            url: 网页URL
            
        Returns:
            str: 网页正文内容
        """
        content = ""
        try:
            # 保存当前窗口句柄
            original_window = driver.current_window_handle
            
            # 在新标签页中打开链接
            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[1])
            driver.get(url)
            
            # 等待页面加载
            time.sleep(5)
            
            # 尝试获取页面主要内容
            content_selectors = [
                "article", 
                ".content", 
                ".article-content",
                ".post-content",
                ".entry-content",
                ".article-body",
                ".post-body",
                ".story-body",
                ".news-content",
                ".post-article",
                "main",
                ".main-content"
            ]
            
            content_element = None
            for selector in content_selectors:
                try:
                    content_element = driver.find_element(By.CSS_SELECTOR, selector)
                    if content_element and content_element.text.strip():
                        content = content_element.text.strip()
                        break
                except:
                    continue
            
            # 如果通过常见选择器未找到内容，尝试查找包含文章内容的其他元素
            if not content:
                # 尝试查找段落元素
                try:
                    paragraphs = driver.find_elements(By.TAG_NAME, "p")
                    if paragraphs:
                        # 收集所有段落文本
                        paragraph_texts = [p.text.strip() for p in paragraphs if p.text.strip()]
                        # 过滤掉太短的段落（可能是导航链接等）
                        long_paragraphs = [text for text in paragraph_texts if len(text) > 20]
                        if long_paragraphs:
                            content = "\n".join(long_paragraphs[:10])  # 只取前10段，避免内容过长
                except:
                    pass
            
            # 关闭当前标签页并切换回原始窗口
            driver.close()
            driver.switch_to.window(original_window)
            
        except Exception as e:
            self.logger.error(f"获取页面内容时出错: {str(e)}")
            # 确保无论如何都回到原始窗口
            try:
                if len(driver.window_handles) > 1:
                    driver.close()
                    driver.switch_to.window(original_window)
            except:
                pass
        
        return content[:10000]  # 限制内容长度，避免过长
