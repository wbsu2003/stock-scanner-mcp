from loguru import logger
import sys
import os
from datetime import datetime


# 创建日志目录
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(log_dir, exist_ok=True)

# 配置日志
logger.remove()  # 移除默认的处理器

# 添加标准输出处理器（控制台）
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO",   # 同时显示在控制台和写入到日志文件中
)

# 添加统一的日志文件处理器，按日期自动轮转
logger.add(
    os.path.join(log_dir, "stock_scanner_{time:YYYY-MM-DD}.log"),
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{line} - {message}",
    level="DEBUG",
    rotation="00:00",    # 每天午夜轮转
    retention="7 days",  # 保留7天的日志
    compression="zip",   # 压缩旧日志文件
    enqueue=True         # 使用队列写入，提高性能
)

# 添加错误日志文件处理器，专门记录错误信息
logger.add(
    os.path.join(log_dir, "error_{time:YYYY-MM-DD}.log"),
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{line} - {message}",
    level="ERROR",
    rotation="00:00",     # 每天午夜轮转
    retention="7 days",   # 保留7天的错误日志
    compression="zip",    # 压缩旧日志文件
    enqueue=True          # 使用队列写入，提高性能
)

def clean_old_logs(max_days=7):
    """清理超过指定天数的日志文件"""
    try:
        today = datetime.now()
        for filename in os.listdir(log_dir):
            file_path = os.path.join(log_dir, filename)
            # 跳过目录
            if os.path.isdir(file_path):
                continue
                
            # 检查文件修改时间
            file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            days_old = (today - file_time).days
            
            # 如果文件超过指定天数，删除它
            if days_old > max_days:
                os.remove(file_path)
                logger.info(f"已删除过期日志文件: {filename}")
    except Exception as e:
        logger.error(f"清理日志文件时出错: {e}")

def get_logger():
    """获取通用日志器"""
    # 启动时清理旧日志
    clean_old_logs()
    return logger
