@echo off
chcp 65001 >nul
cls

echo ================================================
echo   🤖 Modern Wikipedia AI Assistant - Windows
echo   Сборка для Windows (использует .ico файлы)
echo ================================================
echo.

REM Проверка текущей операционной системы
echo [0/7] Проверка операционной системы...
ver | findstr /i "Microsoft Windows" >nul
if %errorlevel% neq 0 (
    echo ❌ Этот скрипт предназначен только для Windows!
    echo ❌ Обнаружена система: %OS%
    echo.
    echo Для macOS используйте: build_mac.sh
    echo Для Linux используйте: build_linux.sh или python build.py
    pause
    exit /b 1
)

echo ✅ Система: Windows
echo.

REM Проверка Python
echo [1/7] Проверка установки Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден!
    echo.
    echo Установите Python 3.8+ с сайта:
    echo https://www.python.org/downloads/
    echo.
    echo При установке отметьте "Add Python to PATH"
    echo.
    echo Проверка альтернативных команд...
    python3 --version >nul 2>&1
    if errorlevel 1 (
        echo ❌ python3 также не найден!
        pause
        exit /b 1
    ) else (
        echo ✅ Найден python3, будет использоваться он
        set PYTHON_CMD=python3
    )
) else (
    set PYTHON_CMD=python
)

%PYTHON_CMD% --version 2>&1 | findstr /i "Python" >nul
if errorlevel 1 (
    echo ❌ Не удалось определить версию Python
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('%PYTHON_CMD% --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Python версии %PYTHON_VERSION% обнаружен

REM Проверка наличия иконки для Windows
echo.
echo [2/7] Проверка файлов иконок...
if exist "icon.ico" (
    echo ✅ Найден файл иконки для Windows: icon.ico
    set ICON_FILE=icon.ico
) else if exist "icons\icon.ico" (
    echo ✅ Найден файл иконки для Windows: icons\icon.ico
    set ICON_FILE=icons\icon.ico
) else if exist "icon.icns" (
    echo ⚠️ Найден только .icns файл (для macOS)
    echo    Создаем .ico файл на его основе...
    %PYTHON_CMD% -c "from PIL import Image; img = Image.open('icon.icns'); img.save('icon.ico', format='ICO'); print('✅ Создан icon.ico')" 2>nul
    if exist "icon.ico" (
        echo ✅ Файл icon.ico создан
        set ICON_FILE=icon.ico
    ) else (
        echo ⚠️ Не удалось создать .ico, сборка без иконки
        set ICON_FILE=
    )
) else (
    echo ⚠️ Файл иконки не найден. Сборка без иконки.
    set ICON_FILE=
)

REM Создание виртуального окружения
echo.
echo [3/7] Создание виртуального окружения...
if exist "venv" (
    echo ⚠️ Виртуальное окружение уже существует
    choice /M "Пересоздать? (Y/N)"
    if errorlevel 2 (
        echo Используем существующее окружение
    ) else (
        rmdir /s /q venv 2>nul
        %PYTHON_CMD% -m venv venv
        echo ✅ Виртуальное окружение создано заново
    )
) else (
    %PYTHON_CMD% -m venv venv
    echo ✅ Виртуальное окружение создано
)

REM Активация виртуального окружения
echo.
echo [4/7] Активация виртуального окружения...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ Не удалось активировать виртуальное окружение
    echo Попробуйте запустить от имени администратора
    pause
    exit /b 1
)
echo ✅ Виртуальное окружение активировано

REM Обновление pip
echo.
echo [5/7] Обновление pip и установщика пакетов...
python -m pip install --upgrade pip setuptools wheel
echo ✅ Pip обновлен

REM Установка зависимостей
echo.
echo [6/7] Установка зависимостей из requirements.txt...
if exist "requirements.txt" (
    echo Установка из requirements.txt...
    pip install -r requirements.txt
) else (
    echo ⚠️ Файл requirements.txt не найден
    echo Создаем requirements.txt...
    (
echo wikipedia==1.4.0
echo nltk==3.8.1
echo scikit-learn==1.3.0
echo beautifulsoup4==4.12.2
echo requests==2.31.0
echo numpy==1.24.3
echo pyinstaller==5.13.0
echo Pillow^>=9.0.0
    ) > requirements.txt
    echo Устанавливаем зависимости вручную...
    pip install -r requirements.txt
)
echo ✅ Зависимости установлены

REM Скачивание данных NLTK
echo.
echo [7/7] Загрузка данных NLTK (это займет некоторое время)...
python -c "import nltk; nltk.download('punkt_tab', quiet=True); nltk.download('stopwords', quiet=True); print('✅ Данные NLTK загружены')"
if errorlevel 1 (
    echo ⚠️ Ошибка загрузки данных NLTK
    echo Попробуем загрузить вручную...
    python -c "
import nltk
import ssl

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

print('Скачивание punkt_tab...')
nltk.download('punkt_tab')
print('Скачивание stopwords...')
nltk.download('stopwords')
print('✅ Данные NLTK загружены')
"
)

REM Сборка приложения
echo.
echo [8/8] Сборка приложения с помощью PyInstaller...
echo Выберите тип сборки:
echo 1. Один EXE файл (рекомендуется для распространения)
echo 2. В папке (быстрее, легче отлаживать)
echo 3. Минимальная сборка (только основные зависимости)
echo.

choice /C 123 /M "Ваш выбор (1/2/3): "
if errorlevel 3 (
    echo Собираем минимальную версию...
    if "%ICON_FILE%"=="" (
        pyinstaller --clean --onefile --windowed --name "WikipediaAI" ^
                    --exclude-module PyQt5 ^
                    --exclude-module matplotlib ^
                    --hidden-import "sklearn.utils._weight_vector" ^
                    --hidden-import "sklearn.neighbors._typedefs" ^
                    main.py
    ) else (
        pyinstaller --clean --onefile --windowed --name "WikipediaAI" ^
                    --icon "%ICON_FILE%" ^
                    --exclude-module PyQt5 ^
                    --exclude-module matplotlib ^
                    --hidden-import "sklearn.utils._weight_vector" ^
                    --hidden-import "sklearn.neighbors._typedefs" ^
                    main.py
    )
    set BUILD_TYPE=minimal
) else if errorlevel 2 (
    echo Собираем в папке...
    if "%ICON_FILE%"=="" (
        pyinstaller --clean --windowed --name "WikipediaAI" ^
                    --exclude-module PyQt5 ^
                    --exclude-module matplotlib ^
                    --hidden-import "sklearn.utils._weight_vector" ^
                    --hidden-import "sklearn.neighbors._typedefs" ^
                    main.py
    ) else (
        pyinstaller --clean --windowed --name "WikipediaAI" ^
                    --icon "%ICON_FILE%" ^
                    --exclude-module PyQt5 ^
                    --exclude-module matplotlib ^
                    --hidden-import "sklearn.utils._weight_vector" ^
                    --hidden-import "sklearn.neighbors._typedefs" ^
                    main.py
    )
    set BUILD_TYPE=folder
) else (
    echo Собираем в один EXE файл...
    if "%ICON_FILE%"=="" (
        pyinstaller --clean --onefile --windowed --name "WikipediaAI" ^
                    --add-data "nltk_data;nltk_data" ^
                    --exclude-module PyQt5 ^
                    --exclude-module matplotlib ^
                    --hidden-import "sklearn.utils._weight_vector" ^
                    --hidden-import "sklearn.neighbors._typedefs" ^
                    main.py
    ) else (
        pyinstaller --clean --onefile --windowed --name "WikipediaAI" ^
                    --icon "%ICON_FILE%" ^
                    --add-data "nltk_data;nltk_data" ^
                    --exclude-module PyQt5 ^
                    --exclude-module matplotlib ^
                    --hidden-import "sklearn.utils._weight_vector" ^
                    --hidden-import "sklearn.neighbors._typedefs" ^
                    main.py
    )
    set BUILD_TYPE=onefile
)

echo.
echo ================================================
echo 🎉 Сборка успешно завершена!
echo.

if "%BUILD_TYPE%"=="onefile" (
    echo ✅ Создан один файл: dist\WikipediaAI.exe
    echo 📏 Примерный размер:
    for /f %%s in ('dir /-c "dist\WikipediaAI.exe" ^| findstr /i "WikipediaAI.exe"') do echo       %%s байт
) else if "%BUILD_TYPE%"=="folder" (
    echo ✅ Создана папка с приложением: dist\WikipediaAI\
    echo 📁 Запускаемый файл: dist\WikipediaAI\WikipediaAI.exe
) else (
    echo ✅ Создана минимальная сборка: dist\WikipediaAI.exe
)

echo.
echo 📋 Создание README для пользователя...
(
echo 📋 Wikipedia AI Assistant - Windows
echo =====================================================
echo.
echo 🚀 ИНСТРУКЦИЯ ПО ЗАПУСКУ:
echo.
if "%BUILD_TYPE%"=="onefile" (
echo 1. Запустите файл: WikipediaAI.exe
) else if "%BUILD_TYPE%"=="folder" (
echo 1. Перейдите в папку WikipediaAI
echo 2. Запустите файл: WikipediaAI.exe
) else (
echo 1. Запустите файл: WikipediaAI.exe
)
echo.
echo 2. При первом запуске приложение может загрузить
echo    необходимые данные (1-2 минуты)
echo.
echo 3. После загрузки откроется главное окно программы
echo.
echo ⚠️ ВАЖНО:
echo - Антивирус может заблокировать файл .exe
echo - Добавьте папку с программой в исключения антивируса
echo - Или используйте версию "в папке" (не onefile)
echo.
echo 📁 ВАШИ ДАННЫЕ:
echo База знаний сохраняется в: %%APPDATA%%\WikipediaAI\
echo.
echo 🔧 ПЕРЕСБОРКА:
echo Для обновления программы запустите build_windows.bat
echo.
echo =====================================================
echo 🤖 Modern Wikipedia AI Assistant
echo 📧 Поддержка: ваш.email@example.com
echo 🌐 GitHub: https://github.com/ваш-репозиторий
echo =====================================================
echo Сборка от: %DATE% %TIME%
) > "dist\README_Windows.txt"

echo ✅ Создан README_Windows.txt
echo.

REM Открытие папки с результатом
echo ================================================
echo 📂 Открытие папки с результатами...
timeout /t 2 /nobreak >nul

choice /M "Открыть папку dist? (Y/N)"
if errorlevel 2 (
    echo Папка с результатом: %CD%\dist\
    echo.
    echo Для запуска программы:
    if "%BUILD_TYPE%"=="folder" (
        echo   dist\WikipediaAI\WikipediaAI.exe
    ) else (
        echo   dist\WikipediaAI.exe
    )
) else (
    explorer "dist"
)

echo.
echo ⚡ Готово! Для запуска программы:
if "%BUILD_TYPE%"=="folder" (
    echo   dist\WikipediaAI\WikipediaAI.exe
) else (
    echo   dist\WikipediaAI.exe
)
echo.
echo ================================================
pause