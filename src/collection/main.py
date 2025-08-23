import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import time
import argparse
import json
from concurrent.futures import ThreadPoolExecutor, as_completed


from util.store_util import StoreUtil
from util.logger import get_logger
from collection.collector import *


logger = get_logger("collection.log")


class CollectionImpl(object):
    def __init__(self, config_file_path=None):
        self.config_file_path = config_file_path
        self.date = time.strftime("%Y-%m-%d", time.localtime())
        self.collectors = []
        self.config = {}
        self.store_config = {}
        self.mode = "test"

        self.init(config_file_path)
        self.report_path = ""
        self.store_util = StoreUtil(self.store_config)

    def PrintConfig(self):
        logger.info(
            "--------------------------- 配置信息 --------------------------")
        logger.info("日期：%s" % self.date)
        logger.info("配置文件：%s" % self.config_file_path)
        logger.info("收集目标：")
        for collecter in self.collectors:
            logger.info("%s: %s", collecter.__class__.__name__, collecter)
        # logger.info("---------------------------- 存储配置 --------------------------")
        # logger.info(self.store_util)
        self.store_util.PrintStoreConfig()

    def Run(self):
        reports = {}
        # 使用线程池，最多同时运行5个线程
        with ThreadPoolExecutor(max_workers=5) as executor:
            # 提交所有任务到线程池
            future_to_collector = {
                executor.submit(self._run_collector, collecter): collecter
                for collecter in self.collectors
            }

            # 等待任务完成并收集结果
            for future in as_completed(future_to_collector):
                collecter = future_to_collector[future]
                try:
                    result = future.result()
                    collect_cnt, success_cnt = result
                    reports[collecter.source] = {
                        "total": collect_cnt,
                        "success": success_cnt
                    }
                    logger.info(f"收集器 {collecter.source} 完成任务，共收集 {collect_cnt} 条数据，成功存储 {success_cnt} 条")
                except Exception as e:
                    logger.error(f"收集器 {collecter.source} 执行出错: {str(e)}")

        return reports

    def _run_collector(self, collecter):
        """
        运行单个收集器的任务
        """
        data = collecter.Collect()
        collect_cnt = len(data)
        # 获取data的所有值（Record对象）
        records = list(data.values())
        result = self.store_util.save_records(records)
        success_cnt = result["success"]
        return collect_cnt, success_cnt

    def init(self, config_file):
        """
        读取配置文件，根据collectors的名称创建collector对象
        """
        if not config_file or not os.path.exists(config_file):
            logger.warning("配置文件不存在: %s" % config_file)
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except Exception as e:
            logger.error("读取配置文件失败: %s" % str(e))

        self.mode = self.config.get('mode', 'simple')
        collectors = self.config.get('collectors', [])

        for collector in collectors:
            try:
                interval = int(collector.get('interval', 1))
                dayinyear = datetime.datetime.now().timetuple().tm_yday
                if dayinyear % interval != 0: 
                    logger.info("跳过 %s(%d, %d)" % (collector.get('source'), dayinyear, interval))
                    continue
                name = collector.get('class_name')
                collector["mode"] = self.mode
                if name in globals():
                    collector_class = globals()[name]
                    collector_instance = collector_class(collector)
                    self.collectors.append(collector_instance)
                else:
                    logger.warning("未找到collector类: %s" % name)
            except Exception as e:
                source = collector.get("source")
                logger.error("创建collector失败: %s, 错误: %s" % (source, str(e)))

        self.store_config = self.config.get('storage', {})


def parse_args():
    parser = argparse.ArgumentParser(description='数据收集程序')
    parser.add_argument('--config', '-c', help='配置文件路径')
    return parser.parse_args()

def report(reports):
    return

def main():
    args = parse_args()

    logger.info(
        "================================ 初始化 ================================")
    impl = CollectionImpl(args.config)
    impl.PrintConfig()

    logger.info(
        "================================ 开始收集 ================================")

    reports = impl.Run()

    logger.info(
        "================================ 收集完成，汇总结果 ================================")

    for key in reports:
        logger.info("%s: %s" % (key, reports[key]))
    report(reports)

    logger.info(
        "================================ 完成任务，爬虫结束 ================================")


if __name__ == '__main__':
    main()
