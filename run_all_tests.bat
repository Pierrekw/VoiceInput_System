@echo off
REM 语音输入系统 - 全面测试运行脚本
REM 此脚本提供多种测试运行选项，适用于不同的测试场景

SETLOCAL ENABLEDELAYEDEXPANSION

REM 设置中文编码
setset PYTHONIOENCODING=utf-8

REM 清屏
cls

echo ===================================================================
echo 🚀 语音输入系统 - 全面测试运行脚本
echo ===================================================================
echo 此脚本提供多种测试运行选项，帮助您验证系统功能

echo.
echo 1. 使用pytest运行所有测试
echo 2. 非交互式运行自动集成测试
echo 3. 运行综合集成测试
echo 4. 验证JSON配置文件格式
echo.

:choice
set /p "option=请选择测试选项 (1-4, 直接按回车选择1): "
if "!option!"=="" set option=1

if !option! EQU 1 goto pytest_all
if !option! EQU 2 goto auto_integration
if !option! EQU 3 goto full_integration
if !option! EQU 4 goto check_json

REM 无效选项
cls
echo ❌ 无效的选择，请重新输入
goto choice

:pytest_all
echo ===================================================================
echo 🧪 使用pytest运行所有测试
echo ===================================================================
python -m pytest -v
goto end

:auto_integration
echo ===================================================================
echo 🤖 非交互式运行自动集成测试
echo ===================================================================
python tests/integrated_test.py < NUL
goto end

:full_integration
echo ===================================================================
echo 🔄 运行综合集成测试
echo ===================================================================
echo 注意：此测试将启动交互式测试界面
pause
echo
echo 请在测试界面中选择选项 1 运行综合集成测试
echo
echo 按任意键继续...
pause >nul
echo
echo 启动测试中...
start "语音输入系统 - 集成测试" cmd /k "python tests/integrated_test.py"
goto end

:check_json
echo ===================================================================
echo 🔍 验证JSON配置文件格式
echo ===================================================================
python check_json.py
goto end

:end
echo ===================================================================
echo ✅ 测试命令已执行完毕
echo ===================================================================
echo 按任意键退出...
pause >nul
EXIT /B