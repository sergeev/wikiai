import sys
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import sqlite3
import json
import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer
import threading
from datetime import datetime
import wikipedia
import requests
from bs4 import BeautifulSoup
import pickle
import os
from collections import defaultdict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import warnings

warnings.filterwarnings('ignore')
import html
from urllib.parse import quote
import time

def resource_path(relative_path):
    """ Получить абсолютный путь к ресурсу для PyInstaller """
    try:
        # PyInstaller создает временную папку и сохраняет путь в _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Проверка и загрузка NLTK данных
try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab')
    nltk.download('stopwords')


class ModernWikipediaAI:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("🤖 Modern Wikipedia AI Assistant")
        self.window.geometry("1400x850")
        self.window.configure(bg="#0a192f")

        # Создаем папку для данных, если её нет
        self.data_dir = os.path.join(os.path.expanduser("~"), ".wikipedia_ai")
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

        # Путь к файлу базы знаний
        self.kb_path = os.path.join(self.data_dir, "knowledge_base.json")

        # Установка русского языка для Wikipedia
        wikipedia.set_lang("ru")

        # Настройка цветовой схемы (синяя тема)
        self.colors = {
            'primary': '#0a192f',
            'secondary': '#112240',
            'accent': '#64ffda',
            'light': '#ccd6f6',
            'lighter': '#a8b2d1',
            'card': '#112240',
            'success': '#64ffda',
            'warning': '#f9d71c',
            'error': '#ff6b6b',
            'user_msg': '#1e40af',
            'ai_msg': '#1e3a8a',
        }

        # База знаний
        self.knowledge_base = {}
        self.load_knowledge_base()

        # NLP компоненты для русского
        self.stemmer = SnowballStemmer("russian")
        self.stop_words_ru = set(stopwords.words('russian'))

        # TF-IDF векторная модель
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='russian')

        # История диалога
        self.conversation_history = []

        # Создаем интерфейс
        self.create_interface()

        # Начальное сообщение
        self.add_to_chat("🤖 Привет! Я современный Wikipedia AI Assistant с русским интерфейсом.\n"
                         "Я могу искать информацию в русской Википедии и отвечать на ваши вопросы.")

    def create_interface(self):
        """Создать современный интерфейс"""
        # Заголовок
        header_frame = tk.Frame(self.window, bg=self.colors['primary'], height=100)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)

        # Текст заголовка
        tk.Label(header_frame, text="🌐 MODERN WIKIPEDIA AI",
                 font=("Arial", 28, "bold"),
                 bg=self.colors['primary'],
                 fg=self.colors['accent']).pack(pady=(20, 5))

        tk.Label(header_frame, text="Интеллектуальный помощник с русской Википедией",
                 font=("Arial", 12),
                 bg=self.colors['primary'],
                 fg=self.colors['lighter']).pack()

        # Основная область с разделением
        main_container = tk.Frame(self.window, bg=self.colors['primary'])
        main_container.pack(fill="both", expand=True, padx=20, pady=10)

        # Левая панель (фиксированная ширина)
        left_panel = tk.Frame(main_container, bg=self.colors['secondary'])
        left_panel.pack(side="left", fill="y")

        # Правая панель
        right_panel = tk.Frame(main_container, bg=self.colors['primary'])
        right_panel.pack(side="right", fill="both", expand=True)

        # Создаем левую панель
        self.create_left_panel(left_panel)

        # Создаем правую панель
        self.create_right_panel(right_panel)

    def create_left_panel(self, parent):
        """Создать левую панель управления"""
        # Поисковая панель
        search_frame = tk.Frame(parent, bg=self.colors['secondary'], padx=15, pady=15)
        search_frame.pack(fill="x", pady=(0, 10))

        tk.Label(search_frame, text="🔍 Поиск в Википедии",
                 font=("Arial", 12, "bold"),
                 bg=self.colors['secondary'],
                 fg=self.colors['accent']).pack(anchor="w", pady=(0, 10))

        # Поле поиска
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=self.search_var,
                                font=("Arial", 11),
                                bg="#1d2b4f", fg=self.colors['light'],
                                insertbackground=self.colors['accent'],
                                relief="flat", width=30)
        search_entry.pack(fill="x", pady=(0, 10))
        search_entry.bind("<Return>", lambda e: self.search_wikipedia())

        # Кнопка поиска
        search_btn = tk.Button(search_frame, text="🔍 Найти",
                               command=self.search_wikipedia,
                               bg=self.colors['accent'], fg=self.colors['primary'],
                               font=("Arial", 11, "bold"),
                               relief="flat", cursor="hand2",
                               padx=20, pady=5)
        search_btn.pack()

        # Быстрый поиск
        tk.Label(search_frame, text="Быстрый поиск:",
                 font=("Arial", 10),
                 bg=self.colors['secondary'],
                 fg=self.colors['lighter']).pack(anchor="w", pady=(15, 5))

        quick_frame = tk.Frame(search_frame, bg=self.colors['secondary'])
        quick_frame.pack(fill="x")

        quick_topics = ["Искусственный интеллект", "История", "Наука", "Технологии"]
        for topic in quick_topics:
            btn = tk.Button(quick_frame, text=topic,
                            command=lambda t=topic: self.quick_search(t),
                            bg="#1d2b4f", fg=self.colors['light'],
                            font=("Arial", 9),
                            relief="flat", cursor="hand2")
            btn.pack(fill="x", pady=2)

        # Результаты поиска
        results_frame = tk.Frame(parent, bg=self.colors['secondary'], padx=15, pady=15)
        results_frame.pack(fill="both", expand=True, pady=(0, 10))

        tk.Label(results_frame, text="📚 Найденные статьи",
                 font=("Arial", 12, "bold"),
                 bg=self.colors['secondary'],
                 fg=self.colors['accent']).pack(anchor="w", pady=(0, 10))

        # Список результатов
        self.results_listbox = tk.Listbox(results_frame,
                                          bg="#1d2b4f",
                                          fg=self.colors['light'],
                                          font=("Arial", 10),
                                          selectbackground=self.colors['accent'],
                                          selectforeground=self.colors['primary'],
                                          relief="flat",
                                          height=12)

        scrollbar = tk.Scrollbar(results_frame, orient="vertical")
        self.results_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.results_listbox.yview)

        self.results_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.results_listbox.bind("<<ListboxSelect>>", self.on_topic_select)

        # Кнопки действий
        actions_frame = tk.Frame(parent, bg=self.colors['secondary'], padx=15, pady=15)
        actions_frame.pack(fill="x", pady=(0, 10))

        tk.Label(actions_frame, text="⚡ Действия",
                 font=("Arial", 12, "bold"),
                 bg=self.colors['secondary'],
                 fg=self.colors['accent']).pack(anchor="w", pady=(0, 10))

        action_buttons = [
            ("📥 Добавить в базу", self.add_selected_to_kb),
            ("🧹 Очистить базу", self.clear_knowledge_base),
            ("💾 Экспорт данных", self.export_knowledge_base),
            ("🔄 Обновить", self.update_knowledge_base_display),
        ]

        for text, command in action_buttons:
            btn = tk.Button(actions_frame, text=text,
                            command=command,
                            bg=self.colors['accent'], fg=self.colors['primary'],
                            font=("Arial", 10, "bold"),
                            relief="flat", cursor="hand2",
                            padx=20, pady=8)
            btn.pack(fill="x", pady=5)

        # Статистика
        stats_frame = tk.Frame(parent, bg=self.colors['secondary'], padx=15, pady=15)
        stats_frame.pack(fill="x")

        tk.Label(stats_frame, text="📊 Статистика",
                 font=("Arial", 12, "bold"),
                 bg=self.colors['secondary'],
                 fg=self.colors['accent']).pack(anchor="w", pady=(0, 10))

        self.stats_label = tk.Label(stats_frame,
                                    text="База знаний: 0 статей\nЗагружено: 0 КБ",
                                    font=("Arial", 10),
                                    bg=self.colors['secondary'],
                                    fg=self.colors['lighter'],
                                    justify="left")
        self.stats_label.pack(anchor="w")

    def create_right_panel(self, parent):
        """Создать правую панель (чат и информация)"""
        # Вкладки
        style = ttk.Style()
        style.configure("Custom.TNotebook", background=self.colors['secondary'])
        style.configure("Custom.TNotebook.Tab",
                        background=self.colors['secondary'],
                        foreground=self.colors['lighter'])
        style.map("Custom.TNotebook.Tab",
                  background=[("selected", self.colors['accent'])],
                  foreground=[("selected", self.colors['primary'])])

        self.notebook = ttk.Notebook(parent, style="Custom.TNotebook")
        self.notebook.pack(fill="both", expand=True)

        # Вкладка 1: Чат
        chat_tab = tk.Frame(self.notebook, bg=self.colors['primary'])
        self.notebook.add(chat_tab, text="💬 Чат с ИИ")

        # Чат
        chat_container = tk.Frame(chat_tab, bg=self.colors['primary'])
        chat_container.pack(fill="both", expand=True, padx=10, pady=10)

        # История чата
        self.chat_frame = tk.Frame(chat_container, bg=self.colors['primary'])
        self.chat_frame.pack(fill="both", expand=True)

        # Canvas для прокрутки чата
        self.chat_canvas = tk.Canvas(self.chat_frame, bg=self.colors['primary'],
                                     highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.chat_frame, orient="vertical",
                                  command=self.chat_canvas.yview)
        self.chat_scrollable_frame = tk.Frame(self.chat_canvas, bg=self.colors['primary'])

        self.chat_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all"))
        )

        self.chat_canvas.create_window((0, 0), window=self.chat_scrollable_frame,
                                       anchor="nw")
        self.chat_canvas.configure(yscrollcommand=scrollbar.set)

        self.chat_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Поле ввода
        input_frame = tk.Frame(chat_container, bg=self.colors['primary'])
        input_frame.pack(fill="x", pady=(10, 0))

        self.input_var = tk.StringVar()
        self.input_entry = tk.Entry(input_frame,
                                    textvariable=self.input_var,
                                    font=("Arial", 12),
                                    bg="#1d2b4f", fg=self.colors['light'],
                                    insertbackground=self.colors['accent'],
                                    relief="flat")
        self.input_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.input_entry.bind("<Return>", lambda e: self.process_query())

        send_btn = tk.Button(input_frame, text="Отправить →",
                             command=self.process_query,
                             bg=self.colors['accent'], fg=self.colors['primary'],
                             font=("Arial", 11, "bold"),
                             relief="flat", cursor="hand2",
                             padx=25, pady=8)
        send_btn.pack(side="right")

        # Вкладка 2: Статья
        article_tab = tk.Frame(self.notebook, bg=self.colors['primary'])
        self.notebook.add(article_tab, text="📖 Читать статью")

        self.article_text = scrolledtext.ScrolledText(article_tab,
                                                      wrap=tk.WORD,
                                                      font=("Arial", 11),
                                                      bg=self.colors['secondary'],
                                                      fg=self.colors['light'],
                                                      insertbackground=self.colors['accent'],
                                                      relief="flat",
                                                      borderwidth=0)
        self.article_text.pack(fill="both", expand=True, padx=10, pady=10)
        self.article_text.config(state="disabled")

        # Вкладка 3: База знаний
        kb_tab = tk.Frame(self.notebook, bg=self.colors['primary'])
        self.notebook.add(kb_tab, text="📚 Моя база знаний")

        self.kb_text = scrolledtext.ScrolledText(kb_tab,
                                                 wrap=tk.WORD,
                                                 font=("Arial", 10),
                                                 bg=self.colors['secondary'],
                                                 fg=self.colors['light'],
                                                 relief="flat",
                                                 borderwidth=0)
        self.kb_text.pack(fill="both", expand=True, padx=10, pady=10)
        self.kb_text.config(state="disabled")

    def add_message_to_chat(self, message, is_user=False):
        """Добавить сообщение в чат"""
        message_frame = tk.Frame(self.chat_scrollable_frame,
                                 bg=self.colors['primary'])
        message_frame.pack(fill="x", padx=10, pady=5)

        # Аватар
        avatar_color = self.colors['user_msg'] if is_user else self.colors['ai_msg']
        avatar_text = "👤" if is_user else "🤖"

        avatar_frame = tk.Frame(message_frame, bg=avatar_color, width=40, height=40)
        avatar_frame.pack(side="left", padx=(0, 10))
        avatar_frame.pack_propagate(False)

        avatar_label = tk.Label(avatar_frame, text=avatar_text,
                                font=("Arial", 16),
                                bg=avatar_color, fg="white")
        avatar_label.pack(expand=True)

        # Текст сообщения
        text_frame = tk.Frame(message_frame, bg=self.colors['secondary'],
                              relief="flat", borderwidth=0)
        text_frame.pack(side="right", fill="x", expand=True)

        message_label = tk.Label(text_frame, text=message,
                                 font=("Arial", 11),
                                 bg=self.colors['secondary'],
                                 fg=self.colors['light'],
                                 wraplength=600,
                                 justify="left",
                                 anchor="w")
        message_label.pack(anchor="w", padx=15, pady=10)

        # Прокрутка вниз
        self.chat_canvas.yview_moveto(1.0)

    def add_to_chat(self, message, is_user=False):
        """Потокобезопасное добавление в чат"""
        self.window.after(0, self.add_message_to_chat, message, is_user)

    def search_wikipedia(self):
        """Поиск в русской Википедии"""
        query = self.search_var.get().strip()
        if not query:
            self.add_to_chat("⚠️ Введите поисковый запрос", is_user=False)
            return

        self.add_to_chat(f"🔍 Ищу в Википедии: {query}", is_user=True)

        try:
            # Очищаем список
            self.results_listbox.delete(0, tk.END)

            # Ищем в русской Википедии
            wikipedia.set_lang("ru")
            search_results = wikipedia.search(query, results=10)

            if not search_results:
                self.add_to_chat("❌ По вашему запросу ничего не найдено", is_user=False)
                return

            # Добавляем результаты
            for result in search_results:
                self.results_listbox.insert(tk.END, result)

            self.add_to_chat(f"✅ Найдено {len(search_results)} статей", is_user=False)

        except wikipedia.exceptions.DisambiguationError as e:
            self.results_listbox.delete(0, tk.END)
            for option in e.options[:10]:
                self.results_listbox.insert(tk.END, option)

            self.add_to_chat("🔍 Уточните запрос. Выберите вариант из списка:", is_user=False)

        except Exception as e:
            self.add_to_chat(f"❌ Ошибка поиска: {str(e)}", is_user=False)

    def quick_search(self, topic):
        """Быстрый поиск"""
        self.search_var.set(topic)
        self.search_wikipedia()

    def on_topic_select(self, event):
        """Обработка выбора темы"""
        selection = self.results_listbox.curselection()
        if not selection:
            return

        topic = self.results_listbox.get(selection[0])
        self.load_wikipedia_article(topic)

    def load_wikipedia_article(self, topic):
        """Загрузить статью из Википедии"""
        self.add_to_chat(f"📖 Загружаю статью: {topic}", is_user=False)

        try:
            # Получаем страницу на русском
            wikipedia.set_lang("ru")
            page = wikipedia.page(topic, auto_suggest=True)

            # Отображаем в текстовом поле
            self.article_text.config(state="normal")
            self.article_text.delete(1.0, tk.END)

            # Форматируем статью
            article_content = f"{'═' * 70}\n"
            article_content += f"📚 {page.title}\n"
            article_content += f"{'═' * 70}\n\n"

            # Берем начало статьи
            content = page.content[:3000]

            # Улучшаем форматирование
            paragraphs = content.split('\n\n')
            for para in paragraphs[:8]:
                if para.strip() and len(para.strip()) > 30:
                    article_content += para.strip() + "\n\n"

            article_content += f"\n{'─' * 70}\n"
            article_content += f"🔗 Полная статья: {page.url}\n"

            self.article_text.insert(1.0, article_content)
            self.article_text.config(state="disabled")

            # Переключаем на вкладку статьи
            self.notebook.select(1)

            # Сохраняем текущую статью
            self.current_article = {
                'title': page.title,
                'content': page.content,
                'summary': page.summary,
                'url': page.url
            }

            self.add_to_chat(f"✅ Статья '{page.title}' загружена", is_user=False)

        except wikipedia.exceptions.PageError:
            self.add_to_chat(f"❌ Страница '{topic}' не найдена", is_user=False)
        except Exception as e:
            self.add_to_chat(f"❌ Ошибка загрузки: {str(e)}", is_user=False)

    def add_selected_to_kb(self):
        """Добавить статью в базу знаний"""
        selection = self.results_listbox.curselection()
        if not selection:
            self.add_to_chat("⚠️ Выберите статью из списка", is_user=False)
            return

        topic = self.results_listbox.get(selection[0])

        try:
            # Получаем статью
            wikipedia.set_lang("ru")
            page = wikipedia.page(topic, auto_suggest=True)

            # Добавляем в базу знаний
            self.knowledge_base[page.title] = {
                'content': page.content,
                'summary': page.summary,
                'url': page.url,
                'language': 'ru',
                'timestamp': datetime.now().isoformat()
            }

            # Обновляем базу
            self.update_knowledge_base_display()

            self.add_to_chat(f"✅ Статья '{page.title}' добавлена в базу знаний", is_user=False)

        except Exception as e:
            self.add_to_chat(f"❌ Ошибка добавления: {str(e)}", is_user=False)

    def process_query(self):
        """Обработать запрос пользователя"""
        query = self.input_var.get().strip()
        if not query:
            return

        # Добавляем запрос в чат
        self.add_to_chat(query, is_user=True)
        self.input_var.set("")

        # Обрабатываем в отдельном потоке
        threading.Thread(target=self.generate_response,
                         args=(query,), daemon=True).start()

    def generate_response(self, query):
        """Сгенерировать ответ"""
        try:
            # Проверяем команды
            response = self.check_russian_commands(query)
            if response:
                self.add_to_chat(response, is_user=False)
                return

            # Ищем в базе знаний
            response = self.search_in_knowledge_base(query)

            # Если не нашли, ищем в Википедии
            if not response or "не знаю" in response.lower():
                wiki_response = self.search_in_wikipedia_direct(query)
                if wiki_response:
                    response = wiki_response

            self.add_to_chat(response, is_user=False)

        except Exception as e:
            self.add_to_chat(f"❌ Ошибка: {str(e)}", is_user=False)

    def check_russian_commands(self, query):
        """Проверка русских команд"""
        query_lower = query.lower()

        commands = {
            'привет': "Привет! Чем могу помочь? 😊",
            'здравствуй': "Здравствуйте! Задавайте вопросы.",
            'как дела': "Отлично! Готов помочь вам.",
            'что ты умеешь': "Я могу искать статьи в Википедии и отвечать на вопросы.",
            'спасибо': "Пожалуйста! Рад помочь!",
            'помощь': "Задавайте вопросы на любые темы!",
            'очистить': "Чат очищен!",
            'база знаний': f"В базе {len(self.knowledge_base)} статей.",
        }

        for cmd, response in commands.items():
            if cmd in query_lower:
                return response

        return None

    def search_in_knowledge_base(self, query):
        """Поиск в базе знаний"""
        if not self.knowledge_base:
            return "База знаний пуста. Добавьте статьи из Википедии."

        # Простой поиск по заголовкам
        for title, data in self.knowledge_base.items():
            if query.lower() in title.lower():
                response = f"📚 **Нашел в базе знаний:**\n"
                response += f"**Статья:** {title}\n\n"
                response += f"**Кратко:** {data['summary'][:150]}...\n\n"
                response += f"📖 Откройте вкладку 'База знаний' для подробностей"
                return response

        return "В базе знаний нет информации по этому вопросу."

    def search_in_wikipedia_direct(self, query):
        """Прямой поиск в Википедии"""
        try:
            # Ищем на русском
            wikipedia.set_lang("ru")

            try:
                page = wikipedia.page(query, auto_suggest=True)

                response = f"🔍 **Нашел в Википедии:**\n"
                response += f"**Статья:** {page.title}\n\n"
                response += f"{page.summary}\n\n"
                response += f"🔗 **Ссылка:** {page.url}"

                return response

            except wikipedia.exceptions.DisambiguationError as e:
                options = e.options[:5]
                response = f"🔍 **Уточните запрос:**\n"
                response += "Найдено несколько вариантов:\n\n"
                for i, option in enumerate(options, 1):
                    response += f"{i}. {option}\n"
                return response

        except Exception as e:
            return f"❌ Не удалось найти информацию."

    def update_knowledge_base_display(self):
        """Обновить отображение базы знаний"""
        # Сохраняем базу
        self.save_knowledge_base()

        # Обновляем статистику
        total_size = sum(len(str(v)) for v in self.knowledge_base.values()) / 1024
        self.stats_label.config(
            text=f"База знаний: {len(self.knowledge_base)} статей\n"
                 f"Загружено: {total_size:.1f} КБ"
        )

        # Обновляем текст базы знаний
        self.kb_text.config(state="normal")
        self.kb_text.delete(1.0, tk.END)

        if self.knowledge_base:
            kb_info = f"{'═' * 70}\n"
            kb_info += f"📚 БАЗА ЗНАНИЙ ({len(self.knowledge_base)} статей)\n"
            kb_info += f"{'═' * 70}\n\n"

            for i, (title, data) in enumerate(self.knowledge_base.items(), 1):
                kb_info += f"{i}. **{title}**\n"
                kb_info += f"   📝 {data['summary'][:100]}...\n"
                kb_info += f"   📅 {data['timestamp'][:10]}\n"
                kb_info += f"{'─' * 60}\n"
        else:
            kb_info = "📭 База знаний пуста\n\n"
            kb_info += "Добавьте статьи из Википедии!"

        self.kb_text.insert(1.0, kb_info)
        self.kb_text.config(state="disabled")

    def clear_knowledge_base(self):
        """Очистить базу знаний"""
        if messagebox.askyesno("Очистка базы",
                               "Вы уверены, что хотите очистить базу знаний?"):
            self.knowledge_base = {}
            self.update_knowledge_base_display()
            self.add_to_chat("✅ База знаний очищена", is_user=False)

    def export_knowledge_base(self):
        """Экспортировать базу знаний"""
        try:
            filename = f"wikipedia_kb_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.knowledge_base, f, ensure_ascii=False, indent=2)

            self.add_to_chat(f"✅ База знаний экспортирована в {filename}", is_user=False)
        except Exception as e:
            self.add_to_chat(f"❌ Ошибка экспорта: {str(e)}", is_user=False)

    def load_knowledge_base(self):
        """Загрузить базу знаний"""
        try:
            if os.path.exists("knowledge_base.json"):
                with open("knowledge_base.json", 'r', encoding='utf-8') as f:
                    self.knowledge_base = json.load(f)
        except Exception as e:
            print(f"Ошибка загрузки базы знаний: {e}")

    def save_knowledge_base(self):
        """Сохранить базу знаний"""
        try:
            with open("knowledge_base.json", 'w', encoding='utf-8') as f:
                json.dump(self.knowledge_base, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения базы знаний: {e}")

    def ensure_nltk_data(self):
        """Проверить и загрузить данные NLTK при необходимости"""
        try:
            nltk.data.find('tokenizers/punkt_tab')
            nltk.data.find('corpora/stopwords')
            return True
        except LookupError:
            self.add_to_chat("📥 Загружаю необходимые данные NLTK...", is_user=False)
            nltk.download('punkt_tab', quiet=True)
            nltk.download('stopwords', quiet=True)
            self.add_to_chat("✅ Данные NLTK загружены", is_user=False)
            return True
        except Exception as e:
            self.add_to_chat(f"❌ Ошибка загрузки данных NLTK: {e}", is_user=False)
            return False

    def run(self):
        """Запустить приложение"""
        self.window.mainloop()


def main():
    """Главная функция"""
    print("🚀 Запуск Modern Wikipedia AI Assistant...")
    print("🌐 Язык: Русский")

    # Проверка библиотек
    try:
        import wikipedia
        import nltk
        print("✅ Все библиотеки установлены")
    except ImportError as e:
        print(f"❌ Отсутствует библиотека: {e}")
        print("\nУстановите недостающие библиотеки:")
        print("pip install wikipedia-api nltk scikit-learn beautifulsoup4 requests numpy")
        return

    # Запуск приложения
    app = ModernWikipediaAI()
    app.run()


if __name__ == "__main__":
    main()

