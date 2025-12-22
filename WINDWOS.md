# Создайте иконку (опционально)
# Сохраните как icon.ico в папке проекта
# Сборка в один файл
```bash 
pyinstaller --onefile --windowed --icon=icon.ico --name="WikipediaAI" main.py
```
# Сборка без icon
``` bash
pyinstaller --onefile --windowed --name="WikipediaAI" main.py
```
# ИЛИ сборка в папку (проще для отладки)
``` bash
 pyinstaller --windowed --icon=icon.ico --name="WikipediaAI" main.py
```
# Добавьте дополнительные данные, если нужно
``` bash
pyinstaller --onefile --windowed --add-data "nltk_data;nltk_data" --name="WikipediaAI" main.py
```
