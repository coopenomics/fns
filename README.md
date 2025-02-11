## Как использовать

Скрипт №1 (extract_data_model.py например) запускаете один раз с вашим XSD:
```python
extract_data_model.py > model.json
```

Он выведет большую структуру JSON (скелет) на основе XSD.

Редактируете model.json руками или вашей программой, заполняя атрибуты и поля (ИНН, сумму налога и т.д.). Если какой-то элемент должен повторяться (maxOccurs="unbounded"), сделайте в JSON массив таких блоков и доработайте логику генерации в build_element под массив (либо храните поля так, как вам удобнее).

Скрипт №2 (generate_xml.py) берёт заполненный JSON:

```
python generate_xml.py
```

Результат — XML в output.xml, который уже можно отправлять или проверять схемой.

## Как дополнять логику повторяющихся полей
Обратите внимание на фрагменты, где есть maxOccurs = "unbounded". В демонстрационном коде:

Если элемент сложный (есть "model"), то для многократных повторов предполагается, что в model.json лежит items: [ {...}, {...} ] с несколькими объектами. Каждый объект — обычная структура "attributes": [...], "elements": [...].

Если элемент простой (есть "placeholder"), то для многократных значений предполагается, что "value" — это список, например ["abc", "def"]. Тогда генератор создаст несколько <tagName>abc</tagName> и <tagName>def</tagName>.