#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт №1:
1) Читает XSD-файл (например, schema.xsd).
2) Читает файл standart.json, где собраны описания полей (shortName, формат и т.д.).
3) Обходит структуру XSD, находит элементы, атрибуты.
   - Если <xs:element name="X" maxOccurs="unbounded"> => в модели будет массив.
   - Если <xs:element name="X" maxOccurs="1"> => одиночный элемент.
   - Атрибуты тоже включаем.
4) Для каждого такого элемента/атрибута пытается найти описание в standart.json 
   (по shortName == name). 
   - Если находит, берёт fromStandart = {...} (fullName, format, required и т.д.).
   - Формирует объект {"shortName": name, "fromStandart": {...}, "value": ...}.
5) Складывает всё это в итоговую модель (model.json).
"""

import json
import xml.etree.ElementTree as ET
from typing import Dict, Any, List

XSD_NS = "{http://www.w3.org/2001/XMLSchema}"

def load_standart(path: str) -> Dict[str, Dict[str, Any]]:
    """
    Загружает standart.json, возвращает словарь:
    {
      shortName: {
        "fullName": ...,
        "type": ...,
        "format": ...,
        "required": ...,
        "info": ...,
        "tableNumber": ...,
        ...
      },
      ...
    }
    Удобно для быстрого поиска по shortName.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    result = {}
    for table in data.get("tables", []):
        table_num = table.get("tableNumber")
        fields = table.get("fields", [])
        for fld in fields:
            sname = fld.get("shortName")
            if sname:
                # Чтобы хранить и tableNumber для наглядности
                result[sname] = {
                    "fullName": fld.get("fullName"),
                    "type": fld.get("type"),
                    "format": fld.get("format"),
                    "required": fld.get("required"),
                    "info": fld.get("info"),
                    "tableNumber": table_num
                }
    return result

def parse_complex_type(elem: ET.Element, standard_map: Dict[str,Any]) -> Dict[str, Any]:
    """
    Рекурсивно обходит <xs:complexType> => <xs:sequence>/<xs:choice> => <xs:element>.
    Также обходит <xs:attribute>.
    
    Возвращает модель вида:
    {
      "attributes": [
        {
          "shortName": "ВерсПрог",
          "fromStandart": {...},  # данные из standart.json
          "value": ""
        }, 
        ...
      ],
      "elements": [
        {
          "tagName": "Документ",
          "maxOccurs": 1,
          "model": {
             "attributes": [...],
             "elements": [...]
          }
        },
        ...
      ]
    }
    """
    model = {
        "attributes": [],
        "elements": []
    }

    # Обрабатываем <xs:attribute>
    for attr in elem.findall(f".//{XSD_NS}attribute"):
        aname = attr.get("name")
        # maxOccurs для атрибута не бывает, обычно use="required"/"optional"
        # Поищем в standard_map
        from_standart = standard_map.get(aname, {})
        model["attributes"].append({
            "shortName": aname,
            "fromStandart": from_standart,
            "value": ""
        })

    # Для вложенных элементов смотрим <xs:sequence> и <xs:choice>
    # упрощённо не разбираем "sequence" внутри "sequence" и т.д. на нескольких уровнях
    sequence = elem.find(f"{XSD_NS}sequence")
    if sequence is not None:
        for sub_el in sequence.findall(f"{XSD_NS}element"):
            child = process_element(sub_el, standard_map)
            if child:
                model["elements"].append(child)

    choice = elem.find(f"{XSD_NS}choice")
    if choice is not None:
        for sub_el in choice.findall(f"{XSD_NS}element"):
            child = process_element(sub_el, standard_map)
            if child:
                model["elements"].append(child)

    return model

def process_element(element: ET.Element, standard_map: Dict[str,Any]) -> Dict[str, Any]:
    """
    Обрабатывает один <xs:element>. 
    Смотрит атрибуты name, minOccurs, maxOccurs. 
    Если есть вложенный <xs:complexType>, уходим в рекурсию.
    Возвращаем объект вида:
      {
        "tagName": "Документ",
        "maxOccurs": 1 or 'unbounded' (или число),
        "model": { "attributes": [...], "elements": [...] }  # если complex
            или "placeholder": { "shortName": "Документ", fromStandart, "value": "" } если простой
      }
    """
    ename = element.get("name", "")
    min_occurs = element.get("minOccurs", "1")
    max_occurs = element.get("maxOccurs", "1")
    # Если maxOccurs = "unbounded", надо делать массив
    # Если число > 1, тоже массив
    # Иначе 1 => одиночный

    cplx = element.find(f"{XSD_NS}complexType")
    if cplx is not None:
        # Вложенный complexType => рекурсия
        sub_model = parse_complex_type(cplx, standard_map)
        return {
            "tagName": ename,
            "maxOccurs": max_occurs,
            "model": sub_model
        }
    else:
        # Простой элемент
        from_standart = standard_map.get(ename, {})
        return {
            "tagName": ename,
            "maxOccurs": max_occurs,
            "placeholder": {
                "shortName": ename,
                "fromStandart": from_standart,
                "value": ""
            }
        }

def main():
    xsd_path = "schema.xsd"          # Ваш XSD-шаблон
    json_standart_path = "standart.json"  # Ваш файл с таблицами (4.1–4.71)
    output_model_path = "model.json"      # Выходной JSON-модель

    # 1) Загружаем справочник полей
    standard_map = load_standart(json_standart_path)

    # 2) Парсим XSD
    tree = ET.parse(xsd_path)
    root = tree.getroot()

    # Предположим, ищем <xs:element name="‘айл"> как корневой
    main_elem = None
    for el in root.findall(f"{XSD_NS}element"):
        if el.get("name") == "‘айл":
            main_elem = el
            break

    if not main_elem:
        print("Не найден корневой <xs:element name='‘айл'>, завершаем.")
        return

    # Если у <‘айл> есть complexType -> обрабатываем
    cplx = main_elem.find(f"{XSD_NS}complexType")
    if cplx is None:
        print("У корневого элемента ‘айл нет <xs:complexType>, завершаем.")
        return

    root_model = parse_complex_type(cplx, standard_map)

    # Формируем итоговую структуру:
    # {
    #   "rootTag": "‘айл",
    #   "model": { ... }  # attributes + elements
    # }
    final_structure = {
        "rootTag": "‘айл",
        "model": root_model
    }

    # 3) Сохраняем в model.json
    with open(output_model_path, "w", encoding="utf-8") as f:
        json.dump(final_structure, f, indent=2, ensure_ascii=False)

    print(f"Готово! Сформирован шаблон для заполнения: {output_model_path}")

if __name__ == "__main__":
    main()
