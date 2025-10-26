@echo off
echo 测试下载脚本基本功能...

REM 测试基本命令
echo 1. 测试目录创建...
if not exist "test_temp" mkdir "test_temp"
if exist "test_temp" echo ✅ 目录创建成功

echo 2. 测试PowerShell...
powershell -Command "Write-Host 'PowerShell可用'" 2>nul
if %ERRORLEVEL% equ 0 (
    echo ✅ PowerShell可用
) else (
    echo ❌ PowerShell不可用
    echo 尝试其他PowerShell路径...
    powershell.exe -Command "Write-Host 'PowerShell.exe可用'" 2>nul
    if %ERRORLEVEL% equ 0 (
        echo ✅ PowerShell.exe可用
    ) else (
        echo ❌ 所有PowerShell路径都不可用
    )
)

echo 3. 测试网络连接...
ping -n 1 8.8.8.8 >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo ✅ 网络连接正常
) else (
    echo ❌ 网络连接异常
)

echo 4. 测试curl...
curl --version >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo ✅ curl可用
) else (
    echo ❌ curl不可用
)

echo 5. 测试文件下载...
cd test_temp
echo 尝试下载小文件测试...
powershell -Command "Invoke-WebRequest -Uri 'https://httpbin.org/get' -OutFile 'test.txt'" 2>nul
if %ERRORLEVEL% equ 0 (
    echo ✅ PowerShell下载功能正常
    if exist test.txt (
        echo 文件大小:
        dir test.txt | findstr test.txt
        del test.txt
    )
) else (
    echo ❌ PowerShell下载功能异常
)

cd ..
rmdir test_temp 2>nul

echo.
echo 基础功能测试完成
pause