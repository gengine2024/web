from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime
import threading
import time
import whaletv_logger

# 初始化Flask应用
app = Flask(__name__)
# 2. 启用CORS（允许所有域名访问）
CORS(app)

# 本地JSON文件路径
DATA_FILE = "data.json"

logger = whaletv_logger.get_logger()

# 内存中的数据
in_memory_data = None
# 用于线程安全的锁
data_lock = threading.Lock()
# 标记数据是否发生变化
data_modified = False


def init_data_file():
    """ 初始化数据文件（如果不存在则创建默认数据） """
    logger.debug("init_data_file called")

    if not os.path.exists(DATA_FILE):
        # 获取当前时间并格式化为 "年-月-日 时:分:秒" 格式
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        default_data = {
            "title": "clipboard",
            "time": current_time,
            "data": []
        }

        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, ensure_ascii=False, indent=2)

        logger.info(f"初始化数据文件: {DATA_FILE}")


# 定时同步内存中的数据到文件
def sync_data_to_file():
    """ 定时将内存中的数据写入本地JSON文件（仅在数据变化时） """
    global in_memory_data, data_modified
    while True:
        if data_modified:
            logger.debug("sync_data_to_file: Writing data to file...")
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(in_memory_data, f, ensure_ascii=False, indent=2)
            logger.info("Data successfully written to file.")
            # 重置修改标记
            data_modified = False
        time.sleep(60)  # 每60秒检查一次


# 读取内存数据
def read_json_data():
    """ 读取内存数据 """
    global in_memory_data
    with data_lock:
        return in_memory_data if in_memory_data else {}


# 更新内存数据
def write_json_data(data):
    """ 更新内存中的数据并设置数据已修改标记 """
    global in_memory_data, data_modified
    with data_lock:
        in_memory_data = data
        data_modified = True  # 数据发生变化，设置标记


@app.route('/api/json', methods=['GET'])
def get_json():
    """ API接口：获取JSON数据（GET请求） """
    logger.error(f"get_json called with method: {request.method}")

    data = read_json_data()
    if not data:
        return jsonify({
            "code": "1001",
            "msg": "读取文件失败"
        }), 500

    return jsonify(data), 200


@app.route('/api/json', methods=['POST', 'PUT'])
def update_json():
    """ API接口：更新JSON数据（POST/PUT请求） """
    logger.info(f"update_json called with method: {request.method}")

    # 检查请求数据是否为JSON格式
    if not request.is_json:
        return jsonify({
            "code": "2003",
            "msg": "数据更新失败，传入内容非json结构"
        }), 400

    # 获取请求中的JSON数据
    update_data = request.get_json()
    # 读取当前数据
    current_data = read_json_data()
    if not current_data:
        return jsonify({
            "code": "2002",
            "msg": "数据更新失败，读取文件失败"
        }), 500

    # 根据请求方法处理更新：
    # PUT：全量更新（替换整个JSON）
    # POST：部分更新（只更新提供的字段，不改变其他字段）
    if request.method == 'PUT':
        # 全量更新：直接使用请求数据替换
        new_data = update_data
    else:  # POST
        # 部分更新：递归合并字典（支持嵌套结构）
        def merge_dict(target, source):
            for key, value in source.items():
                if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                    merge_dict(target[key], value)
                else:
                    target[key] = value
            return target

        new_data = merge_dict(current_data, update_data)

    # 更新内存中的数据
    write_json_data(new_data)

    return jsonify({
        "code": "0",
        "msg": "数据更新成功"
    }), 200


# 健康检查接口
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "JsonStorageService",
        "version": "1.0.0"
    }), 200


def main():
    """ main Enter """
    logger.info(f"=============================== Start Json DB Service ===============================")

    # 初始化数据文件并加载数据到内存
    init_data_file()
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        global in_memory_data
        in_memory_data = json.load(f)

    # 启动定时同步任务
    threading.Thread(target=sync_data_to_file, daemon=True).start()

    # 运行服务（默认端口5000，支持外部访问）
    app.run(host='0.0.0.0', port=5000, debug=False)


# 主函数
if __name__ == '__main__':
    main()
