import argparse
import datetime
import json
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from util.store_util import Record, StoreUtil
from util.logger import get_logger
from ollama import ChatResponse
from ollama import chat

TYPES = set(["时政", "财经", "科技", "AI", "智驾"])

logger = get_logger("display.log")
store_util = None


def display(records: list, summary: list=None, output_type="html"):
    if output_type == "html":
        from util.html_util import generate_html_report
        generate_html_report(records, "report.html", summary)

    return


def summary_by_ai(records: list) -> str:
    logger.info("======================= 开始生成报告 =======================")
    
    # 如果没有记录，直接返回空字符串
    if not records:
        logger.info("没有记录可供分析")
        return ""
    
    # 构造提供给AI的记录信息
    record_info = ""
    for i, record in enumerate(records[:20]):  # 限制在前20条记录以避免token超限
        record_info += f"{i+1}. 标题: {record.title}\n"
        record_info += f"   类型: {record.type}\n"
        record_info += f"   内容摘要: {record.content}\n"
    
    # 构造提示词
    prompt = f"""
    你是一个专业的新闻分析师，请根据以下新闻记录分析并总结合并出当前的热点话题和趋势 3-5条。请直接以列表的形式输出结果，不要包含任何分析过程或解释性文字，只输出最终的热点总结。

    新闻记录:
    {record_info}

    并以json格式返回，格式如下：
        "topic": [
            "热点话题1（20字以内）：内容概要（100字以内）",
            "热点话题2：内容概要",
            ...
        ]
    ...
    """
    
    try:
        response: ChatResponse = chat(model='qwen3:8b', messages=[
            {
                'role': 'user',
                'content': prompt,
            }], 
            format="json"
        )
        
        summary = json.loads(response['message']['content']).get("topic")
        logger.info("AI生成的总结:")
        logger.info(summary)
        return summary
    except Exception as e:
        logger.error(f"AI总结生成失败: {e}")
        return "无法生成AI总结"


def get_record_list(start_time: datetime, end_time: datetime, type):
    logger.info("======================= 开始查询 =======================")
    logger.info(f"开始时间：{start_time.date()}")
    logger.info(f"结束时间：{end_time.date()}")
    logger.info(f"类型：{type}")

    result = store_util.get_records(start_time, end_time, type)
    logger.info("======================= 查询结果 =======================")
    logger.info(f"查询到 {len(result)} 条记录")
    return result


def parse_args():
    parser = argparse.ArgumentParser(description='数据收集程序')
    parser.add_argument('--dur_mode', '-d', help='时间模式：nd/nw')
    parser.add_argument('--start_time', '-s', help='开始时间')
    parser.add_argument('--end_time', '-e', help='结束时间')
    parser.add_argument('--type', '-t', help='类型')
    parser.add_argument('--mode', '-m', help='模式：展示模式/AI报告模式（默认展示模式）')
    parser.add_argument('--config', '-c', help='配置文件路径')
    return parser.parse_args()


def main():
    try:
        args = parse_args()
        start_time = datetime.datetime.today()
        end_time = datetime.datetime.today()
        if args.dur_mode:
            if args.dur_mode[-1] == 'd':
                n = int(args.dur_mode[:-1])
                start_time = start_time - datetime.timedelta(days=n)
            elif args.dur_mode[-1] == 'w':
                n = int(args.dur_mode[:-1])
                start_time = start_time - datetime.timedelta(weeks=n)
            else:
                logger.error("时间模式错误，使用nd/nw")
                return
        elif args.start_time and args.end_time:
            start_time = datetime.datetime.strptime(
                args.start_time, '%Y-%m-%d')
            end_time = datetime.datetime.strptime(args.end_time, '%Y-%m-%d')
        else:
            logger.error("请输入时间参数")
            return

        type = TYPES
        if args.type:
            type &= set(x.strip() for x in args.type.split(','))

        if args.config:
            with open(args.config, encoding='utf-8') as f:
                config = json.load(f)
                global store_util
                store_util = StoreUtil(config.get('storage'))
        else:
            logger.error("请输入配置文件路径")
            return

        records = get_record_list(start_time, end_time, type)
        summary = None
        if args.mode and args.mode == 'ai':
            summary = summary_by_ai(records)
        display(records, summary)
    except Exception as e:
        logger.error(e)


if __name__ == '__main__':
    main()
