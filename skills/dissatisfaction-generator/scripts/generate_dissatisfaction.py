import pandas as pd
import os
import re

def analyze_user_prompt(user_prompt):
    """分析用户提示词，提取关键信息"""
    keywords = []
    file_names = []
    function_names = []
    
    # 提取文件名
    file_pattern = r'([a-zA-Z0-9_]+\.(py|java|js|ts|tsx|vue|go|cpp|c|rb|php))'
    files = re.findall(file_pattern, user_prompt)
    for f, _ in files:
        if f not in file_names:
            file_names.append(f)
    
    # 提取函数/方法名
    func_pattern = r'(def\s+(\w+)|function\s+(\w+)|class\s+(\w+)|method\s+(\w+))'
    funcs = re.findall(func_pattern, user_prompt)
    for match in funcs:
        for item in match[1:]:
            if item and item not in function_names:
                function_names.append(item)
    
    # 识别关键词
    if any(word in user_prompt for word in ['bug', '修复', '错误', 'bugfix', 'fix']):
        keywords.append('bug修复')
    if any(word in user_prompt for word in ['功能', 'feature', '新增', '添加']):
        keywords.append('功能开发')
    if any(word in user_prompt for word in ['优化', 'optimize', '性能', 'performance']):
        keywords.append('性能优化')
    if any(word in user_prompt for word in ['测试', 'test', '单元测试', 'unit']):
        keywords.append('测试')
    if any(word in user_prompt for word in ['接口', 'API', 'api']):
        keywords.append('接口开发')
    if any(word in user_prompt for word in ['数据库', 'database', 'sql', 'mysql']):
        keywords.append('数据库操作')
    if any(word in user_prompt for word in ['前端', 'frontend', 'UI', '界面']):
        keywords.append('前端开发')
    if any(word in user_prompt for word in ['后端', 'backend', 'server']):
        keywords.append('后端开发')
    
    return {
        'file_names': file_names,
        'function_names': function_names,
        'keywords': keywords
    }

def analyze_log_trajectory(log_trajectory):
    """分析日志轨迹，提取关键信息"""
    analysis = {
        'steps': 0,
        'has_errors': False,
        'has_warnings': False,
        'has_completion': False,
        'length': len(log_trajectory),
        'actions': []
    }
    
    # 统计步骤数
    analysis['steps'] = log_trajectory.count('step') + log_trajectory.count('Step') + log_trajectory.count('步骤') + 5
    
    # 检测错误和警告
    if any(word in log_trajectory for word in ['error', 'Error', 'ERROR', '异常', '失败', '错误']):
        analysis['has_errors'] = True
    if any(word in log_trajectory for word in ['warning', 'Warning', 'WARNING', '警告']):
        analysis['has_warnings'] = True
    
    # 检测完成状态
    if any(word in log_trajectory for word in ['完成', 'success', 'Success', 'SUCCESS', 'done', 'Done']):
        analysis['has_completion'] = True
    
    # 识别动作类型
    if 'read' in log_trajectory.lower() or '读取' in log_trajectory:
        analysis['actions'].append('读取文件')
    if 'write' in log_trajectory.lower() or '写入' in log_trajectory or '创建' in log_trajectory:
        analysis['actions'].append('写入文件')
    if 'edit' in log_trajectory.lower() or '修改' in log_trajectory or '编辑' in log_trajectory:
        analysis['actions'].append('编辑文件')
    if 'run' in log_trajectory.lower() or '执行' in log_trajectory:
        analysis['actions'].append('执行命令')
    if 'test' in log_trajectory.lower() or '测试' in log_trajectory:
        analysis['actions'].append('运行测试')
    
    return analysis

def generate_product_dissatisfaction(prompt_analysis, log_analysis):
    """生成产物不满意描述"""
    file_names = prompt_analysis['file_names']
    function_names = prompt_analysis['function_names']
    keywords = prompt_analysis['keywords']
    
    # 如果没有具体的文件或函数名，使用通用描述
    target_file = file_names[0] if file_names else 'target_file.py'
    target_func = function_names[0] if function_names else 'target_function'
    
    issues = []
    
    # 根据关键词生成不同的不满意原因
    if 'bug修复' in keywords:
        issues.append(f"{target_file} 中的 {target_func} 方法，在处理特定场景时可能存在逻辑缺陷")
        issues.append("对比需求，修复效果可能未达到预期，部分边界场景处理不足")
        issues.append("属于部分场景优化失效")
    
    elif '功能开发' in keywords:
        issues.append(f"{target_file} 中的 {target_func} 函数，新增功能可能存在不完善之处")
        issues.append("对比需求，某些功能点可能未完全实现，影响业务流程")
        issues.append("属于拓展功能完善度不足")
    
    elif '性能优化' in keywords:
        issues.append(f"{target_file} 中的 {target_func} 方法，优化效果可能未达到预期")
        issues.append("对比需求，性能指标可能未达标，影响系统响应速度")
        issues.append("属于优化效果不足")
    
    elif '接口开发' in keywords:
        issues.append(f"{target_file} 中的 API 接口实现，可能存在参数校验不完整")
        issues.append("对比需求，接口功能可能不完善，影响数据交互流程")
        issues.append("属于功能不完善")
    
    else:
        issues.append(f"{target_file} 中的 {target_func} 逻辑，可能存在潜在问题")
        issues.append("对比需求，实现效果可能存在偏差")
        issues.append("属于边界场景轻微异常")
    
    # 根据日志长度添加评价
    if log_analysis['length'] < 50:
        issues.append("生成内容可能不够完整")
    elif log_analysis['length'] > 2000:
        issues.append("生成内容可能存在冗余")
    
    # 如果有错误，添加相关描述
    if log_analysis['has_errors']:
        issues.append("运行过程中存在异常信息，可能影响最终产物质量")
    
    return f"产物不满意：{'。'.join(issues)}"

def generate_process_dissatisfaction(prompt_analysis, log_analysis):
    """生成过程不满意描述"""
    keywords = prompt_analysis['keywords']
    actions = log_analysis['actions']
    
    scenarios = []
    
    # 根据分析结果生成过程不满意
    if 'bug修复' in keywords:
        scenarios.append({
            'when': '在修复 bug 之前',
            'what': '未充分分析问题根源，直接进行代码修改',
            'impact': '可能导致修复不彻底，需要后续返工',
            'root': '需求理解不够深入',
            'solution': '正确做法应先定位问题根因，再制定修复方案'
        })
    
    elif '功能开发' in keywords:
        scenarios.append({
            'when': '在规划任务清单后',
            'what': '未充分考虑功能的边界条件和异常情况',
            'impact': '导致生成的产物功能不完善，部分场景无法正常运行',
            'root': '任务规划不够细致',
            'solution': '正确做法应先梳理所有使用场景，再逐步实现'
        })
    
    elif '性能优化' in keywords:
        scenarios.append({
            'when': '在进行优化之前',
            'what': '未进行性能基准测试，缺乏优化前后的对比数据',
            'impact': '无法准确评估优化效果，可能存在优化不到位的情况',
            'root': '缺乏量化评估意识',
            'solution': '正确做法应先建立性能基准，再进行针对性优化'
        })
    
    else:
        scenarios.append({
            'when': '在执行任务过程中',
            'what': '推理过程可能不够精简，存在冗余步骤',
            'impact': '影响执行效率，可能导致产物质量不稳定',
            'root': '任务规划不够合理',
            'solution': '正确做法应先制定清晰的执行计划，再逐步推进'
        })
    
    # 根据日志分析添加更多场景
    if log_analysis['steps'] < 3:
        scenarios.append({
            'when': '在开始执行前',
            'what': '任务拆解不够细致，步骤过于简略',
            'impact': '可能遗漏关键环节，影响最终结果',
            'root': '任务规划不够充分',
            'solution': '正确做法应将任务拆分为多个明确的步骤'
        })
    
    if log_analysis['has_errors'] and not log_analysis['has_completion']:
        scenarios.append({
            'when': '在遇到错误后',
            'what': '未有效处理异常情况，未能完成任务',
            'impact': '导致任务中断，未能达到预期目标',
            'root': '异常处理能力不足',
            'solution': '正确做法应增加异常处理机制，确保任务可恢复'
        })
    
    # 构建过程不满意描述
    scenario = scenarios[0]
    result = f"过程不满意：{scenario['when']}，{scenario['what']}。{scenario['impact']}。根因在于{scenario['root']}，{scenario['solution']}。"
    
    return result

def generate_dissatisfaction(user_prompt, log_trajectory):
    """
    根据 User Prompt 和日志轨迹生成产物不满意和过程不满意原因
    如果 User Prompt 或日志轨迹为空，返回 None
    """
    if pd.isna(user_prompt) or pd.isna(log_trajectory):
        return None
    
    user_prompt = str(user_prompt).strip()
    log_trajectory = str(log_trajectory).strip()
    
    if not user_prompt or not log_trajectory:
        return None
    
    # 分析用户提示词和日志轨迹
    prompt_analysis = analyze_user_prompt(user_prompt)
    log_analysis = analyze_log_trajectory(log_trajectory)
    
    # 生成不满意原因
    product_dissatisfaction = generate_product_dissatisfaction(prompt_analysis, log_analysis)
    process_dissatisfaction = generate_process_dissatisfaction(prompt_analysis, log_analysis)
    
    return f"{product_dissatisfaction}\n\n{process_dissatisfaction}"

def main():
    input_file = r"e:\claudeCoding\data.xlsx"
    output_file = r"e:\claudeCoding\data.xlsx"
    
    if not os.path.exists(input_file):
        print(f"错误：文件 {input_file} 不存在")
        return
    
    try:
        df = pd.read_excel(input_file)
        
        if '不满意原因' not in df.columns:
            df['不满意原因'] = ""
        
        processed_count = 0
        skipped_count = 0
        
        for index, row in df.iterrows():
            user_prompt = row.get('User Prompt', "")
            log_trajectory = row.get('日志轨迹', "")
            
            dissatisfaction = generate_dissatisfaction(user_prompt, log_trajectory)
            
            if dissatisfaction is not None:
                df.at[index, '不满意原因'] = dissatisfaction
                processed_count += 1
            else:
                skipped_count += 1
            
            if (index + 1) % 10 == 0:
                print(f"已处理 {index + 1} 行数据")
        
        df.to_excel(output_file, index=False)
        print(f"处理完成！共处理 {processed_count} 行数据，跳过 {skipped_count} 行（缺少必要输入数据），结果已保存到 {output_file}")
    
    except Exception as e:
        print(f"处理过程中发生错误：{str(e)}")

if __name__ == "__main__":
    main()
