# -*- coding: utf-8 -*-
"""
并发执行引擎 - 支持文件级并发执行测试用例
"""
import os
import sys
import time
import shutil
import subprocess
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Dict, Any
import json

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from setup_paths import init_paths
init_paths()


class FileSelector:
    """测试文件选择器"""
    
    def __init__(self, env: str):
        """
        初始化文件选择器
        :param env: 当前环境名称
        """
        self.env = env
        # 🔧 使用项目根目录路径，确保路径正确
        project_root = Path(__file__).parent.parent  # 回到 pytestApi 目录
        self.data_dir = project_root / 'data' / env
        
        # 检查数据目录是否存在
        if not self.data_dir.exists():
            print(f"⚠️  警告: 数据目录不存在 {self.data_dir}")
            print(f"    请确保在 data/ 目录下有 {env} 文件夹")
    
    def scan_files(self) -> List[Path]:
        """
        扫描可用的测试文件
        :return: 文件列表
        """
        if not self.data_dir.exists():
            return []
        
        files = list(self.data_dir.glob('*.xlsx'))
        # 过滤掉临时文件 (~$开头的文件) 和隐藏文件
        files = [f for f in files if not f.name.startswith('~$') and not f.name.startswith('.')]
        # 按文件名排序
        files.sort(key=lambda x: x.name)
        
        return files
    
    def _parse_selection(self, choice: str, files: List[Path]) -> List[Path]:
        """
        解析用户的选择输入
        支持格式：1,3,5-8,10
        """
        selected = []
        parts = choice.split(',')
        
        for part in parts:
            part = part.strip()
            if '-' in part:
                # 范围选择: 5-8
                try:
                    start, end = map(int, part.split('-'))
                    for i in range(start, end + 1):
                        if 1 <= i <= len(files):
                            selected.append(files[i - 1])
                except ValueError:
                    print(f"⚠️  忽略无效范围: {part}")
            else:
                # 单个选择: 3
                try:
                    idx = int(part)
                    if 1 <= idx <= len(files):
                        selected.append(files[idx - 1])
                    else:
                        print(f"⚠️  忽略超出范围的编号: {idx}")
                except ValueError:
                    print(f"⚠️  忽略无效输入: {part}")
        
        # 去重并保持顺序
        seen = set()
        result = []
        for f in selected:
            if f not in seen:
                seen.add(f)
                result.append(f)
        
        return result
    
    def _select_by_group(self, files: List[Path]) -> List[Path]:
        """按业务模块分组选择"""
        # 业务模块分组配置
        groups = {
            '用户管理': ['用户管理.xlsx'],
            '订单管理': ['订单管理.xlsx', '订单回收站.xlsx', '购物车管理.xlsx'],
            '商品管理': ['商品管理.xlsx', '通用商品.xlsx', '产品管理.xlsx'],
            '插件管理': [
                '插件管理及资源中心插件.xlsx', '优惠码插件.xlsx', 
                '实名插件.xlsx', '工单插件.xlsx', '提现插件.xlsx', '退款插件.xlsx'
            ],
            '系统管理': ['系统设置.xlsx', '管理员设置.xlsx', '上下游管理.xlsx'],
            '资源管理': ['弹性IP.xlsx', '磁盘.xlsx', 'DCIM.xlsx', '自定义云.xlsx'],
            '财务管理': ['发票.xlsx'],
            'API管理': ['API管理.xlsx'],
        }
        
        print("\n" + "="*60)
        print("📦 业务模块分组")
        print("="*60)
        
        # 只显示当前目录中存在的分组
        available_groups = {}
        for idx, (group_name, group_files) in enumerate(groups.items(), 1):
            # 检查这个分组是否有文件存在
            existing_files = [f for f in files if f.name in group_files]
            if existing_files:
                available_groups[idx] = (group_name, existing_files)
                print(f"  [{idx}] {group_name} ({len(existing_files)} 个文件)")
        
        if not available_groups:
            print("  暂无可用的业务模块分组")
            return []
        
        print("="*60)
        choice = input("\n请选择业务模块编号 (支持多选，如: 1,3,5): ").strip()
        
        if not choice:
            return []
        
        selected = []
        for part in choice.split(','):
            try:
                idx = int(part.strip())
                if idx in available_groups:
                    _, group_files = available_groups[idx]
                    selected.extend(group_files)
            except ValueError:
                print(f"⚠️  忽略无效输入: {part}")
        
        return selected
    
    def interactive_select(self) -> List[Path]:
        """
        交互式选择界面
        :return: 用户选择的文件列表
        """
        files = self.scan_files()
        
        if not files:
            print("❌ 未找到任何测试文件")
            return []
        
        print("\n" + "="*60)
        print(f"📂 可用测试文件列表 (环境: {self.env})")
        print("="*60)
        
        # 显示文件列表
        for idx, file in enumerate(files, 1):
            # 显示文件大小（可选）
            size_kb = file.stat().st_size / 1024
            print(f"  [{idx:2d}] {file.name:<45s} ({size_kb:.1f} KB)")
        
        print("\n" + "="*60)
        print("选择方式:")
        print("  1. 输入文件编号 (例如: 1,3,5-8)")
        print("  2. 输入 'all' 选择全部")
        print("  3. 输入 'group' 按业务模块选择")
        print("  4. 直接回车取消")
        print("="*60)
        
        choice = input("\n请选择: ").strip()
        
        if not choice:
            return []
        elif choice.lower() == 'all':
            print(f"\n✅ 已选择全部 {len(files)} 个文件")
            return files
        elif choice.lower() == 'group':
            return self._select_by_group(files)
        else:
            return self._parse_selection(choice, files)


class ConcurrentExecutor:
    """并发执行引擎"""
    
    def __init__(self, max_workers: int = None, current_dir: str = None):
        """
        初始化并发执行引擎
        :param max_workers: 最大并发数，None 表示自动检测 CPU 核心数
        :param current_dir: 当前工作目录
        """
        self.max_workers = max_workers or os.cpu_count()
        self.current_dir = current_dir or os.getcwd()
        self.results_base_dir = Path(current_dir) / 'TestReport' / 'temp_results'
        
        # 确保临时结果目录存在
        self.results_base_dir.mkdir(parents=True, exist_ok=True)
    
    def execute_single_file(self, file_info: tuple) -> Dict[str, Any]:
        """
        执行单个文件的测试
        :param file_info: (文件路径, worker_id) 元组
        :return: 执行结果字典
        """
        file_path, worker_id = file_info
        
        # 为每个文件创建独立的结果目录
        result_dir = self.results_base_dir / f'worker_{worker_id}'
        result_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置环境变量
        env = os.environ.copy()
        env['TEST_DATA_FILE'] = str(file_path)
        env['ALLURE_RESULTS_DIR'] = str(result_dir)
        env['WORKER_ID'] = str(worker_id)  # 用于日志隔离
        # 🔧 设置 Python 输出编码为 UTF-8，避免 GBK 编码错误（特别是 emoji 字符）
        env['PYTHONIOENCODING'] = 'utf-8'
        
        # 构建 pytest 命令
        test_file = Path(self.current_dir) / 'test_case' / 'test_case.py'
        cmd = [
            sys.executable, '-m', 'pytest',
            str(test_file),
            '-s', '-q',
            '--clean-alluredir',
            f'--alluredir={result_dir}',
            '--tb=short',  # 短格式的错误信息
        ]
        
        print(f"\n🚀 开始执行: {file_path.name} (Worker {worker_id})")
        
        start_time = time.time()
        try:
            result = subprocess.run(
                cmd, 
                env=env, 
                capture_output=True, 
                text=True,
                encoding='utf-8',  # 🔧 明确指定 UTF-8 编码，避免 Windows 默认 GBK 编码导致的 emoji 错误
                errors='replace',  # 遇到无法解码的字符时用替换字符代替，避免崩溃
                cwd=self.current_dir,
                timeout=600  # 10分钟超时
            )
            end_time = time.time()
            
            return {
                'file': file_path.name,
                'file_path': str(file_path),
                'worker_id': worker_id,
                'result_dir': result_dir,
                'return_code': result.returncode,
                'duration': end_time - start_time,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'success': result.returncode == 0,
                'error': None
            }
            
        except subprocess.TimeoutExpired:
            end_time = time.time()
            return {
                'file': file_path.name,
                'file_path': str(file_path),
                'worker_id': worker_id,
                'result_dir': result_dir,
                'return_code': -1,
                'duration': end_time - start_time,
                'stdout': '',
                'stderr': 'Execution timeout (600s)',
                'success': False,
                'error': 'Timeout'
            }
            
        except Exception as e:
            end_time = time.time()
            return {
                'file': file_path.name,
                'file_path': str(file_path),
                'worker_id': worker_id,
                'result_dir': result_dir,
                'return_code': -1,
                'duration': end_time - start_time,
                'stdout': '',
                'stderr': str(e),
                'success': False,
                'error': str(e)
            }
    
    def execute_concurrent(self, file_list: List[Path]) -> List[Dict[str, Any]]:
        """
        并发执行多个文件
        :param file_list: 要执行的文件列表
        :return: 执行结果列表
        """
        if not file_list:
            print("❌ 文件列表为空")
            return []
        
        print(f"\n{'='*60}")
        print(f"🚀 启动并发执行引擎")
        print(f"{'='*60}")
        print(f"   📊 文件数: {len(file_list)}")
        print(f"   ⚙️  并发数: {self.max_workers}")
        print(f"   📁 结果目录: {self.results_base_dir}")
        print(f"{'='*60}\n")
        
        results = []
        
        # 准备任务列表：(文件路径, worker_id)
        tasks = [(file, idx) for idx, file in enumerate(file_list)]
        
        # 使用进程池执行
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_file = {
                executor.submit(self.execute_single_file, task): task[0]
                for task in tasks
            }
            
            # 等待任务完成
            completed = 0
            total = len(future_to_file)
            
            for future in as_completed(future_to_file):
                file = future_to_file[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    completed += 1
                    
                    # 显示进度和结果
                    status = "✅ 通过" if result['success'] else "❌ 失败"
                    print(f"\n[{completed}/{total}] {status} | {result['file']:<45s} | "
                          f"耗时: {result['duration']:.2f}s")
                    
                    # 如果失败，显示错误信息
                    if not result['success'] and result.get('error'):
                        print(f"         ⚠️  错误: {result['error']}")
                    
                except Exception as e:
                    print(f"\n❌ {file.name} 执行异常: {e}")
                    results.append({
                        'file': file.name,
                        'file_path': str(file),
                        'success': False,
                        'error': str(e),
                        'duration': 0
                    })
        
        print(f"\n{'='*60}")
        print(f"✅ 并发执行完成")
        print(f"{'='*60}\n")
        
        return results


class ReportAggregator:
    """Allure 报告聚合器"""
    
    def __init__(self, report_dir: str, results_dirs: List[Path]):
        """
        初始化报告聚合器
        :param report_dir: 最终报告目录
        :param results_dirs: 所有 allure-results 目录列表
        """
        self.report_dir = Path(report_dir)
        self.results_dirs = results_dirs
        self.merged_results_dir = self.report_dir.parent / 'allure-results'
    
    def merge_results(self) -> bool:
        """
        合并所有 allure-results
        :return: 是否成功
        """
        print("\n📊 正在合并测试结果...")
        
        try:
            # 清空并创建合并目录
            if self.merged_results_dir.exists():
                shutil.rmtree(self.merged_results_dir)
            self.merged_results_dir.mkdir(parents=True, exist_ok=True)
            
            # 复制所有结果文件
            total_files = 0
            for result_dir in self.results_dirs:
                if result_dir.exists():
                    for file in result_dir.glob('*'):
                        if file.is_file():
                            # 确保文件名唯一（避免覆盖）
                            dest_file = self.merged_results_dir / file.name
                            counter = 1
                            while dest_file.exists():
                                stem = file.stem
                                suffix = file.suffix
                                dest_file = self.merged_results_dir / f"{stem}_{counter}{suffix}"
                                counter += 1
                            
                            shutil.copy2(file, dest_file)
                            total_files += 1
            
            print(f"   ✅ 已合并 {total_files} 个结果文件")
            return True
            
        except Exception as e:
            print(f"   ❌ 合并结果失败: {e}")
            return False
    
    def generate_report(self) -> bool:
        """
        生成 Allure 报告
        :return: 是否成功
        """
        print("\n📈 正在生成 Allure 报告...")
        
        try:
            cmd = f'allure generate {self.merged_results_dir} -o {self.report_dir} --clean'
            result = os.system(cmd)
            
            if result == 0:
                print(f"   ✅ 报告生成成功!")
                print(f"   📁 报告位置: {self.report_dir}")
                return True
            else:
                print("   ❌ 报告生成失败!")
                print("   请确保已安装 Allure 命令行工具")
                return False
                
        except Exception as e:
            print(f"   ❌ 生成报告时出错: {e}")
            return False
    
    def generate_summary(self, execution_results: List[Dict[str, Any]]) -> None:
        """
        生成执行摘要
        :param execution_results: 执行结果列表
        """
        total = len(execution_results)
        success = sum(1 for r in execution_results if r.get('success', False))
        failed = total - success
        total_time = sum(r.get('duration', 0) for r in execution_results)
        avg_time = total_time / total if total > 0 else 0
        
        print("\n" + "="*60)
        print("📊 执行摘要")
        print("="*60)
        print(f"  📦 总文件数: {total}")
        print(f"  ✅ 成功: {success}")
        print(f"  ❌ 失败: {failed}")
        print(f"  📈 成功率: {(success/total*100):.1f}%")
        print(f"  ⏱️  总耗时: {total_time:.2f}s ({total_time/60:.1f} 分钟)")
        print(f"  🚀 平均耗时: {avg_time:.2f}s/文件")
        
        # 如果有失败的文件，列出来
        if failed > 0:
            print(f"\n  ⚠️  失败的文件:")
            for result in execution_results:
                if not result.get('success', False):
                    error_msg = result.get('error', '未知错误')
                    print(f"     ❌ {result['file']}: {error_msg}")
        
        print("="*60)


class LogMerger:
    """日志合并工具"""
    
    @staticmethod
    def merge_logs(log_dir: Path, output_file: Path) -> bool:
        """
        合并所有 worker 的日志到统一文件
        :param log_dir: 日志目录
        :param output_file: 输出文件
        :return: 是否成功
        """
        try:
            print("\n📝 正在合并日志文件...")
            
            # 查找所有日志文件
            log_files = []
            if log_dir.exists():
                # 查找格式: log.worker_0, log.worker_1, etc.
                log_files = sorted(log_dir.glob('log.worker_*'))
            
            if not log_files:
                print("   ℹ️  未找到需要合并的日志文件")
                return True
            
            # 读取所有日志条目
            all_entries = []
            for log_file in log_files:
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        entries = f.readlines()
                        all_entries.extend(entries)
                except Exception as e:
                    print(f"   ⚠️  读取日志文件 {log_file.name} 失败: {e}")
            
            # 按时间戳排序（如果日志有时间戳的话）
            # 这里简单地按原顺序合并，如果需要排序可以解析时间戳
            
            # 写入合并后的日志
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"{'='*80}\n")
                f.write(f"合并日志 - 生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"来源文件数: {len(log_files)}\n")
                f.write(f"{'='*80}\n\n")
                
                for log_file in log_files:
                    f.write(f"\n{'='*80}\n")
                    f.write(f"来源: {log_file.name}\n")
                    f.write(f"{'='*80}\n")
                    
                    try:
                        with open(log_file, 'r', encoding='utf-8') as lf:
                            f.write(lf.read())
                            f.write("\n")
                    except Exception as e:
                        f.write(f"读取失败: {e}\n")
           
            print(f"   ✅ 日志已合并到: {output_file}")
            print(f"   📊 合并了 {len(log_files)} 个日志文件")
            
            return True
            
        except Exception as e:
            print(f"   ❌ 合并日志失败: {e}")
            return False


# 测试代码
if __name__ == '__main__':
    print("并发执行模块测试")
    print("="*60)
    
    # 测试文件选择器
    selector = FileSelector('v10')
    files = selector.scan_files()
    print(f"找到 {len(files)} 个测试文件")
    for f in files[:5]:  # 只显示前5个
        print(f"  - {f.name}")

