from bs4 import BeautifulSoup
import json
import re
import os
import asyncio
import aiohttp
import datetime

def get_total_pages(soup):
    """
    Определяет общее количество страниц по информации в пагинаторе
    """
    try:
        # Ищем текст с информацией о количестве записей
        pagination_info = soup.select_one('div.dataTables_info')
        if pagination_info:
            info_text = pagination_info.text.strip()
            
            # Ищем общее количество записей в тексте
            match = re.search(r'из (\d+) записей', info_text)
            if match:
                total_records = int(match.group(1))
                records_per_page = 50  # На странице показывается 50 записей
                total_pages = (
                    (total_records + records_per_page - 1) // records_per_page
                )
                return total_pages
        
        # Если не нашли информацию о записях, пробуем найти ссылки пагинации
        pagination = soup.select_one('div.dataTables_paginate')
        if pagination:
            page_links = pagination.select('a')
            if page_links:
                # Ищем все номера страниц
                page_numbers = []
                for link in page_links:
                    try:
                        num = int(link.text.strip())
                        page_numbers.append(num)
                    except ValueError:
                        continue
                
                if page_numbers:
                    max_page = max(page_numbers)
                    return max_page
        
        # Если ничего не нашли, возвращаем 2 страницы по умолчанию
        return 2
    except Exception:
        # Если произошла ошибка, возвращаем 2 страницы по умолчанию
        return 2

async def check_rcsi_status(issn, journal_name="", session=None):
    """
    Асинхронно проверяет статус журнала в базе РЦНИ и RSCI по его ISSN или названию.
    
    Args:
        issn (str): ISSN журнала для проверки
        journal_name (str): Название журнала (используется если поиск по ISSN 
                           не дал результатов)
        session (aiohttp.ClientSession): Сессия для выполнения запросов
        
    Returns:
        dict: словарь с ключами 'white_level' и 'RSCI' и их значениями
    """
    should_close_session = False
    if not session:
        session = aiohttp.ClientSession()
        should_close_session = True
    
    try:
        if not issn and not journal_name:
            return {
                "white_level": "none", 
                "RSCI": False, 
                "rcsi_url": "none", 
                "elibrary_url": "none"
            }
        
        # Очищаем ISSN от возможных лишних символов
        cleaned_issn = ""
        if issn:
            # Удаляем все символы, кроме цифр, X и x
            cleaned_issn = ''.join(
                c for c in issn if c.isdigit() or c.upper() == 'X'
            )
            # Если длина больше 8, возможно склеены два ISSN - берем первый
            if len(cleaned_issn) > 8:
                cleaned_issn = cleaned_issn[:8]
            # Форматируем ISSN с дефисом 
            if len(cleaned_issn) == 8:
                cleaned_issn = f"{cleaned_issn[:4]}-{cleaned_issn[4:]}"
        
        # Заголовки для имитации браузера
        headers = {
            'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/91.0.4472.124 Safari/537.36'),
            'Accept': ('text/html,application/xhtml+xml,application/xml;q=0.9,'
                      'image/webp,*/*;q=0.8'),
            'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
        
        # Статус по умолчанию
        status = {
            "white_level": "none", 
            "RSCI": False, 
            "rcsi_url": "none", 
            "elibrary_url": "none"
        }
        
        # Формируем ссылку на поиск в elibrary по ISSN
        if cleaned_issn:
            # Используем базовую ссылку на поиск журналов с добавлением ISSN в параметры
            elibrary_url = (
                f"https://elibrary.ru/titles.asp?rubriccode=&sortorder=4"
                f"&titlename={cleaned_issn}&order=1"
            )
            status["elibrary_url"] = elibrary_url
        
        # Сначала пробуем поиск по ISSN, если он есть
        found_by_issn = False
        if cleaned_issn:
            # Проверяем наличие в белом списке по точному URL с очищенным ISSN
            white_list_url = (
                f"https://journalrank.rcsi.science/ru/record-sources/"
                f"?s={cleaned_issn}&adv=true"
            )
            
            # Добавляем таймаут 15 секунд для запроса
            async with session.get(
                white_list_url, headers=headers, timeout=15
            ) as response:
                response.raise_for_status()
                html_content = await response.text()
                
                # Парсим страницу с результатами поиска
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Проверяем наличие результатов
                no_results_text = soup.find(
                    string=re.compile('Ничего не найдено')
                )
                
                if not no_results_text:
                    found_by_issn = True
                    links = soup.select('a[href*="/record-sources/details/"]')
                    # Продолжаем обработку найденного журнала...
                else:
                    # Не найден в базе РЦНИ, пробуем альтернативные методы
                    pass
        
        # Если по ISSN не нашли и есть название журнала, пробуем поиск по названию
        if not found_by_issn and journal_name:
            # Формируем URL для поиска по названию
            search_term = journal_name.replace(' ', '+')
            search_url = (
                f"https://journalrank.rcsi.science/ru/search/"
                f"?s={search_term}&adv=false"
            )
            
            async with session.get(
                search_url, headers=headers, timeout=15
            ) as search_response:
                search_response.raise_for_status()
                search_html = await search_response.text()
                
                search_soup = BeautifulSoup(search_html, 'html.parser')
                journal_links = search_soup.select(
                    'a[href*="/record-sources/details/"]'
                )
                
                if journal_links:
                    # Найдены результаты при поиске по названию журнала
                    links = journal_links
                else:
                    # Журнал не найден ни по ISSN, ни по названию в базе РЦНИ
                    return status
        elif not found_by_issn:
            # Если поиск по ISSN не дал результатов и нет названия
            return status
        
        # Обработка найденных результатов (по ISSN или названию)
        if links:
            # Переходим на детальную страницу журнала
            journal_detail_link = links[0]['href']
            
            # Формируем полный URL если это относительная ссылка
            if not journal_detail_link.startswith('http'):
                journal_detail_link = (
                    f"https://journalrank.rcsi.science{journal_detail_link}"
                )
            
            # Сохраняем ссылку на журнал
            status["rcsi_url"] = journal_detail_link
            
            # Запрашиваем детальную страницу
            async with session.get(
                journal_detail_link, headers=headers, timeout=15
            ) as detail_response:
                detail_response.raise_for_status()
                detail_html = await detail_response.text()
                
                # Парсим детальную страницу
                detail_soup = BeautifulSoup(detail_html, 'html.parser')
                
                # Проверяем уровень белого списка
                level_found = False
                
                # Ищем уровень журнала 
                level_elem = (
                    detail_soup.select_one('.level-circle-value') 
                    or detail_soup.select_one('.level-value')
                )
                if level_elem:
                    level_text = level_elem.get_text().strip().split()[0]
                    if level_text.isdigit():
                        white_level = level_text  # Убираем префикс "K"
                        status["white_level"] = white_level
                        level_found = True
                
                # Если не нашли уровень, проверяем любое упоминание о ВАК
                if not level_found:
                    page_text = detail_soup.get_text().lower()
                    vak_badge = (
                        detail_soup.select_one(
                            'span.badge[title*="Перечень ВАК"]'
                        ) or 'перечень вак' in page_text
                    )
                    
                    if vak_badge:
                        status["white_level"] = "0"  # "0" вместо "K"
                        level_found = True
                
                # Если журнал найден в белом списке, проверяем RSCI
                if level_found:
                    # Проверяем наличие RSCI на странице
                    page_text = detail_soup.get_text().lower()
                    rsci_badge = detail_soup.select_one(
                        'span.badge[title*="RSCI"]'
                    )
                    if (rsci_badge or "rsci" in page_text 
                            or "ядро рниш" in page_text):
                        status["RSCI"] = True
                    else:
                        # Проверяем дополнительно по отдельному запросу с ISSN
                        if cleaned_issn:
                            rsci_url = (
                                "https://journalrank.rcsi.science/ru/record-sources/"
                                f"?s={cleaned_issn}&adv=true&rs=true"
                            )
                            
                            async with session.get(
                                rsci_url, headers=headers, timeout=15
                            ) as rsci_response:
                                rsci_response.raise_for_status()
                                rsci_html = await rsci_response.text()
                                
                                if "Ничего не найдено" not in rsci_html:
                                    status["RSCI"] = True
        
        return status
    
    except Exception:
        # Ошибка при проверке журнала
        return status
    finally:
        if should_close_session:
            await session.close()

async def parse_vak_journals(base_url):
    """
    Асинхронно парсит данные о журналах ВАК с указанного URL
    и возвращает список словарей с данными.
    """
    # Целевая специализация
    target_specialty = "2.3.4"
    
    # Заголовки для имитации браузера
    headers = {
        'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/91.0.4472.124 Safari/537.36')
    }
    
    all_journals = []
    # Множество для отслеживания уже обработанных журналов
    processed_journals = set()
    
    try:
        async with aiohttp.ClientSession() as session:
            # Получаем первую страницу для определения общего количества
            
            # Добавляем таймаут 20 секунд для запроса
            async with session.get(
                base_url, headers=headers, timeout=20
            ) as response:
                response.raise_for_status()
                html_content = await response.text()
                soup = BeautifulSoup(html_content, 'html.parser')
            
                # Определяем общее количество страниц
                total_pages = get_total_pages(soup)
                
                # Создаем задачи для обработки страниц
                page_tasks = []
                for page in range(1, total_pages + 1):
                    # Формируем URL для текущей страницы
                    page_url = (
                        f"{base_url.split('?')[0]}?page={page}&records_per_page=50"
                        f"&q=&issn=&scientific_specialties=2.3.4&category="
                    )
                    page_tasks.append(
                        process_page(
                            page, page_url, headers, session, target_specialty
                        )
                    )
                
                # Ждем завершения всех задач и собираем результаты
                page_results = await asyncio.gather(*page_tasks)
                
                # Обрабатываем результаты и удаляем дубликаты
                for journals, journal_keys in page_results:
                    for journal in journals:
                        journal_key = f"{journal['id']}_{journal['issn']}"
                        if journal_key not in processed_journals:
                            all_journals.append(journal)
                            processed_journals.add(journal_key)
        
        print(f"Найдено {len(all_journals)} журналов со специальностью {target_specialty}")
        return all_journals
    
    except aiohttp.ClientError as e:
        print(f"Ошибка при запросе к сайту: {e}")
        return all_journals
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        return all_journals

async def process_page(page, page_url, headers, session, target_specialty):
    """
    Асинхронно обрабатывает одну страницу с журналами ВАК.
    """
    try:
        async with session.get(
            page_url, headers=headers, timeout=20
        ) as response:
            response.raise_for_status()
            html_content = await response.text()
            soup = BeautifulSoup(html_content, 'html.parser')
        
            # Находим таблицу с данными
            table = soup.find('table')
            
            if not table:
                return [], set()
            
            # Получаем все строки таблицы
            rows = table.find_all('tr')
            
            # Словарь для хранения текущего журнала
            current_journal = None
            prev_number = None
            has_target_specialty = False
            journal_relevance = True  # По умолчанию журнал считается актуальным
            
            journals = []
            journal_keys = set()
            
            # Пропускаем заголовок таблицы
            for row in rows[1:]:
                # Получаем все ячейки текущей строки
                cells = row.find_all('td')
                
                if not cells:
                    continue
                    
                # Проверяем, есть ли номер журнала (новая запись)
                number_cell = cells[0].text.strip()
                
                # Если ячейка с номером не пуста - это новый журнал
                if number_cell and number_cell != prev_number:
                    # Сохраняем предыдущий журнал с нужной специальностью
                    if current_journal and has_target_specialty:
                        journal_key = f"{current_journal['id']}_{current_journal['issn']}"
                        if journal_key not in journal_keys:
                            # Добавим журнал без проверки РЦНИ
                            journals.append(current_journal)
                            journal_keys.add(journal_key)
                    
                    # Извлекаем данные о журнале
                    journal_name = cells[1].text.strip() if len(cells) > 1 else ""
                    issn = cells[2].text.strip() if len(cells) > 2 else ""
                    
                    # Определяем категорию ВАК, или "none" если не указана
                    vak_category = ""
                    if len(cells) > 5:
                        vak_category = cells[5].text.strip()
                    
                    # Если категория пустая, устанавливаем "none"
                    if not vak_category:
                        vak_category = "none"
                    # Если начинается с "К" и далее цифра, удаляем "К"
                    elif (vak_category.startswith('К') 
                          and vak_category[1:].isdigit()):
                        vak_category = vak_category[1:]
                    
                    # Создаем новый журнал
                    current_journal = {
                        "id": number_cell,
                        "name_of_publication": journal_name,
                        "issn": issn,
                        # Массив объектов {scientific_specialty, date}
                        "specialties": [],
                        "vak_category": vak_category,
                        "white_level": "none",
                        "RSCI": False,
                        "rcsi_url": "none",
                        "elibrary_url": "none",
                        "relevance": True  # По умолчанию журнал актуален
                    }
                    
                    prev_number = number_cell
                    # Сбрасываем флаг для нового журнала
                    has_target_specialty = False
                    journal_relevance = True  # Сбрасываем статус актуальности для нового журнала
                
                # Извлекаем научную специальность и дату включения
                if len(cells) > 3 and current_journal:
                    specialty = cells[3].text.strip()
                    # Проверяем, содержит ли специальность нашу целевую (2.3.4)
                    if specialty and target_specialty in specialty:
                        has_target_specialty = True
                        
                        # Получаем дату
                        date = cells[4].text.strip() if len(cells) > 4 else ""
                        
                        # Проверка актуальности журнала по дате
                        if date and "по " in date:
                            # Формат даты: "с DD.MM.YYYY по DD.MM.YYYY"
                            match = re.search(r'по (\d{2})\.(\d{2})\.(\d{4})', date)
                            if match:
                                day, month, year = map(int, match.groups())
                                end_date = datetime.date(year, month, day)
                                today = datetime.date.today()
                                
                                # Если срок истёк, отмечаем журнал как неактуальный
                                if end_date < today:
                                    journal_relevance = False
                                    current_journal["relevance"] = False
                        
                        # Проверяем, что мы еще не добавили эту специальность
                        specialty_exists = False
                        for spec in current_journal["specialties"]:
                            if spec["scientific_specialty"] == specialty:
                                specialty_exists = True
                                break
                        
                        if not specialty_exists and date:
                            # Добавляем специальность и дату как объект
                            current_journal["specialties"].append({
                                "scientific_specialty": specialty,
                                "date": date
                            })
            
            # Добавляем последний журнал на странице с нужной специальностью
            if current_journal and has_target_specialty:
                journal_key = f"{current_journal['id']}_{current_journal['issn']}"
                if journal_key not in journal_keys:
                    journals.append(current_journal)
                    journal_keys.add(journal_key)
            
            return journals, journal_keys
            
    except Exception:
        # Ошибка при обработке страницы
        return [], set()

async def check_journals_status(journals_data):
    """
    Асинхронно проверяет статус журналов в РЦНИ и RSCI.
    """
    if not journals_data:
        return journals_data
    
    print(f"Проверка {len(journals_data)} журналов в базах РЦНИ и RSCI...")
    
    # Счетчики для статистики
    updated_count = 0
    total_white_list = 0
    total_rsci = 0
    
    # Создаем задачи для проверки журналов
    async with aiohttp.ClientSession() as session:
        # Сначала подсчитываем статистику по уже имеющимся данным
        for journal in journals_data:
            if journal.get("white_level") and journal.get("white_level") != "none":
                total_white_list += 1
                
            if journal.get("RSCI"):
                total_rsci += 1
        
        # Создаем список журналов, требующих проверки
        journals_to_check = []
        for i, journal in enumerate(journals_data):
            if not journal.get("white_level") or journal.get("white_level") == "none":
                journals_to_check.append((i, journal))
        
        if journals_to_check:
            print(f"Необходимо проверить {len(journals_to_check)} журналов")
        
            # Ограничим количество одновременных задач
            # Максимум 5 одновременных запросов
            semaphore = asyncio.Semaphore(5)
            
            async def check_journal_with_semaphore(idx, journal):
                async with semaphore:
                    return await check_rcsi_status(
                        journal.get('issn', ''),
                        journal.get('name_of_publication', ''),
                        session
                    )
            
            # Создаем задачи для проверки
            tasks = [
                check_journal_with_semaphore(i, journal) 
                for i, (_, journal) in enumerate(journals_to_check)
            ]
            results = await asyncio.gather(*tasks)
            
            # Обновляем данные журналов
            for (idx, journal), status in zip(journals_to_check, results):
                if status.get("white_level") != "none":
                    journal.update(status)
                    
                    # Увеличиваем счетчики
                    if status.get("white_level") != "none":
                        total_white_list += 1
                    
                    if status.get("RSCI"):
                        total_rsci += 1
                    
                    updated_count += 1
        
    print("\nСтатистика:")
    print(f"Всего журналов: {len(journals_data)}")
    print(f"Обновлено записей: {updated_count}")
    print(f"Журналов в белом списке: {total_white_list}")
    print(f"Журналов в RSCI: {total_rsci}")
    
    return journals_data

def save_to_json(data, filename):
    """
    Сохраняет данные в JSON файл
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"Данные успешно сохранены в файл {filename}")
    except Exception as e:
        print(f"Ошибка при сохранении в JSON: {e}")

async def main_async():
    # Имя JSON-файла с данными
    json_filename = "vak_journals_2.3.4.json"
    journals_data = []
    
    # Проверяем, существует ли файл с данными
    if os.path.exists(json_filename):
        print(f"Найден существующий файл с данными: {json_filename}")
        try:
            # Загружаем данные из существующего файла
            with open(json_filename, 'r', encoding='utf-8') as f:
                journals_data = json.load(f)
            print(f"Загружено {len(journals_data)} журналов из файла")
        except Exception as e:
            print(f"Ошибка при чтении файла {json_filename}: {e}")
            journals_data = []
    
    # Если данные не загружены из файла, парсим с сайта ВАК
    if not journals_data:
        print("Данные не загружены из файла. Начинаем парсинг с сайта ВАК...")
        # Базовый URL с фильтром по специальности 2.3.4
        base_url = (
            "https://vak.academy/?q=&issn=&scientific_specialties=2.3.4&category="
            "&records_per_page=50"
        )
        
        print("Парсинг данных...")
        journals_data = await parse_vak_journals(base_url)
    
    # Асинхронно проверяем статус журналов в РЦНИ и RSCI
    if journals_data:
        journals_data = await check_journals_status(journals_data)
        
        # Сохраняем обновленные данные в JSON-файл
        save_to_json(journals_data, json_filename)
    else:
        print("Данные не найдены")

def main():
    """
    Точка входа в программу, запускает асинхронные функции
    """
    # Запускаем асинхронную функцию main_async
    asyncio.run(main_async())

if __name__ == "__main__":
    main() 