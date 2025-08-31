import logging
import os
from datetime import datetime

# 存储已创建的logger实例
_loggers = {}

def get_logger(filename='app.log'):
    """
    获取logger实例
    
    Args:
        filename (str): 日志文件名，默认为'app.log'
        
    Returns:
        logging.Logger: 配置好的logger实例
    """
    if filename in _loggers:
        return _loggers[filename]
    
    # 创建logger实例
    logger_name = f'OpenEyes_{filename}' if filename != 'app.log' else 'OpenEyes'
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    
    # 避免重复添加处理器
    if not logger.handlers:
        # 创建带日期的目录结构
        today = datetime.now().strftime('%Y-%m-%d')
        log_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'logs', today)
        os.makedirs(log_dir, exist_ok=True)
        
        # 创建文件处理器
        log_file_path = os.path.join(log_dir, filename)
        if os.path.exists(log_file_path):
            os.remove(log_file_path)
        file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # 创建格式化器并添加到处理器
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        # 将处理器添加到logger
        logger.addHandler(file_handler)
    
    _loggers[filename] = logger
    return logger

# 默认logger实例，保持向后兼容性
logger = get_logger()