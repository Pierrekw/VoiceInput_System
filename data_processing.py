import re
import logging
import cn2an  # 需要安装: pip install cn2an

# 基础配置
logging.basicConfig(
    level=logging.INFO, # 设置希望捕获的最低日志级别
    format='%(asctime)s - %(levelname)s - %(message)s', # 定义输出格式
    datefmt='%Y-%m-%d %H:%M:%S' # 定义时间格式（如果格式中使用了 %(asctime)s）
)


class DataProcessor:
    def __init__(self):
        # 数字映射字典
        self.digit_map = {
            '零': 0, '一': 1, '二': 2, '三': 3, '四': 4,
            '五': 5, '六': 6, '七': 7, '八': 8, '九': 9,
            '十': 10, '百': 100, '千': 1000, '万': 10000,
            '点': '.', '两': 2
        }
    
    def extract_data_pairs(self, text):
        """
        从文本中提取数据对（如：1号12.5）
        返回: 列表，每个元素为 (编号, 数值) 元组
        """
        # 匹配模式：数字+号+数字（可能包含中文数字和小数点）
        pattern = r'(\d+)\s*[号]?\s*([零一二两三四五六七八九十百千万点.]+)'
        matches = re.findall(pattern, text)
        
        data_pairs = []
        for match in matches:
            number_id = match[0]  # 编号
            value_str = match[1]   # 数值字符串（可能包含中文）
            
            # 转换中文数字到阿拉伯数字
            arabic_value = self.chinese_to_arabic(value_str)
            if arabic_value is not None:
                data_pairs.append((number_id, arabic_value))
                logging.info(f"提取数据对: 编号{number_id}, 值{arabic_value}")
        
        return data_pairs
    
    def chinese_to_arabic(self, value_input):
        """将中文数字字符串转换为阿拉伯数字"""
        
        # 首先检查输入是否已经是数字（整数或浮点数）
        if isinstance(value_input, (int, float)):
            logging.info(f"输入已是数字，直接返回: {value_input}")
            return value_input
        
        # 如果输入是字符串，才进行转换逻辑
        value_str = value_input
                        
        try:
            # 使用cn2an库进行转换（更准确）
            if any(char in value_str for char in '零一二三四五六七八九十百千万点'):
                arabic_value = cn2an.cn2an(value_str, 'normal')
                logging.info(f"转换成功: {value_str} -> {arabic_value}")
                return arabic_value
            else:
                # 已经是阿拉伯数字或浮点数
                return float(value_str)
        except Exception as e:
            logging.error(f"数字转换失败 '{value_str}': {e}")
            # 尝试简单转换
            try:
                return float(value_str)
            except ValueError:
                return None
    
    def parse_measurement_data(self, text):
        """
        解析测量数据文本
        支持多种格式: 
        - "1号12.5" 
        - "1号十二点五"
        - "1号,12.5"
        """
        # 多种分隔符支持
        patterns = [
            r'(\d+)\s*[号]?\s*[:：]?\s*([\d.零一二两三四五六七八九十百千万点]+)',
            r'(\d+)\s*[,，]\s*([\d.零一二两三四五六七八九十百千万点]+)'
        ]
        
        all_pairs = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                number_id, value_str = match
                arabic_value = self.chinese_to_arabic(value_str)
                if arabic_value is not None:
                    all_pairs.append((number_id, arabic_value))
        
        return all_pairs
        
 
        # **模块自查代码：单独运行此文件时执行以下测试**
if __name__ == '__main__':
    # 创建 DataProcessor 类的实例
    processor = DataProcessor()
    
    # 测试提取功能 - 现在通过实例调用方法
    test_text = "1号十二点五，2号三点一四"
    pairs = processor.extract_data_pairs(test_text)  # 使用 processor. 调用方法
    print("提取的数据对:", pairs)
    
    # 测试转换功能 - 同样通过实例调用方法
    for id, value in pairs:
        converted_value = processor.chinese_to_arabic(value)  # 使用 processor. 调用方法
        print(f"编号{id}, 原始值: {value}, 转换后: {converted_value}")