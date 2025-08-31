import json
from util.logger import get_logger
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


logger = get_logger("store.log")

Base = declarative_base()


class Record(Base):
    __tablename__ = 'record'

    id = Column(Integer, primary_key=True, autoincrement=True)
    time = Column(DateTime)
    title = Column(String(255))
    source = Column(String(100))
    content = Column(Text)
    tags = Column(String(255))
    type = Column(String(50))
    url = Column(String(255))

    def __repr__(self):
        return "<Record(id='%s', time='%s', title='%s', source='%s', content len='%d', tags='%s', type='%s', url='%s')>" % (
            self.id, self.time, self.title, self.source, len(self.content), self.tags, self.type, self.url)

    def to_dict(self):
        return {
            'id': self.id,
            'time': self.time.strftime('%Y-%m-%d %H:%M:%S') if self.time else None,
            'title': self.title,
            'source': self.source,
            'content': self.content,
            'tags': self.tags,
            'type': self.type,
            'url': self.url
        }


class StoreUtil:
    def __init__(self, config=None):
        """
        初始化StoreUtil

        Args:
            config (dict): 数据库配置信息，包括host, port, username, password, database等
        """
        self.engine = None
        self.Session = None
        self.config = config or {}

        if config:
            self._init_database()

    def _init_database(self):
        """
        初始化数据库连接
        """
        try:
            host = self.config.get('host', 'localhost')
            port = self.config.get('port', 3306)
            username = self.config.get('username', 'root')
            password = self.config.get('password', '')
            database = self.config.get('database', 'openeyes')

            # 创建数据库引擎
            connection_string = f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}?charset=utf8mb4"
            self.engine = create_engine(connection_string, echo=False)

            # 创建Session类
            self.Session = sessionmaker(bind=self.engine)

            # 创建表
            Base.metadata.create_all(self.engine)

            logger.info("数据库连接初始化成功")
        except Exception as e:
            logger.error(f"数据库连接初始化失败: {str(e)}")

    def PrintStoreConfig(self):
        """
        打印存储配置信息
        """
        if self.config:
            logger.info("Store Config:")
            logger.info(f"  Host: {self.config.get('host', 'localhost')}")
            logger.info(f"  Port: {self.config.get('port', 3306)}")
            logger.info(
                f"  Database: {self.config.get('database', 'openeyes')}")
            logger.info(f"  Username: {self.config.get('username', 'root')}")
        else:
            logger.info("Store Config: 未配置")

    def save_records(self, records: list):
        """
        批量保存记录到数据库

        Args:
            records (list): 记录对象列表

        Returns:
            dict: 包含成功和失败数量的统计信息
        """
        if not self.Session:
            logger.error("数据库未初始化")
            return {"success": 0, "failed": len(records)}

        if not isinstance(records, list):
            logger.error("参数必须是记录对象列表")
            return {"success": 0, "failed": 0}

        # 过滤掉已存在的记录
        filtered_records = []
        fail_store_records = []
        for record in records:
            if self.judge_record_contains(record):
                fail_store_records.append(record)
            else:
                filtered_records.append(record)

        if not filtered_records:
            logger.info("没有需要保存的新记录")
            return {"success": 0, "failed": len(records)}

        try:
            session = self.Session()
            session.add_all(filtered_records)
            session.commit()
            success_count = len(filtered_records)
            logger.info("成功批量保存 %d 条记录 \n %s" % (success_count, json.dumps([v.to_dict() for v in filtered_records], ensure_ascii=False, indent=2)))
            failed_count = len(fail_store_records)
            logger.info("无需保存 %d 条记录 \n %s" % (failed_count, json.dumps([v.to_dict() for v in fail_store_records], ensure_ascii=False, indent=2)))
            session.close()
            return {"success": success_count, "failed": failed_count}
        except Exception as e:
            logger.error(f"批量保存记录失败: {str(e)}")
            session.rollback()
            session.close()
            return {"success": 0, "failed": len(records)}

    def save_record(self, record: Record):
        """
        保存记录到数据库

        Args:
            record_data (dict): 记录数据

        Returns:
            bool: 保存是否成功
        """
        if not self.Session:
            logger.error("数据库未初始化")
            return False

        if self.judge_record_contains(record):
            logger.warn(f"记录已存在： {record}")
            return False

        try:
            session = self.Session()
            session.add(record)
            session.commit()
            logger.info(f"记录保存成功: {record}")
            session.close()
            return True
        except Exception as e:
            logger.error(f"记录保存失败: {str(e)}")
            session.rollback()
            session.close()
            return False

    def judge_record_contains(self, record: Record) -> bool:
        """
        判断记录是否已存在
        :param record: 记录对象
        :return: True表示已存在，False表示不存在
        """
        try:
            session = self.Session()
            query = session.query(Record).filter(Record.url == record.url)
            exists = query.first() is not None
            if not exists:  # 只有当URL不存在时才检查标题
                query = session.query(Record).filter(Record.title == record.title)
                exists = query.first() is not None
            session.close()
            return exists
        except Exception as e:
            logger.error(f"判断记录是否存在失败: {str(e)}")
            return False

