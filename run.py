# -*- coding: utf-8 -*-
import pytest
import os
import sys
import subprocess
import time
import shutil
from config.config_loader import get_env_value, get_env_now
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from setup_paths import init_paths
init_paths()

# 导入并发执行模块
from common.concurrent_executor import (
    FileSelector, 
    ConcurrentExecutor, 
    ReportAggregator,
    LogMerger
)

current_dir = os.path.dirname(os.path.abspath(__file__))
def run_tests():
    """生成Allure报告"""
    print("📊 生成Allure测试报告...")
    
    # 从配置中获取相对路径，然后拼接为绝对路径
    AllureReport = os.path.join(current_dir, get_env_value('test_report_dir'))
    AllureResult = os.path.join(current_dir, get_env_value('test_result_dir'))
    Screenshot = os.path.join(current_dir, get_env_value('test_screenshot_dir'))
    
    # 确保目录存在
    os.makedirs(AllureReport, exist_ok=True)
    os.makedirs(AllureResult, exist_ok=True)
    os.makedirs(Screenshot, exist_ok=True)
    
    print(f"   📁 报告目录: {AllureReport}")
    print(f"   📁 结果目录: {AllureResult}")

    print("📋 开始执行pytest测试用例...")
    
    # 测试文件路径
    test_file = os.path.join(current_dir, 'test_case', 'test_case.py')
    
    print(f"   📄 测试文件: {test_file}")
    
    test_result = pytest.main([test_file, '-s', '-q', '--clean-alluredir', f'--alluredir={AllureResult}'])
    try:
        cmd = f'allure generate {AllureResult} -o {AllureReport} --clean'
        result = os.system(cmd)
        setup_chinese_interface()
        if result == 0:
            print("✅ Allure 报告生成成功!")
            print(f"📁 报告位置: {AllureReport}")
            
            # 尝试打开报告
           
            try:
                choice = input("\n是否打开报告? (y/n): ").lower().strip()
                if choice in ['y', 'yes', '是']:
                    cmd = f'allure open {AllureReport}'
                    result = os.system(cmd)
            except KeyboardInterrupt:
                print("\n用户取消操作")
           
        else:
            print("❌ Allure 报告生成失败!")
            print("请确保已安装 Allure 命令行工具")
            
    except Exception as e:
        print(f"❌ 生成报告时出错: {e}")

    return test_result

def setup_chinese_interface():
    """设置中文界面"""
    print("🌏 设置Allure报告为中文界面...")
    try:
        # 获取当前脚本所在目录
        AllureReport = os.path.join(current_dir, get_env_value('test_report_dir'))
        
        from tools.allure_setting_zh_cn import main
        main(report_dir=AllureReport)
        return True
    except Exception as e:
        print(f"⚠️  中文化设置失败: {e}")
        return False

def open_report():
    """打开报告"""
    print("🌐 准备打开测试报告...")
    
    # 获取当前脚本所在目录
    AllureReport = os.path.join(current_dir, get_env_value('test_report_dir'))
    AllureResult = os.path.join(current_dir, get_env_value('test_result_dir'))
    cmd = f'allure generate {AllureResult} -o {AllureReport} --clean'
    result = os.system(cmd)
    setup_chinese_interface()
    if result == 0:
        print("✅ Allure 报告生成成功!")
        print(f"📁 报告位置: {AllureReport}")
        cmd = f'allure open {AllureReport}'
        result = os.system(cmd)

def run_concurrent_tests():
    """🚀 并发执行测试的主入口"""
    
    print("\n" + "="*60)
    print("🚀 接口自动化测试 - 并发执行模式")
    print("="*60)
    
    # 1. 获取当前环境
    env = get_env_now()
    print(f"\n🌍 当前环境: {env}")
    
    # 2. 文件选择
    selector = FileSelector(env)
    selected_files = selector.interactive_select()
    
    if not selected_files:
        print("\n❌ 未选择任何文件，退出执行")
        return
    
    print(f"\n✅ 已选择 {len(selected_files)} 个文件:")
    for idx, f in enumerate(selected_files, 1):
        print(f"   {idx}. {f.name}")
    
    # 3. 并发设置
    default_workers = os.cpu_count()
    print(f"\n⚙️  并发设置:")
    print(f"   💡 系统 CPU 核心数: {default_workers}")
    print(f"   💡 推荐并发数: {min(default_workers, len(selected_files))}")
    
    max_workers_input = input(f"   请输入并发数 (直接回车使用推荐值): ").strip()
    
    if max_workers_input:
        try:
            max_workers = int(max_workers_input)
            if max_workers < 1:
                print("   ⚠️  并发数至少为 1，使用默认值")
                max_workers = min(default_workers, len(selected_files))
            elif max_workers > default_workers * 2:
                print(f"   ⚠️  并发数过大，建议不超过 {default_workers * 2}，使用默认值")
                max_workers = min(default_workers, len(selected_files))
        except ValueError:
            print("   ⚠️  输入无效，使用默认值")
            max_workers = min(default_workers, len(selected_files))
    else:
        max_workers = min(default_workers, len(selected_files))
    
    # 4. 执行确认
    print("\n" + "="*60)
    print("📋 执行计划:")
    print("="*60)
    print(f"   📦 测试文件: {len(selected_files)} 个")
    print(f"   ⚙️  并发数: {max_workers}")
    print(f"   🌍 环境: {env}")
    
    
    confirm = input("\n是否开始执行? (y/n): ").lower().strip()
    if confirm not in ['y', 'yes', '是']:
        print("❌ 用户取消执行")
        return
    
    # 5. 开始并发执行
    print("\n" + "="*60)
    print("开始并发执行测试用例...")
    print("="*60)
    
    executor = ConcurrentExecutor(max_workers=max_workers, current_dir=current_dir)
    execution_results = executor.execute_concurrent(selected_files)
    
    # 6. 报告聚合
    print("\n" + "="*60)
    print("📊 生成测试报告")
    print("="*60)
    
    # 获取报告和结果目录
    AllureReport = os.path.join(current_dir, get_env_value('test_report_dir'))
    result_dirs = [r['result_dir'] for r in execution_results]
    
    aggregator = ReportAggregator(
        report_dir=AllureReport,
        results_dirs=result_dirs
    )
    
    # 合并测试结果
    if aggregator.merge_results():
        # 生成报告
        if aggregator.generate_report():
            # 中文化
            setup_chinese_interface()
    
    # 生成执行摘要
    aggregator.generate_summary(execution_results)
    
    # 7. 合并日志
    log_dir = Path(current_dir) / 'log'
    print(log_dir)
    merged_log_file = log_dir / f'log.merged.{time.strftime("%Y-%m-%d_%H-%M-%S")}'
    LogMerger.merge_logs(log_dir, merged_log_file)
    
    # 8. 清理临时文件
    print("\n🧹 清理临时文件...")
    temp_results_dir = Path(current_dir) / 'TestReport' / 'temp_results'
    if temp_results_dir.exists():
        try:
            shutil.rmtree(temp_results_dir)
            print("   ✅ 临时文件清理完成")
        except Exception as e:
            print(f"   ⚠️  清理临时文件失败: {e}")
    
    # 清理 worker 日志文件（可选，如果需要保留可以注释掉）
    if log_dir.exists():
        worker_logs = list(log_dir.glob('log.worker_*'))
        if worker_logs:
            try:
                for log_file in worker_logs:
                    log_file.unlink()
                print(f"   ✅ 已清理 {len(worker_logs)} 个 worker 日志文件")
            except Exception as e:
                print(f"   ⚠️  清理 worker 日志失败: {e}")
    
    # 9. 打开报告
    print("\n" + "="*60)
    choice = input("是否打开报告? (y/n): ").lower().strip()
    if choice in ['y', 'yes', '是']:
        open_report()
    
    print("\n" + "="*60)
    print("✅ 并发执行完成!")
    print("="*60 + "\n")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🤖 接口自动化测试执行器")
    print("="*60)
    
    # 选择执行模式
    print("\n执行模式:")
    print("  [1] 标准模式 (串行执行，使用配置文件中的测试数据)")
    print("  [2] 并发模式 (文件级并发，选择指定文件并发执行)")
    print("="*60)
    
    mode = input("\n请选择模式 (1/2，直接回车默认标准模式): ").strip()
    
    if mode == '2':
        run_concurrent_tests()
    else:
        if mode != '1' and mode != '':
            print("⚠️  输入无效，使用标准模式")
        run_tests()