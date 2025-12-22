import os
import sys
import platform
import subprocess
import shutil


def build_app():
    """Функция сборки приложения"""

    system = platform.system()
    app_name = "WikipediaAI"

    print(f"🛠️ Сборка для {system}")
    print("=" * 50)

    # Удаляем старые сборки
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    if os.path.exists("build"):
        shutil.rmtree("build")

    # Параметры для разных ОС
    if system == "Windows":
        # Windows
        cmd = [
            "pyinstaller",
            "--onefile",
            "--windowed",
            "--name", app_name,
            "--add-data", "nltk_data;nltk_data",
            "main.py"
        ]

    elif system == "Darwin":  # macOS
        cmd = [
            "pyinstaller",
            "--onefile",
            "--windowed",
            "--name", app_name,
            "--add-data", "nltk_data:nltk_data",
            "main.py"
        ]

    else:  # Linux
        cmd = [
            "pyinstaller",
            "--onefile",
            "--name", app_name.lower(),
            "--add-data", "nltk_data:nltk_data",
            "main.py"
        ]

    # Выполняем сборку
    try:
        subprocess.run(cmd, check=True)
        print(f"✅ Сборка завершена успешно!")
        print(f"📁 Исполняемый файл в папке: dist/")

    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка сборки: {e}")
        return False

    # Создаем README для пользователя
    create_readme(system)
    return True


def create_readme(system):
    """Создать файл README для пользователя"""

    readme_content = f"""
# Wikipedia AI Assistant

## Инструкция по запуску

{'### Для Windows' if system == 'Windows' else '### Для macOS' if system == 'Darwin' else '### Для Linux'}

1. Запустите файл: `dist/{'WikipediaAI.exe' if system == 'Windows' else 'WikipediaAI.app' if system == 'Darwin' else 'wikipedia-ai'}`

2. При первом запуске программа скачает необходимые данные NLTK (это может занять 1-2 минуты).

3. После загрузки данных откроется основное окно приложения.

## Возможные проблемы и решения

### 1. Отсутствуют библиотеки
Если при запуске появляются ошибки о missing libraries:
- Установите Python 3.8 или выше
- Установите Microsoft Visual C++ Redistributable (для Windows)

### 2. Ошибка NLTK данных
Если возникают ошибки загрузки данных NLTK:
- Проверьте подключение к интернету
- Запустите программу от имени администратора
- Или запустите в командной строке:
  ```bash
  python -c "import nltk; nltk.download('punkt_tab'); nltk.download('stopwords')"""