#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import xml.etree.ElementTree as ET

def build_element(tag, data):
    """
    Создаёт элемент XML с именем tag.
    data - это словарь вида {
       "attributes": {...},
       "elements": {
          "ChildName": {...} или "ChildName": "some text"
       }
    }
    Возвращает объект Element (xml.etree.ElementTree.Element).
    """
    element = ET.Element(tag)

    # Проставим атрибуты (если есть)
    if "attributes" in data:
        for attr_name, attr_value in data["attributes"].items():
            # Если attr_value не пустой, добавим
            if attr_value != "":
                element.set(attr_name, str(attr_value))

    # Проставим дочерние элементы (если есть)
    if "elements" in data:
        for child_name, child_data in data["elements"].items():
            if isinstance(child_data, dict):
                # Значит там вложенная структура
                child_elem = build_element(child_name, child_data)
                element.append(child_elem)
            else:
                # Иначе это просто текст или пустая строка
                # По схеме может быть элемент без вложенных типов
                if child_data != "":
                    subel = ET.SubElement(element, child_name)
                    subel.text = str(child_data)
    return element

if __name__ == "__main__":
    # Допустим, у нас есть заполненный JSON с ключом "‘айл":
    with open("filled_data.json", "r", encoding="utf-8") as f:
        filled_data = json.load(f)

    # filled_data ожидается вида:
    # {
    #   "‘айл": {
    #       "attributes": {"ИдФайл": "...", "ВерсПрог": "...", "ВерсФорм": "..."},
    #       "elements": {
    #           "Документ": {...} 
    #       }
    #   }
    # }

    root_tag = "‘айл"
    root_data = filled_data[root_tag]

    # Строим XML-дерево
    root_element = build_element(root_tag, root_data)

    # Сохраняем в файл
    tree = ET.ElementTree(root_element)
    tree.write("output.xml", encoding="windows-1251", xml_declaration=True)
