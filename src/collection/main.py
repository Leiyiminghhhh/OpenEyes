import time
import argparse
import json
import asyncio
from datetime import datetime
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from collection.crawler_main_page import MainPageCrawler, MainPageCrawlerConfig
from collection.crawler_record import RecordCrawler, RecordCrawlerConfig
from util.logger import get_logger
from util.store_util import Record, StoreUtil

RETRY_TIMES = 3
MAX_URL_NUM = 50

logger = get_logger("collection.log")


class CollectionImpl(object):
    store_util = None
    crawler_configs = []

    def __init__(self, config_file_path=None):
        logger.info(
            "--------------------------- 配置信息 --------------------------")
        logger.info("日期：%s" % time.strftime("%Y-%m-%d", time.localtime()))
        logger.info("配置文件：%s" % config_file_path)
        self.config = None
        with open(config_file_path, 'r', encoding='utf-8') as f:
            config_str = f.read()
            self.config = json.loads(config_str)
            logger.info("文件内容：\n%s" % config_str)

        self.store_util = StoreUtil(self.config.get("storage"))
        self.store_util.PrintStoreConfig()
        for idx, crawl_config in enumerate(self.config.get("crawls")):
            logger.info("%d crawl：%s" % (idx, crawl_config))
            main_page_config = MainPageCrawlerConfig(**crawl_config)
            self.crawler_configs.append(main_page_config)

    def Run(self):
        url_status = {}
        for main_page_config in self.crawler_configs:
            for idx in range(RETRY_TIMES):
                try:
                    # 主页
                    logger.info(f"------ 从主页获取URL({idx}) ------")
                    logger.info(main_page_config)
                    main_page_crawler = MainPageCrawler(main_page_config)
                    result = json.loads(asyncio.run(main_page_crawler.Run()))
                    logger.info(
                        f">>>>>>>>>>>>>>>>>>> 主页收集到 {len(result)} 个页面：")
                    for item in result:
                        logger.info("{%s -> %s}" %
                                    (item.get("title"), item.get("url")))

                    # 文章
                    logger.info("------ 从URL获取文章 ------")
                    urls = self.__filter_urls(result)
                    logger.info(f">>>>>>>>>>>>>>>>>>> 获取 {len(urls)} 个URL")

                    crawler_config = RecordCrawlerConfig(urls)
                    record_crawler = RecordCrawler(crawler_config)
                    crawl_result = record_crawler.Run()
                    logger.info(
                        f">>>>>>>>>>>>>>>>>>> 收集到 {len(crawl_result)} 篇文章：\n {crawl_result}")

                    success_num, failed_num = self.__convert_and_store(
                        crawl_result, main_page_config)
                    logger.info(">>>>>>>>>>>>>>>>>>> 存储 %d 条数据成功, %d 条失败" %
                                (success_num, failed_num))
                    url_status[main_page_config.source] = (
                        True, len(result), len(crawl_result), success_num)
                except Exception as e:
                    logger.error("主程序运行异常：%s" % str(e))
                    continue
                if main_page_config.source in url_status:
                    break
            if main_page_config.source not in url_status:
                url_status[main_page_config.source] = False

        return url_status

    def __filter_urls(self, result):
        seen_urls = set()
        urls = []
        idx = 0
        for item in result:
            url = item.get("url")
            if url not in seen_urls:
                seen_urls.add(url)
                if not self.store_util.judge_url_contains(url):
                    urls.append(url)
                    idx += 1
                    if idx >= MAX_URL_NUM:
                        break
        return urls

    def __convert_and_store(self, results, config):
        logger.info("------ 转换存储数据 ------")
        store_list = []
        for url in results:
            item = results[url]
            data = ""
            article_time = ""
            try:
                data = json.loads(item)[0]
                article_time = datetime.strptime(data.get("time"), "%Y-%m-%d")
            except ValueError as e:
                logger.error("时间转换失败：%s %s %s" % (str(e), url, item))
                article_time = datetime.today()
            except Exception as e:
                logger.error("转换数据失败：%s %s %s" % (str(e), url, item))
                continue

            record = Record(
                content=data.get("content"),
                tags=data.get("tags"),
                time=article_time,
                title=data.get("title"),
                type=config.type,
                source=config.source,
                url=url)
            store_list.append(record)
        ans = self.store_util.save_records(store_list)
        return ans.get("success"), ans.get("failed")


def parse_args():
    parser = argparse.ArgumentParser(description='数据收集程序')
    parser.add_argument('--config', '-c', help='配置文件路径')
    return parser.parse_args()


def main():
    args = parse_args()

    logger.info(
        "================================ 初始化 ================================")
    impl = CollectionImpl(args.config)

    logger.info(
        "================================ 开始收集 ================================")
    url_status = impl.Run()

    for source, status in url_status.items():
        if status is False:
            logger.info("%s\t❌" % source)
        else:
            logger.info("%s:\t%d -> %d -> %d\t✅" %
                        (source, status[1], status[2], status[3]))

    logger.info(
        "================================ 完成任务，爬虫结束 ================================")


if __name__ == '__main__':
    main()
