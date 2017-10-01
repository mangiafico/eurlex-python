# EUR-Lex Python

## a simple Python library for EUR-Lex

The primary purpose of this library is to identify all components of all English language documents in the Legislation collection (DTS = 3).

EUR-Lex documents are described using the FRBR Work/Expression/Manifestation/Item vocabulary. The `query` function in this library returns an iterable of Work objects, each of which provides information about a document, its English expression, and all of its English manifestations and items. It requires registration credentials with the EUR-Lex Webservice.

For example, the following code prints information about each item:

```python
from eurlex import EUR_Lex

for work in EUR_Lex.query(username, password):
    print()
    print('CELEX:', work.celex)
    print('type:', work.type)
    print('year:', work.year)
    print('number:', work.number)
    print('date:', work.date)
    exp = work.english_expression
    print('  language:', exp.language)
    print('  title:', exp.title)
    for manifest in exp.manifestations:
        print('    format:', manifest.format)
        for item in manifest.items:
            print('      uri:', item.uri)
            print('      filename:', item.filename)
```
