#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Модуль-обертка для парсера журналов.
Используется для запуска парсера из графического интерфейса.
"""

import os
import json
import sys


class ParserWrapper:
    """
    Класс для запуска парсера журналов из GUI.
    """
    
    def __init__(self, output_file="vak_journals_2.3.4.json"):
        """
        Инициализация обертки парсера
        
        Args:
            output_file (str): Имя файла для сохранения результатов
        """
        # Определяем директорию приложения (директория, где находится EXE)
        if getattr(sys, 'frozen', False):
            # Если запущено как EXE
            app_dir = os.path.dirname(sys.executable)
        else:
            # Если запущено как скрипт
            app_dir = os.path.dirname(os.path.abspath(__file__))
            
        self.output_file = os.path.join(app_dir, output_file)
    
    def run_parser(self):
        """
        Запуск парсера и возврат результатов
        
        Returns:
            dict: Словарь с результатами парсинга:
                  journals_processed - количество обработанных журналов
                  white_list_journals - количество журналов в белом списке
                  rsci_journals - количество журналов в RSCI
        """
        try:
            # Импортируем парсер напрямую вместо запуска через subprocess
            import parser
            
            # Запускаем парсер
            parser.main()
            
            # Проверяем создание файла с данными
            if not os.path.exists(self.output_file):
                return {
                    "journals_processed": 0,
                    "white_list_journals": 0,
                    "rsci_journals": 0,
                    "error": "Файл с результатами не создан"
                }
            
            # Загружаем данные для статистики
            try:
                with open(self.output_file, 'r', encoding='utf-8') as file:
                    journals = json.load(file)
                
                # Считаем статистику
                journals_count = len(journals)
                white_list_count = sum(
                    1 for j in journals if j.get("white_level") != "none"
                )
                rsci_count = sum(1 for j in journals if j.get("RSCI"))
                
                return {
                    "journals_processed": journals_count,
                    "white_list_journals": white_list_count,
                    "rsci_journals": rsci_count
                }
            except Exception as e:
                return {
                    "journals_processed": 0,
                    "white_list_journals": 0,
                    "rsci_journals": 0,
                    "error": f"Ошибка при чтении файла результатов: {str(e)}"
                }
                
        except Exception as e:
            # В случае любой ошибки возвращаем нули
            return {
                "journals_processed": 0,
                "white_list_journals": 0,
                "rsci_journals": 0,
                "error": str(e)
            } 