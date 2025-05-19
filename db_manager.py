#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Модуль для работы с данными журналов и их хранением.
"""

import json
import os
import pandas as pd
import sys


class JournalDatabase:
    """
    Класс для работы с базой данных журналов.
    Выполняет загрузку, сохранение и фильтрацию журналов.
    """
    
    def __init__(self, filename="vak_journals_2.3.4.json"):
        """
        Инициализация базы данных журналов
        
        Args:
            filename (str): Имя файла с данными журналов
        """
        # Определяем директорию приложения (директория, где находится EXE)
        if getattr(sys, 'frozen', False):
            # Если запущено как EXE
            app_dir = os.path.dirname(sys.executable)
        else:
            # Если запущено как скрипт
            app_dir = os.path.dirname(os.path.abspath(__file__))
            
        self.filename = os.path.join(app_dir, filename)
        self.journals = []
        self.load_data()
    
    def load_data(self):
        """
        Загрузка данных из JSON файла
        
        Returns:
            bool: True, если загрузка прошла успешно, иначе False
        """
        try:
            if os.path.exists(self.filename):
                with open(self.filename, 'r', encoding='utf-8') as file:
                    self.journals = json.load(file)
                return True
            return False
        except Exception as e:
            print(f"Ошибка при загрузке данных: {e}")
            return False
    
    def save_data(self, journals=None):
        """
        Сохранение данных в JSON файл
        
        Args:
            journals (list, optional): Список журналов для сохранения. 
                                      По умолчанию None, что означает 
                                      сохранение self.journals
        
        Returns:
            bool: True, если сохранение прошло успешно, иначе False
        """
        if journals is None:
            journals = self.journals
        
        try:
            with open(self.filename, 'w', encoding='utf-8') as file:
                json.dump(journals, file, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Ошибка при сохранении данных: {e}")
            return False
    
    def get_journals(self):
        """
        Получение списка всех журналов
        
        Returns:
            list: Список всех журналов
        """
        return self.journals
    
    def get_journal_by_issn(self, issn):
        """
        Поиск журнала по ISSN
        
        Args:
            issn (str): ISSN журнала
        
        Returns:
            dict: Словарь с данными журнала или None, если журнал не найден
        """
        if not issn:
            return None
        
        # Очищаем ISSN от лишних символов
        clean_issn = issn.strip().replace("-", "")
        
        for journal in self.journals:
            current_issn = journal.get("issn", "").strip().replace("-", "")
            if current_issn == clean_issn:
                return journal
        
        return None
    
    def get_vak_categories(self):
        """
        Получение списка всех категорий ВАК
        
        Returns:
            list: Список уникальных категорий ВАК
        """
        categories = set()
        
        for journal in self.journals:
            category = journal.get("vak_category")
            if category and category != "none":
                categories.add(category)
        
        return sorted(list(categories))
    
    def get_white_levels(self):
        """
        Получение списка всех уровней белого списка
        
        Returns:
            list: Список уникальных уровней белого списка
        """
        levels = set()
        
        for journal in self.journals:
            level = journal.get("white_level")
            if level and level != "none":
                levels.add(level)
        
        return sorted(list(levels))
    
    def filter_journals(
        self, vak_categories=None, white_levels=None, in_rsci=None
    ):
        """
        Фильтрация журналов по заданным критериям
        
        Args:
            vak_categories: Список категорий ВАК для фильтрации
            white_levels: Список уровней белого списка для фильтрации
            in_rsci: Булево значение для фильтрации по RSCI
            
        Returns:
            list: Отфильтрованный список журналов
        """
        filtered_journals = []
        
        for journal in self.journals:
            # Показываем только актуальные журналы
            if journal.get("relevance", True) is False:
                continue
                
            # Фильтрация по категориям ВАК
            if vak_categories:
                journal_vak = journal.get("vak_category", "none")
                if journal_vak not in vak_categories:
                    continue
            
            # Фильтрация по уровням белого списка
            if white_levels:
                journal_white = journal.get("white_level", "none")
                if journal_white not in white_levels:
                    continue
            
            # Фильтрация по RSCI
            if in_rsci is not None:
                journal_rsci = journal.get("RSCI", False)
                if journal_rsci != in_rsci:
                    continue
            
            # Журнал прошел все фильтры
            filtered_journals.append(journal)
        
        return filtered_journals
    
    def export_to_excel(
        self, journals, output_file="vak_journals_filtered.xlsx"
    ):
        """
        Экспорт журналов в Excel файл
        
        Args:
            journals: Список журналов для экспорта
            output_file: Путь к выходному файлу Excel
            
        Returns:
            bool: True в случае успеха, False в случае ошибки
        """
        try:
            # Создаем DataFrame для экспорта
            data = []
            for journal in journals:
                data.append({
                    "Название журнала": journal.get("name_of_publication", ""),
                    "ISSN": journal.get("issn", ""),
                    "Категория ВАК": journal.get("vak_category", "none"),
                    "Уровень белого списка": journal.get("white_level", "none"),
                    "RSCI": "Да" if journal.get("RSCI") else "Нет",
                    "Ссылка elibrary": journal.get("elibrary_url", ""),
                    "Ссылка РЦНИ": journal.get("rcsi_url", "")
                })
            
            # Создаем DataFrame и сохраняем в Excel
            df = pd.DataFrame(data)
            df.to_excel(output_file, index=False, engine='openpyxl')
            
            return True
        except Exception:
            return False 