#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Модуль с графическим интерфейсом для работы с журналами.
"""

import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox

# Импорт наших модулей
from db_manager import JournalDatabase
from parser_wrapper import ParserWrapper


class JournalAnalyzerApp:
    """
    Основной класс графического интерфейса
    """
    
    def __init__(self, root):
        """
        Инициализация интерфейса
        
        Args:
            root: Корневой виджет tkinter
        """
        self.root = root
        self.db = JournalDatabase()
        self.parser = ParserWrapper()
        
        # Настройка стилей
        self._setup_styles()
        
        # Переменные для фильтров
        self.vak_categories = {
            "1": tk.BooleanVar(value=False),
            "2": tk.BooleanVar(value=False),
            "3": tk.BooleanVar(value=False),
            "none": tk.BooleanVar(value=False)
        }
        
        self.white_levels = {
            "1": tk.BooleanVar(value=False),
            "2": tk.BooleanVar(value=False),
            "3": tk.BooleanVar(value=False),
            "4": tk.BooleanVar(value=False),
            "none": tk.BooleanVar(value=False)
        }
        
        self.rsci_var = tk.StringVar(value="all")
        
        # Текущие отфильтрованные журналы
        self.filtered_journals = []
        
        # Создание интерфейса
        self._create_ui()
        
        # Заполнение списка журналов
        self.update_journal_list()
    
    def _setup_styles(self):
        """
        Настройка стилей для виджетов
        """
        style = ttk.Style()
        
        # Основной цвет приложения
        primary_color = "#3498db"  # Голубой
        secondary_color = "#f5f5f5"  # Светло-серый
        
        # Настройка стиля окна
        self.root.configure(bg=secondary_color)
        
        # Настройка стиля кнопок
        style.configure(
            "TButton",
            font=("Arial", 10, "bold"),
            padding=5
        )
        
        # Стиль для основной кнопки действия
        style.configure(
            "Accent.TButton",
            font=("Arial", 10, "bold"),
            padding=5
        )
        
        # Пробуем улучшить внешний вид кнопок для Windows
        if os.name == 'nt':  # Windows
            style.theme_use('vista')
        
        # Стиль для меток
        style.configure(
            "TLabel",
            font=("Arial", 9),
            background=secondary_color
        )
        
        # Стиль для фреймов
        style.configure(
            "TFrame",
            background=secondary_color
        )
        
        # Стиль для LabelFrame
        style.configure(
            "TLabelframe",
            font=("Arial", 9),
            background=secondary_color,
            foreground=primary_color
        )
        style.configure(
            "TLabelframe.Label",
            font=("Arial", 9, "bold"),
            background=secondary_color,
            foreground=primary_color
        )
        
        # Стиль для чекбоксов
        style.configure(
            "TCheckbutton",
            font=("Arial", 9),
            background=secondary_color
        )
        
        # Стиль для радиокнопок
        style.configure(
            "TRadiobutton",
            font=("Arial", 9),
            background=secondary_color
        )
        
        # Стиль для статусбара
        style.configure(
            "Status.TLabel",
            font=("Arial", 9),
            padding=2,
            background="#f0f0f0",
            relief=tk.SUNKEN
        )
        
        # Стиль для заголовка
        style.configure(
            "Title.TLabel",
            font=("Arial", 12, "bold"),
            foreground=primary_color,
            background=secondary_color
        )
        
        # Стиль для статистики
        style.configure(
            "Stats.TLabel",
            font=("Arial", 9, "bold"),
            foreground="#555555",
            background=secondary_color
        )

    def _on_filter_changed(self, event):
        """Обработчик изменения фильтров"""
        self.update_journal_list()
    
    def _create_ui(self):
        """
        Создание элементов интерфейса
        """
        # Создание главного фрейма
        main_frame = ttk.Frame(self.root, padding=5)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Верхняя панель с заголовком
        title_label = ttk.Label(
            main_frame, 
            text="Фильтр журналов 2.3.4",
            style="Title.TLabel"
        )
        title_label.pack(pady=5)
        
        # Фрейм для фильтров
        filter_frame = ttk.LabelFrame(
            main_frame, 
            text="Параметры фильтрации", 
            padding=5
        )
        filter_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Создаем три колонки для фильтров
        vak_frame = ttk.LabelFrame(
            filter_frame, 
            text="Категории ВАК", 
            padding=5
        )
        vak_frame.grid(row=0, column=0, padx=5, pady=5, sticky=tk.NSEW)
        
        white_frame = ttk.LabelFrame(
            filter_frame, 
            text="Белый список", 
            padding=5
        )
        white_frame.grid(row=0, column=1, padx=5, pady=5, sticky=tk.NSEW)
        
        rsci_frame = ttk.LabelFrame(
            filter_frame, 
            text="RSCI", 
            padding=5
        )
        rsci_frame.grid(row=0, column=2, padx=5, pady=5, sticky=tk.NSEW)
        
        # Настраиваем веса для колонок
        filter_frame.columnconfigure(0, weight=1)
        filter_frame.columnconfigure(1, weight=1)
        filter_frame.columnconfigure(2, weight=1)
        
        # Добавляем чекбоксы для категорий ВАК
        ttk.Checkbutton(
            vak_frame, 
            text="Категория 1", 
            variable=self.vak_categories["1"]
        ).pack(anchor=tk.W, pady=1)
        
        ttk.Checkbutton(
            vak_frame, 
            text="Категория 2", 
            variable=self.vak_categories["2"]
        ).pack(anchor=tk.W, pady=1)
        
        ttk.Checkbutton(
            vak_frame, 
            text="Категория 3", 
            variable=self.vak_categories["3"]
        ).pack(anchor=tk.W, pady=1)
        
        ttk.Checkbutton(
            vak_frame, 
            text="Без категории", 
            variable=self.vak_categories["none"]
        ).pack(anchor=tk.W, pady=1)
        
        # Добавляем чекбоксы для белого списка
        ttk.Checkbutton(
            white_frame, 
            text="Уровень 1", 
            variable=self.white_levels["1"]
        ).pack(anchor=tk.W, pady=1)
        
        ttk.Checkbutton(
            white_frame, 
            text="Уровень 2", 
            variable=self.white_levels["2"]
        ).pack(anchor=tk.W, pady=1)
        
        ttk.Checkbutton(
            white_frame, 
            text="Уровень 3", 
            variable=self.white_levels["3"]
        ).pack(anchor=tk.W, pady=1)
        
        ttk.Checkbutton(
            white_frame, 
            text="Уровень 4", 
            variable=self.white_levels["4"]
        ).pack(anchor=tk.W, pady=1)
        
        ttk.Checkbutton(
            white_frame, 
            text="Не входит", 
            variable=self.white_levels["none"]
        ).pack(anchor=tk.W, pady=1)
        
        # Добавляем радиокнопки для RSCI
        ttk.Radiobutton(
            rsci_frame, 
            text="Все", 
            variable=self.rsci_var, 
            value="all"
        ).pack(anchor=tk.W, pady=1)
        
        ttk.Radiobutton(
            rsci_frame, 
            text="Да", 
            variable=self.rsci_var, 
            value="yes"
        ).pack(anchor=tk.W, pady=1)
        
        ttk.Radiobutton(
            rsci_frame, 
            text="Нет", 
            variable=self.rsci_var, 
            value="no"
        ).pack(anchor=tk.W, pady=1)
        
        # Фрейм для статистики и кнопок
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Создаем переменные для статистики
        self.total_journals_var = tk.StringVar(value="Всего: 0")
        self.white_list_journals_var = tk.StringVar(value="В БС: 0")
        self.rsci_journals_var = tk.StringVar(value="В RSCI: 0")
        
        # Статистика и кнопки в одной строке
        stats_frame = ttk.LabelFrame(
            bottom_frame, 
            text="Статистика", 
            padding=3
        )
        stats_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(
            stats_frame, 
            textvariable=self.total_journals_var,
            style="Stats.TLabel"
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(
            stats_frame, 
            textvariable=self.white_list_journals_var,
            style="Stats.TLabel"
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(
            stats_frame, 
            textvariable=self.rsci_journals_var,
            style="Stats.TLabel"
        ).pack(side=tk.LEFT, padx=5)
        
        # Кнопки
        button_frame = ttk.Frame(bottom_frame)
        button_frame.pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            button_frame, 
            text="Обновить", 
            command=self.start_update_data,
            width=17
        ).pack(side=tk.LEFT, padx=2, pady=5)
        
        ttk.Button(
            button_frame, 
            text="Экспорт в Excel", 
            command=self.filter_and_export,
            width=16,
            style="Accent.TButton"
        ).pack(side=tk.LEFT, padx=2, pady=5)
        
        # Статусбар
        self.status_var = tk.StringVar(value="Готов к работе")
        status_bar = ttk.Label(
            main_frame, 
            textvariable=self.status_var, 
            style="Status.TLabel",
            anchor=tk.W
        )
        status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=(5, 0))
    
    def update_journal_list(self):
        """
        Обновление статистики журналов
        """
        # Получаем все журналы
        all_journals = self.db.get_journals()
        
        # Считаем статистику
        total = len(all_journals)
        white_list_count = sum(
            1 for j in all_journals 
            if j.get("white_level") != "none"
        )
        rsci_count = sum(1 for j in all_journals if j.get("RSCI"))
        
        # Обновляем переменные статистики
        self.total_journals_var.set(f"Всего: {total}")
        self.white_list_journals_var.set(f"В БС: {white_list_count}")
        self.rsci_journals_var.set(f"В RSCI: {rsci_count}")
        
        # Обновляем статус
        self.status_var.set(f"База содержит {total} журналов")
    
    def _get_selected_filters(self):
        """
        Получение выбранных фильтров
        
        Returns:
            dict: Словарь с выбранными фильтрами
        """
        # Получаем выбранные категории ВАК
        vak_selected = [
            category for category, var in self.vak_categories.items() 
            if var.get()
        ]
        
        # Получаем выбранные уровни белого списка
        white_selected = [
            level for level, var in self.white_levels.items() 
            if var.get()
        ]
        
        # Получаем значение RSCI
        rsci_value = self.rsci_var.get()
        rsci_filter = None
        if rsci_value == "yes":
            rsci_filter = True
        elif rsci_value == "no":
            rsci_filter = False
        
        return {
            "vak_categories": vak_selected,
            "white_levels": white_selected,
            "rsci": rsci_filter
        }
    
    def filter_and_export(self):
        """
        Фильтрация журналов и экспорт в Excel
        """
        # Проверяем, существует ли файл с данными
        if not self.db.journals:
            messagebox.showwarning(
                "Нет данных", 
                "База журналов пуста. Необходимо обновить базу."
            )
            return
        
        # Получаем выбранные фильтры
        filters = self._get_selected_filters()
        
        # Если ничего не выбрано, выводим предупреждение
        if not any([
            filters["vak_categories"], 
            filters["white_levels"], 
            filters["rsci"] is not None
        ]):
            messagebox.showwarning(
                "Нет фильтров", 
                "Выберите хотя бы один параметр для фильтрации."
            )
            return
        
        # Фильтруем журналы
        filtered_journals = self.db.filter_journals(
            vak_categories=filters["vak_categories"],
            white_levels=filters["white_levels"],
            in_rsci=filters["rsci"]
        )
        
        # Проверяем, что есть результаты фильтрации
        if not filtered_journals:
            messagebox.showinfo(
                "Результаты фильтрации", 
                "По заданным критериям журналы не найдены."
            )
            return
        
        # Путь к файлу Excel
        excel_path = os.path.join(os.getcwd(), "vak_journals_filtered.xlsx")
        
        # Экспортируем в Excel
        if self.db.export_to_excel(filtered_journals, excel_path):
            # Показываем сообщение об успешном экспорте
            msg = (
                f"Отфильтровано {len(filtered_journals)} журналов.\n"
            )
            messagebox.showinfo("Экспорт завершен", msg)
            
            # Открываем файл
            if os.name == 'nt':
                os.startfile(excel_path)
        else:
            # Показываем сообщение об ошибке
            messagebox.showerror(
                "Ошибка экспорта", 
                "Не удалось экспортировать данные."
            )
    
    def start_update_data(self):
        """
        Запускает обновление данных в отдельном потоке
        """
        # Проверяем, не запущено ли уже обновление
        is_running = (hasattr(self, "update_thread") and 
                      self.update_thread.is_alive())
        
        if is_running:
            messagebox.showinfo(
                "Обновление", 
                "Обновление уже запущено"
            )
            return
        
        # Запрашиваем подтверждение
        confirm_msg = (
            "Обновить базу журналов? "
        )
        if not messagebox.askyesno("Обновление", confirm_msg):
            return
        
        # Обновляем статус
        self.status_var.set("Обновление данных...")
        
        # Запускаем обновление в отдельном потоке
        self.update_thread = threading.Thread(
            target=self._update_data_thread,
            daemon=True
        )
        self.update_thread.start()
    
    def _update_data_thread(self):
        """
        Выполняет обновление данных в отдельном потоке
        """
        try:
            # Обновляем данные
            result = self.parser.run_parser()
            
            # Обновляем интерфейс в основном потоке
            self.root.after(0, self._update_completed, result)
        except Exception as e:
            # Обрабатываем ошибки в основном потоке
            self.root.after(0, self._update_failed, str(e))
    
    def _update_completed(self, result):
        """
        Обработка завершения обновления данных
        
        Args:
            result: Результат выполнения обновления
        """
        # Перезагружаем данные
        success = self.db.load_data()
        
        if not success:
            self.status_var.set("Ошибка при загрузке данных")
            messagebox.showerror(
                "Ошибка", 
                "Не удалось загрузить данные после обновления."
            )
            return
        
        # Обновляем статистику в интерфейсе
        self.update_journal_list()
        
        # Обновляем статус
        journals_count = result.get('journals_processed', 0)
        msg = f"Обновление завершено. Собрано {journals_count} журналов."
        self.status_var.set(msg)
        
        # Показываем сообщение
        white_list_count = result.get('white_list_journals', 0) 
        rsci_count = result.get('rsci_journals', 0)
        
        info_msg = (
            f"База журналов успешно обновлена!\n\n"
            f"Всего журналов: {journals_count}\n"
            f"В белом списке: {white_list_count}\n"
            f"В RSCI: {rsci_count}"
        )
        
        messagebox.showinfo("Обновление завершено", info_msg)
    
    def _update_failed(self, error_message):
        """
        Обработка ошибки при обновлении данных
        
        Args:
            error_message: Сообщение об ошибке
        """
        # Обновляем статус
        self.status_var.set("Ошибка при обновлении данных")
        
        # Показываем сообщение об ошибке
        error_msg = f"Не удалось обновить данные: {error_message}"
        messagebox.showerror("Ошибка", error_msg) 