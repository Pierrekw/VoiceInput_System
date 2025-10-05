# -*- coding: utf-8 -*-
"""
项目重构工具脚本

此脚本用于根据系统分离方案自动重构项目目录结构，
将同步和异步系统分离到独立的目录中，并创建共享组件目录。

使用方法：
1. 备份项目文件
2. 运行此脚本: python restructure_project.py
3. 脚本会根据配置自动移动文件和创建目录

注意事项：
- 请确保在运行前关闭所有使用项目文件的程序
- 建议在运行前先查看脚本的配置和实现，确保符合您的需求
- 脚本提供了模拟运行模式，可以先预览将要执行的操作
"""

import os
import shutil
import logging
import argparse
from pathlib import Path
import sys

# 配置日志
def setup_logger(log_level=logging.INFO):
    """设置日志记录器"""
    logger = logging.getLogger('ProjectRestructurer')
    logger.setLevel(log_level)
    
    # 避免重复添加handler
    if not logger.handlers:
        # 创建控制台handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        
        # 创建文件handler
        log_dir = Path(__file__).parent / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / 'restructure.log'
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(log_level)
        
        # 设置日志格式
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        # 添加handler到logger
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
    
    return logger


class ProjectRestructurer:
    """项目重构器类"""
    
    def __init__(self, simulate=False, log_level=logging.INFO):
        # 项目根目录
        self.project_root = Path(__file__).parent
        
        # 模拟运行模式
        self.simulate = simulate
        
        # 初始化日志
        self.logger = setup_logger(log_level)
        
        # 定义目录结构
        # 源目录 -> 目标目录映射
        self.directory_mapping = {
            # 同步系统目录
            'main.py': 'sync_system/main.py',
            'adapters/audio_capture.py': 'sync_system/adapters/audio_capture.py',
            'adapters/data_exporter.py': 'sync_system/adapters/data_exporter.py',
            'adapters/tts_controller.py': 'sync_system/adapters/tts_controller.py',
            'sync_config/': 'sync_system/config/',
            
            # 异步系统目录
            'main_production.py': 'async_system/main.py',
            'async_audio/': 'async_system/audio/',
            'async_config/': 'async_system/config/',
            'async_processing/': 'async_system/processing/',
            
            # 共享组件目录
            'interfaces/': 'shared/interfaces/',
            'text_processor.py': 'shared/text_processor.py',
            'shared_utils/': 'shared/utils/',
            'models/': 'shared/models/',
            
            # 测试目录
            'tests/': 'tests/',
            
            # 文档目录
            'docs/': 'docs/',
            'SYSTEM_WORKFLOW.md': 'docs/SYSTEM_WORKFLOW.md',
            'SHARED_MODULE_GUIDE.md': 'docs/SHARED_MODULE_GUIDE.md',
            'SYSTEM_SEPARATION_PLAN.md': 'docs/SYSTEM_SEPARATION_PLAN.md',
            'DETAILED_RESTRUCTURING_GUIDE.md': 'docs/DETAILED_RESTRUCTURING_GUIDE.md',
            'SYSTEM_SEPARATION_COMPARISON.md': 'docs/SYSTEM_SEPARATION_COMPARISON.md',
        }
        
        # 需要创建的目录列表
        self.required_directories = [
            'sync_system',
            'sync_system/adapters',
            'sync_system/config',
            'async_system',
            'async_system/audio',
            'async_system/config',
            'async_system/processing',
            'shared',
            'shared/interfaces',
            'shared/utils',
            'shared/models',
            'tests',
            'docs',
            'logs/sync',
            'logs/async',
        ]
        
        # 特殊处理文件
        self.special_files = {
            'requirements.txt': {
                'dest': 'requirements.txt',
                'action': 'keep'
            },
            '.gitignore': {
                'dest': '.gitignore',
                'action': 'keep'
            },
            'README.md': {
                'dest': 'README.md',
                'action': 'update'
            }
        }
        
        # 保存已移动的文件记录
        self.moved_files = []
        
        # 保存创建的目录记录
        self.created_directories = []
        
        # 保存跳过的文件记录
        self.skipped_files = []
        
        # 保存失败的操作记录
        self.failed_operations = []
    
    def create_directories(self):
        """创建所需的目录结构"""
        self.logger.info("📁 开始创建目录结构...")
        
        for dir_path in self.required_directories:
            abs_dir_path = self.project_root / dir_path
            if not abs_dir_path.exists():
                if self.simulate:
                    self.logger.info(f"📋 [模拟] 将创建目录: {abs_dir_path}")
                else:
                    try:
                        abs_dir_path.mkdir(parents=True, exist_ok=True)
                        self.logger.info(f"✅ 创建目录成功: {abs_dir_path}")
                        self.created_directories.append(str(abs_dir_path))
                    except Exception as e:
                        self.logger.error(f"❌ 创建目录失败: {abs_dir_path}, 错误: {e}")
                        self.failed_operations.append(("create_dir", str(abs_dir_path), str(e)))
            else:
                self.logger.warning(f"⚠️ 目录已存在: {abs_dir_path}")
    
    def move_files(self):
        """根据映射移动文件"""
        self.logger.info("📂 开始移动文件...")
        
        for src, dest in self.directory_mapping.items():
            src_path = self.project_root / src
            dest_path = self.project_root / dest
            
            # 检查源路径是否存在
            if not src_path.exists():
                self.logger.warning(f"⚠️ 源路径不存在: {src_path}")
                self.skipped_files.append(str(src_path))
                continue
            
            # 确保目标目录存在
            dest_dir = dest_path.parent
            if not dest_dir.exists():
                if self.simulate:
                    self.logger.info(f"📋 [模拟] 将创建目录: {dest_dir}")
                else:
                    try:
                        dest_dir.mkdir(parents=True, exist_ok=True)
                        self.logger.info(f"✅ 创建目标目录成功: {dest_dir}")
                        self.created_directories.append(str(dest_dir))
                    except Exception as e:
                        self.logger.error(f"❌ 创建目标目录失败: {dest_dir}, 错误: {e}")
                        self.failed_operations.append(("create_dir", str(dest_dir), str(e)))
                        continue
            
            # 移动文件或目录
            try:
                if src_path.is_dir():
                    # 移动目录
                    if self.simulate:
                        self.logger.info(f"📋 [模拟] 将移动目录: {src_path} -> {dest_path}")
                    else:
                        # 如果目标目录已存在，合并内容
                        if dest_path.exists():
                            self.logger.info(f"🔄 目标目录已存在，合并内容: {dest_path}")
                            # 遍历源目录中的所有文件和子目录
                            for item in src_path.iterdir():
                                item_dest = dest_path / item.name
                                if item.is_dir():
                                    if item_dest.exists():
                                        # 递归合并子目录
                                        self._merge_directories(item, item_dest)
                                    else:
                                        shutil.move(str(item), str(item_dest))
                                        self.logger.info(f"✅ 移动子目录: {item} -> {item_dest}")
                                else:
                                    # 文件存在则覆盖
                                    if item_dest.exists():
                                        self.logger.warning(f"⚠️ 文件已存在，将覆盖: {item_dest}")
                                    shutil.move(str(item), str(item_dest))
                                    self.logger.info(f"✅ 移动文件: {item} -> {item_dest}")
                        else:
                            shutil.move(str(src_path), str(dest_path))
                            self.logger.info(f"✅ 移动目录: {src_path} -> {dest_path}")
                        self.moved_files.append((str(src_path), str(dest_path)))
                else:
                    # 移动文件
                    if self.simulate:
                        self.logger.info(f"📋 [模拟] 将移动文件: {src_path} -> {dest_path}")
                    else:
                        # 文件存在则覆盖
                        if dest_path.exists():
                            self.logger.warning(f"⚠️ 文件已存在，将覆盖: {dest_path}")
                        shutil.move(str(src_path), str(dest_path))
                        self.logger.info(f"✅ 移动文件: {src_path} -> {dest_path}")
                        self.moved_files.append((str(src_path), str(dest_path)))
            except Exception as e:
                self.logger.error(f"❌ 移动失败: {src_path} -> {dest_path}, 错误: {e}")
                self.failed_operations.append(("move", str(src_path), str(dest_path), str(e)))
    
    def _merge_directories(self, src_dir, dest_dir):
        """递归合并两个目录"""
        for item in src_dir.iterdir():
            item_dest = dest_dir / item.name
            if item.is_dir():
                if item_dest.exists():
                    # 递归合并子目录
                    self._merge_directories(item, item_dest)
                else:
                    shutil.move(str(item), str(item_dest))
                    self.logger.info(f"✅ 移动子目录: {item} -> {item_dest}")
            else:
                # 文件存在则覆盖
                if item_dest.exists():
                    self.logger.warning(f"⚠️ 文件已存在，将覆盖: {item_dest}")
                shutil.move(str(item), str(item_dest))
                self.logger.info(f"✅ 移动文件: {item} -> {item_dest}")
    
    def handle_special_files(self):
        """处理特殊文件"""
        self.logger.info("📝 开始处理特殊文件...")
        
        for src, config in self.special_files.items():
            src_path = self.project_root / src
            dest_path = self.project_root / config['dest']
            action = config['action']
            
            if action == 'keep':
                # 保持文件不变
                if src_path.exists():
                    self.logger.info(f"📌 保持文件不变: {src_path}")
                else:
                    self.logger.warning(f"⚠️ 文件不存在，跳过保持操作: {src_path}")
            elif action == 'update':
                # 更新文件
                if self.simulate:
                    self.logger.info(f"📋 [模拟] 将更新文件: {src_path}")
                else:
                    if src_path.exists():
                        # 备份原文件
                        backup_path = src_path.with_suffix(src_path.suffix + '.bak')
                        try:
                            shutil.copy2(str(src_path), str(backup_path))
                            self.logger.info(f"💾 备份文件: {src_path} -> {backup_path}")
                            
                            # 这里可以添加更新文件的逻辑
                            # 例如更新README.md以反映新的项目结构
                            if src == 'README.md':
                                self._update_readme(src_path)
                        except Exception as e:
                            self.logger.error(f"❌ 更新文件失败: {src_path}, 错误: {e}")
                            self.failed_operations.append(("update", str(src_path), str(e)))
                    else:
                        self.logger.warning(f"⚠️ 文件不存在，跳过更新操作: {src_path}")
            elif action == 'create':
                # 创建文件
                if self.simulate:
                    self.logger.info(f"📋 [模拟] 将创建文件: {dest_path}")
                else:
                    if not dest_path.exists():
                        try:
                            # 这里可以添加创建文件的逻辑
                            # 例如创建.gitignore文件
                            if src == '.gitignore':
                                self._create_gitignore(dest_path)
                        except Exception as e:
                            self.logger.error(f"❌ 创建文件失败: {dest_path}, 错误: {e}")
                            self.failed_operations.append(("create", str(dest_path), str(e)))
                    else:
                        self.logger.warning(f"⚠️ 文件已存在，跳过创建操作: {dest_path}")
    
    def _update_readme(self, readme_path):
        """更新README.md文件"""
        try:
            # 读取现有内容
            with open(readme_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否已经包含项目结构信息
            if "## 项目结构" not in content:
                # 添加项目结构信息
                new_content = content + "\n\n## 项目结构\n\n""
                ```\n"
                "├── sync_system/           # 同步系统代码\n"
                "│   ├── main.py            # 同步系统入口\n"
                "│   ├── adapters/          # 同步系统适配器\n"
                "│   └── config/            # 同步系统配置\n"
                "├── async_system/          # 异步系统代码\n"
                "│   ├── main.py            # 异步系统入口\n"
                "│   ├── audio/             # 异步音频处理\n"
                "│   ├── processing/        # 异步数据处理\n"
                "│   └── config/            # 异步系统配置\n"
                "├── shared/                # 共享组件\n"
                "│   ├── interfaces/        # 共享接口定义\n"
                "│   ├── utils/             # 共享工具类\n"
                "│   └── models/            # 共享模型文件\n"
                "├── tests/                 # 测试代码\n"
                "├── docs/                  # 文档\n"
                "├── logs/                  # 日志文件\n"
                "│   ├── sync/              # 同步系统日志\n"
                "│   └── async/             # 异步系统日志\n"
                "├── requirements.txt       # 项目依赖\n"
                "├── README.md              # 项目说明\n"
                "└── .gitignore             # Git忽略规则\n"
                "```\n""
            
            # 更新README.md
            
                with open(readme_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                    self.logger.info(f"✅ 更新README.md成功: {readme_path}")
            else:
                    self.logger.info(f"✅ README.md已包含项目结构信息，跳过更新: {readme_path}")
        except Exception as e:
    
            self.logger.error(f"❌ 更新README.md失败: {e}")
            raise
    
    def _create_gitignore(self, gitignore_path):
        """创建.gitignore文件"""
        try:
            gitignore_content = """
# Python
__pycache__/
*.py[cod]
*$py.class

# Virtual environments
venv/
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# IDEs and editors
.vscode/
.idea/
*.swp
*.swo
*~

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Logs
logs/
*.log

# Runtime data
pids
*.pid
*.seed
*.pid.lock

# Coverage directory used by tools like istanbul
coverage/

# nyc test coverage
.nyc_output

# Grunt intermediate storage (https://gruntjs.com/creating-plugins#storing-task-files)
.grunt

# Bower dependency directory (https://bower.io/)
bower_components/

# node-waf configuration
.lock-wscript

# Compiled binary addons (https://nodejs.org/api/addons.html)
build/Release

# Dependency directories
node_modules/
jspm_packages/

# Snowpack dependency directory (https://snowpack.dev/)
web_modules/

# TypeScript cache
*.tsbuildinfo

# Optional npm cache directory
.npm

# Optional eslint cache
.eslintcache

# Microbundle cache
.rpt2_cache/
.rts2_cache_cjs/
.rts2_cache_es/
.rts2_cache_umd/

# Optional REPL history
.node_repl_history

# Output of 'npm pack'
*.tgz

# Yarn Integrity file
.yarn-integrity

# parcel-bundler cache (https://parceljs.org/)
.cache
.parcel-cache

# Next.js build output
.next

# Nuxt.js build / generate output
.nuxt
dist

# Gatsby files
.cache/
public

# vuepress build output
.vuepress/dist

# vuepress v2.x temp and cache directory
.temp
.cache

# Serverless directories
.serverless/

# FuseBox cache
.fusebox/

# DynamoDB Local files
.dynamodb/

# TernJS port file
.tern-port

# Stores VSCode versions used for testing VSCode extensions
.vscode-test

# yarn v2
.yarn/cache
.yarn/unplugged
.yarn/build-state.yml
.yarn/install-state.gz
.pnp.*

# Excel files
*.xlsx
*.xls
!tests/*.xlsx
!tests/*.xls

# Model files (如果模型文件很大，可以考虑不提交)
# shared/models/
"""
            
            with open(gitignore_path, 'w', encoding='utf-8') as f:
                f.write(gitignore_content.strip())
            self.logger.info(f"✅ 创建.gitignore成功: {gitignore_path}")
        except Exception as e:
            self.logger.error(f"❌ 创建.gitignore失败: {e}")
            raise
    
    def create_venv_files(self):
        """创建虚拟环境相关文件"""
        self.logger.info("🐍 开始创建虚拟环境相关文件...")
        
        # 创建同步系统venv配置
        sync_venv_file = self.project_root / 'sync_system' / 'requirements.txt'
        if not sync_venv_file.exists():
            if self.simulate:
                self.logger.info(f"📋 [模拟] 将创建同步系统requirements.txt: {sync_venv_file}")
            else:
                try:
                    # 复制主requirements.txt内容
                    main_requirements = self.project_root / 'requirements.txt'
                    if main_requirements.exists():
                        shutil.copy2(str(main_requirements), str(sync_venv_file))
                        self.logger.info(f"✅ 创建同步系统requirements.txt成功: {sync_venv_file}")
                    else:
                        # 创建空文件或默认内容
                        with open(sync_venv_file, 'w', encoding='utf-8') as f:
                            f.write("# 同步系统依赖\n")
                        self.logger.info(f"✅ 创建空的同步系统requirements.txt成功: {sync_venv_file}")
                except Exception as e:
                    self.logger.error(f"❌ 创建同步系统requirements.txt失败: {e}")
                    self.failed_operations.append(("create", str(sync_venv_file), str(e)))
        else:
            self.logger.warning(f"⚠️ 同步系统requirements.txt已存在: {sync_venv_file}")
        
        # 创建异步系统venv配置
        async_venv_file = self.project_root / 'async_system' / 'requirements.txt'
        if not async_venv_file.exists():
            if self.simulate:
                self.logger.info(f"📋 [模拟] 将创建异步系统requirements.txt: {async_venv_file}")
            else:
                try:
                    # 复制主requirements.txt内容
                    main_requirements = self.project_root / 'requirements.txt'
                    if main_requirements.exists():
                        shutil.copy2(str(main_requirements), str(async_venv_file))
                        self.logger.info(f"✅ 创建异步系统requirements.txt成功: {async_venv_file}")
                    else:
                        # 创建空文件或默认内容
                        with open(async_venv_file, 'w', encoding='utf-8') as f:
                            f.write("# 异步系统依赖\n")
                        self.logger.info(f"✅ 创建空的异步系统requirements.txt成功: {async_venv_file}")
                except Exception as e:
                    self.logger.error(f"❌ 创建异步系统requirements.txt失败: {e}")
                    self.failed_operations.append(("create", str(async_venv_file), str(e)))
        else:
            self.logger.warning(f"⚠️ 异步系统requirements.txt已存在: {async_venv_file}")
    
    def generate_report(self):
        """生成重构报告"""
        self.logger.info("📊 生成重构报告...")
        
        report_path = self.project_root / 'logs' / 'restructure_report.md'
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write("# 项目重构报告\n\n")
                f.write(f"## 重构时间\n\n{self.logger.handlers[1].formatter.formatTime(logging.LogRecord('dummy', logging.INFO, '', 0, '', (), None))}\n\n")
                f.write("## 重构模式\n\n")
                f.write(f"- 模拟运行: {'是' if self.simulate else '否'}\n\n")
                
                f.write("## 创建的目录\n\n")
                if self.created_directories:
                    for dir_path in sorted(self.created_directories):
                        f.write(f"- {dir_path}\n")
                else:
                    f.write("- 无\n")
                f.write("\n")
                
                f.write("## 移动的文件\n\n")
                if self.moved_files:
                    for src, dest in self.moved_files:
                        f.write(f"- {src} -> {dest}\n")
                else:
                    f.write("- 无\n")
                f.write("\n")
                
                f.write("## 跳过的文件\n\n")
                if self.skipped_files:
                    for file_path in sorted(self.skipped_files):
                        f.write(f"- {file_path}\n")
                else:
                    f.write("- 无\n")
                f.write("\n")
                
                f.write("## 失败的操作\n\n")
                if self.failed_operations:
                    for op in self.failed_operations:
                        if len(op) == 4:
                            action, src, dest, error = op
                            f.write(f"- {action}: {src} -> {dest}, 错误: {error}\n")
                        elif len(op) == 3:
                            action, path, error = op
                            f.write(f"- {action}: {path}, 错误: {error}\n")
                        else:
                            f.write(f"- {op}\n")
                else:
                    f.write("- 无\n")
                f.write("\n")
                
                f.write("## 重构建议\n\n")
                if self.failed_operations:
                    f.write("1. 检查失败的操作，手动处理这些问题\n")
                f.write("1. 重构完成后，建议运行测试确保系统功能正常\n")
                f.write("2. 根据新的目录结构更新导入路径\n")
                f.write("3. 考虑为同步和异步系统创建独立的虚拟环境\n")
                f.write("4. 更新Git仓库以反映新的项目结构\n")
            
            self.logger.info(f"✅ 重构报告生成成功: {report_path}")
            
            # 打印摘要
            self.logger.info("\n📋 重构摘要:")
            self.logger.info(f"✅ 创建目录: {len(self.created_directories)}")
            self.logger.info(f"✅ 移动文件: {len(self.moved_files)}")
            self.logger.info(f"⚠️ 跳过文件: {len(self.skipped_files)}")
            self.logger.info(f"❌ 失败操作: {len(self.failed_operations)}")
            self.logger.info(f"📊 详细报告: {report_path}")
        except Exception as e:
            self.logger.error(f"❌ 生成重构报告失败: {e}")
    
    def run(self):
        """执行重构过程"""
        self.logger.info("🚀 开始项目重构...")
        
        try:
            # 1. 创建目录结构
            self.create_directories()
            
            # 2. 移动文件
            self.move_files()
            
            # 3. 处理特殊文件
            self.handle_special_files()
            
            # 4. 创建虚拟环境相关文件
            self.create_venv_files()
            
            # 5. 生成重构报告
            self.generate_report()
            
            if self.simulate:
                self.logger.info("✅ 模拟重构完成，请检查输出并确认后再执行实际重构")
            else:
                self.logger.info("✅ 项目重构完成！")
            
        except Exception as e:
            self.logger.error(f"❌ 重构过程中发生异常: {e}")
            self.failed_operations.append(("run", "整个重构过程", str(e)))
            self.generate_report()
            raise


# 主函数
def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='项目重构工具')
    parser.add_argument('--simulate', '-s', action='store_true', help='模拟运行模式，不实际执行文件操作')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出模式')
    args = parser.parse_args()
    
    # 确定日志级别
    log_level = logging.DEBUG if args.verbose else logging.INFO
    
    # 创建重构器实例
    restructurer = ProjectRestructurer(simulate=args.simulate, log_level=log_level)
    
    # 执行重构
    try:
        restructurer.run()
        return 0
    except Exception as e:
        print(f"❌ 重构失败: {e}")
        return 1


# 程序入口
if __name__ == "__main__":
    sys.exit(main())