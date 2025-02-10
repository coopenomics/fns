#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET
import json

def parse_complex_type(elem):
    """
    Рекурсивно разбирает комплексный тип (xs:complexType), извлекает
    атрибуты и дочерние xs:element, создаёт структуру для дальнейшего заполнения.
    Возвращает словарь со структурой: {
      "attributes": { ... },
      "elements": {
         "ElementName": { ... },  # вложенная структура
         ...
      }
    }
    """
    ns = "{http://www.w3.org/2001/XMLSchema}"
    model = {
        "attributes": {},
        "elements": {}
    }

    # Проходим по возможным <xs:attribute>
    for attr in elem.findall(f".//{ns}attribute"):
        attr_name = attr.get("name")
        # В качестве «заглушки» ставим пустую строку
        model["attributes"][attr_name] = ""

    # Проходим по <xs:sequence>/<xs:choice> -> <xs:element>
    # (упрощённо, без детального учёта minOccurs/maxOccurs)
    sequence = elem.find(f".//{ns}sequence")
    if sequence is not None:
        for child_el in sequence.findall(f"{ns}element"):
            child_name = child_el.get("name")
            # Проверяем, нет ли у него собственного complexType
            complex_type = child_el.find(f"{ns}complexType")
            if complex_type is not None:
                # Рекурсивно получаем структуру
                model["elements"][child_name] = parse_complex_type(complex_type)
            else:
                # Если тип простой — просто пустая строка
                model["elements"][child_name] = ""

    # Аналогично ищем <xs:choice>, если есть
    choice = elem.find(f".//{ns}choice")
    if choice is not None:
        for child_el in choice.findall(f"{ns}element"):
            child_name = child_el.get("name")
            complex_type = child_el.find(f"{ns}complexType")
            if complex_type is not None:
                model["elements"][child_name] = parse_complex_type(complex_type)
            else:
                model["elements"][child_name] = ""
    return model


def extract_data_model(xsd_path):
    """
    Извлекает модель данных из заданного XSD. 
    Возвращает словарь, который затем можно вывести в JSON для ручного заполнения.
    """
    ns = "{http://www.w3.org/2001/XMLSchema}"
    tree = ET.parse(xsd_path)
    root = tree.getroot()

    # Ищем главный элемент схемы <xs:element name="‘айл">
    main_elem = None
    for elem in root.findall(f"{ns}element"):
        if elem.get("name") == "‘айл":  # имя корневого элемента из XSD
            main_elem = elem
            break

    if not main_elem:
        raise ValueError("Не найден элемент <xs:element name='‘айл'> в XSD")

    # Смотрим внутри <xs:element> -> <xs:complexType> ...
    complex_type = main_elem.find(f"{ns}complexType")
    if complex_type is None:
        raise ValueError("У элемента ‘айл нет complexType в XSD")

    # Парсим его в виде dict-модели
    model = parse_complex_type(complex_type)

    # Сам root-элемент тоже имеет атрибуты: ИдФайл, ВерсПрог, ВерсФорм
    # Подставим их в верхний уровень:
    # (Упрощение: в XSD атрибуты самого <xs:element> не расписаны,
    #  но мы можем вытащить вручную, как выше, или просто жёстко прописать)
    # Ниже — способ вытащить атрибуты root’а из complexType:
    for attr in complex_type.findall(f".//{ns}attribute"):
        attr_name = attr.get("name")
        model["attributes"][attr_name] = ""

    return { "‘айл": model }


if __name__ == "__main__":
    xsd_file = "schema.xsd"  # ваш файл
    data_model = extract_data_model(xsd_file)
    # Выводим результат в JSON (либо сохраняем в файл)
    print(json.dumps(data_model, indent=2, ensure_ascii=False))
