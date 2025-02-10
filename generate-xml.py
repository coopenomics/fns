#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт №2:
1) Берёт заполненный model.json (те же поля, но "value" уже не пустые).
2) Генерирует XML-документ по той же структуре: rootTag = "‘айл", 
   затем вложенные атрибуты, элементы и т.д.
3) Учитывает maxOccurs. Если maxOccurs > 1 или "unbounded", 
   предполагаем, что в "model.json" в соответствующем месте может быть список.
4) Сохраняем XML с нужным заголовком "<?xml version='1.0' encoding='windows-1251'?>".
"""

import json
import xml.etree.ElementTree as ET
from typing import Any, List, Dict

def create_element(tag_name: str, model_part: Dict[str, Any]) -> ET.Element:
    """
    Рекурсивно создаёт элемент с именем tag_name на основе структуры:
    {
      "attributes": [
        {
          "shortName": ...,
          "value": ...
        }, ...
      ],
      "elements": [
        {
          "tagName": "...",
          "maxOccurs": "...",
          "model": { ... }   // если complexType
            ИЛИ
          "placeholder": { "shortName":"...", "value": "..." } // если простой
        },
        ...
      ]
    }
    """
    el = ET.Element(tag_name)

    # Заполняем атрибуты
    for attr_obj in model_part.get("attributes", []):
        short_name = attr_obj["shortName"]
        val = attr_obj.get("value", "")
        if val != "":
            el.set(short_name, str(val))

    # Заполняем вложенные элементы
    for elem_obj in model_part.get("elements", []):
        tagName = elem_obj["tagName"]
        max_occ = elem_obj["maxOccurs"]

        # Смотрим, есть ли "model" (сложный элемент) или "placeholder" (простой)
        if "model" in elem_obj:
            # Это комплексный элемент
            # Но если maxOccurs="unbounded" или >1 — возможно, в model.json
            # хранится список таких структур. 
            sub_item = elem_obj["model"]
            # Смотрим, есть ли в sub_item "arrayData" или что-то подобное.
            # Упростим: предполагаем, что если нужно несколько повторов, 
            # пользователь скопировал этот блок n раз.

            # Чтобы это корректно обрабатывать, 
            # можно в model.json хранить sub_item в виде массива. 
            # Но в нашем подходе sub_item -> dict. 
            # Часто делают: "modelArray": [ {...}, {...} ].
            # Для демонстрации примем упрощённый вариант: 
            # один экземпляр, если "maxOccurs"=="1".
            # Если "unbounded", то пользователь сам может делать 
            # sub_item: [{...}, {...}] 
            # Тогда делаем несколько узлов.

            if max_occ == "unbounded" or (max_occ.isdigit() and int(max_occ) > 1):
                # Предположим, user в "model" положил "items": [ {...}, {...} ]
                items = sub_item.get("items", [])
                for one_item in items:
                    child_el = create_element(tagName, one_item)
                    el.append(child_el)
            else:
                # maxOccurs=1
                child_el = create_element(tagName, sub_item)
                el.append(child_el)

        elif "placeholder" in elem_obj:
            # Простой элемент
            placeholder = elem_obj["placeholder"]
            # Если тоже повторяющийся, user мог сделать "values": ["...", "..."] 
            # Упростим:
            val = placeholder.get("value", "")
            if max_occ == "unbounded":
                # Предположим, user заполнил placeholder["value"] = ["v1","v2"]
                # Тогда делаем несколько <tagName>v1</tagName>, <tagName>v2</tagName>...
                if isinstance(val, list):
                    for v in val:
                        child_el = ET.SubElement(el, tagName)
                        child_el.text = str(v)
                else:
                    # Если user не заполнил как список — создаём один
                    child_el = ET.SubElement(el, tagName)
                    child_el.text = str(val)
            else:
                # maxOccurs=1
                child_el = ET.SubElement(el, tagName)
                child_el.text = str(val)

    return el

def main():
    input_model = "model.json"  # Заполненный пользователем JSON
    output_xml = "result.xml"   # Итоговый XML

    with open(input_model, "r", encoding="utf-8") as f:
        data = json.load(f)

    root_tag = data["rootTag"]
    root_model = data["model"]

    # Строим XML
    root_element = create_element(root_tag, root_model)

    # Сохраняем с кодировкой windows-1251 и xml-заголовком
    tree = ET.ElementTree(root_element)
    tree.write(output_xml, encoding="windows-1251", xml_declaration=True)

    print(f"XML сформирован в файле '{output_xml}'.")

if __name__ == "__main__":
    main()
