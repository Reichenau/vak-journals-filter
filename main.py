#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Основной модуль запуска приложения для анализа журналов ВАК.
"""

import tkinter as tk
from gui import JournalAnalyzerApp


def main():
    """
    Функция запуска приложения
    """
    root = tk.Tk()
    root.title("Фильтр журналов 2.3.4")
    root.geometry("800x400")
    root.minsize(700, 350)
    
    # Создаем приложение
    app = JournalAnalyzerApp(root)
    _ = app  # Подавляем предупреждение линтера о неиспользуемой переменной
    
    # Запускаем главный цикл
    root.mainloop()


if __name__ == "__main__":
    main() 