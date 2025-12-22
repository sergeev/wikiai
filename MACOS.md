# Сборка для macOS
``` bash
 pyinstaller --onefile --windowed --name="WikipediaAI" main.py
```

# Создание .app пакета
``` bash
pyinstaller --windowed --name="WikipediaAI" main.py
```

# После сборки может потребоваться:
# 1. Права на выполнение
``` bash
chmod +x dist/WikipediaAI.app/Contents/MacOS/WikipediaAI
```

# 2. Если приложение заблокировано macOS:
``` bash
xattr -cr dist/WikipediaAI.app
```