import os
import sys
import logging
import platform
from datetime import datetime
from logging.handlers import RotatingFileHandler
import re


# 控制台日志颜色格式
LOG_COLORS = {
    # 'DEBUG': '\033[94m',  # 蓝色
    'INFO': '\033[92m',     # 绿色
    'WARNING': '\033[93m',  # 黄色
    'ERROR': '\033[91m',    # 红色
    'CRITICAL': '\033[95m'  # 紫色
}

# 前景颜色代码
BLACK = "\033[30m"      # 黑色
RED = "\033[31m"        # 红色
GREEN = "\033[32m"      # 绿色
YELLOW = "\033[33m"     # 黄色
BLUE = "\033[34m"       # 蓝色
MAGENTA = "\033[35m"    # 品红（紫红色）
CYAN = "\033[36m"       # 青色
WHITE = "\033[37m"      # 白色

RESET_COLOR = '\033[0m'  # 重置颜色


# 定义颜色码的正则表达式模式
color_code_pattern = re.compile(r'\033\[\d+m')


def is_win_and_win10_or_lower():
    """ 非Windows系统，或Win10或更低版本 """
    if platform.system() != "Windows":
        return False  # "不是Windows操作系统"

    version = platform.version()
    build_number = int(version.split('.')[2])

    if build_number < 22000:
        return True
    else:
        return False


def remove_color_codes(text):
    """ 移除颜色编码 """
    return color_code_pattern.sub('', text)


class ColoredFormatter(logging.Formatter):
    """自定义的彩色日志格式化器"""

    def __init__(self, fmt=None, datefmt=None, style='%', use_color=True):
        super().__init__(fmt, datefmt, style)
        self.use_color = use_color

    def format(self, record):
        log_message = super().format(record)

        if self.use_color:
            # 是windows且系统小于等于win10,格式化日志
            if is_win_and_win10_or_lower():
                if log_message.endswith(RESET_COLOR):
                    # 移除颜色字符串
                    log_message = remove_color_codes(log_message)
                    
                return log_message
            
            # 尾部已经包含了颜色时，直接返回
            if log_message.endswith(RESET_COLOR):
                return log_message
            else:
                color = LOG_COLORS.get(record.levelname, '')
                return f"{color}{log_message}{RESET_COLOR}"
        elif log_message.endswith(RESET_COLOR):
            # 未使用颜色时，移除颜色字符串
            log_message = remove_color_codes(log_message)

        return log_message


def create_log_dir():
    """创建日志目录"""
    parent_path = os.path.dirname(os.path.abspath(sys.argv[0]))  # 使用sys.argv[0]来获取当前执行文件的路径
    print(f"Error creating log directory: {sys.argv[0]}")
    print(f"Error creating log directory: {parent_path}")
    log_dir = os.path.join(parent_path, 'logs')
    try:
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        return log_dir
    except OSError as e:
        print(f"Error creating log directory: {e}")
        raise


def get_log_level():
    """从环境变量获取日志级别"""
    log_level = os.environ.get('WHALETV_LOG_LEVEL', 'DEBUG')
    return getattr(logging, log_level.upper(), logging.DEBUG)


def should_log_to_file():
    """检查是否需要输出日志到文件"""
    return os.environ.get('WHALETV_LOG_TO_FILE', 'true').lower() == 'true'


class WhaleLogger:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if WhaleLogger._initialized:
            return

        self.logger = None
        self.log_filename = None
        WhaleLogger._initialized = True

    def get_logger(self):
        """获取logger实例"""
        if self.logger is not None:
            return self.logger

        try:
            # 创建logger
            logger = logging.getLogger('WhaleTV')
            logger.setLevel(get_log_level())

            # 如果logger已经有handlers，清除它们
            if logger.handlers:
                logger.handlers.clear()

            # 创建控制台处理器
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(get_log_level())
            console_formatter = ColoredFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                                                 use_color=True)
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)

            # 根据环境变量决定是否添加文件处理器
            if should_log_to_file():
                # 创建日志目录
                log_dir = create_log_dir()

                # 设置日志文件名
                if self.log_filename is None:
                    self.log_filename = datetime.now().strftime("%Y-%m-%d") + '.log'
                log_path = os.path.join(log_dir, self.log_filename)

                # 文件处理器（带轮转）
                file_handler = RotatingFileHandler(
                    log_path,
                    maxBytes=10 * 1024 * 1024,  # 10MB
                    backupCount=5,
                    encoding='utf-8'
                )
                file_handler.setLevel(logging.DEBUG)
                file_formatter = ColoredFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                                                  use_color=False)
                file_handler.setFormatter(file_formatter)
                logger.addHandler(file_handler)

            self.logger = logger
            return logger

        except Exception as e:
            print(f"Error initializing logger: {e}")
            raise


def get_logger():
    """获取logger的便捷函数"""
    return WhaleLogger().get_logger()


def debug_blue(msg):
    """ 蓝色 """
    logging_debug_color(msg, BLUE)


def debug_magenta(msg):
    """ 品红(紫红色) """
    logging_debug_color(msg, MAGENTA)


def debug_cyan(msg):
    """ 青色 """
    logging_debug_color(msg, CYAN)


def logging_debug_color(msg, color):
    """ 自定义颜色 """
    get_logger().debug(f"{color}{msg}{RESET_COLOR}")

    # 用该方案会导致后一个debug方法也会被颜色
    # logger = get_logger()
    # for handler in logger.handlers:
    #     if isinstance(handler, RotatingFileHandler):
    #         handler.setFormatter(ColoredFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    #                                               use_color=False))
    #         handler.emit(logging.LogRecord(name=logger.name, level=logging.DEBUG, pathname=__file__, lineno=0,
    #                                        msg=msg, args=(), exc_info=None))
    #     elif isinstance(handler, logging.StreamHandler):
    #         # 控制台输出时，增加颜色格式
    #         fmt = f'{color}%(asctime)s - %(name)s - %(levelname)s - %(message)s{RESET_COLOR}'
    #         handler.setFormatter(ColoredFormatter(fmt, use_color=True))
    #         handler.emit(logging.LogRecord(name=logger.name, level=logging.DEBUG, pathname=__file__, lineno=0,
    #                                        msg=f"{msg}", args=(), exc_info=None))


def exception(ex, tag):
    """
    输出异常信息
    :param ex: 异常信息对象
    :param tag: 标识符，一般传入调用的方法名即可
    :return:
    """
    get_logger().error(f"\r\n【{tag}】 Exception message:\r\n  {ex}")


# test
# debug_blue("test")
# debug_cyan("test")
# debug_magenta("test")
#
# get_logger().debug("test")
# get_logger().info("test")
# get_logger().warning("test")
# get_logger().error("test")
