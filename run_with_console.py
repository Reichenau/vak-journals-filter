#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Модуль запуска приложения с отображением консоли.
Используется для отладки при запуске из exe-файла.
"""

import sys
import traceback
from main import main

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Отображаем ошибку в консоли
        print("Произошла ошибка:", str(e))
        print("Traceback:")
        traceback.print_exc()
        
        # Ждем нажатия клавиши перед закрытием консоли
        input("\nНажмите Enter для закрытия...")
        sys.exit(1) 