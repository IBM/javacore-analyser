from xml.dom import minidom

doc = minidom.Document()

doc.appendChild(doc.createComment("Sample XML Document"))

book = doc.createElement('book')
doc.appendChild(book)

title = doc.createElement('title')
title.appendChild(doc.createTextNode('Sample XML Thing'))
book.appendChild(title)

author = doc.createElement('author')
book.appendChild(author)
name = doc.createElement('name')
author.appendChild(name)
firstname = doc.createElement('first')
name.appendChild(firstname)
firstname.appendChild(doc.createTextNode('Benjamin'))
name.appendChild(doc.createTextNode(' '))
lastname = doc.createElement('last')
name.appendChild(lastname)
lastname.appendChild(doc.createTextNode('Smith'))

affiliation = doc.createElement('affiliation')
author.appendChild(affiliation)
affiliation.appendChild(doc.createTextNode('A'))

chapter = doc.createElement('chapter')
book.appendChild(chapter)
chapter.setAttribute('number', '1')
title = doc.createElement('title')
chapter.appendChild(title)
title.appendChild(doc.createTextNode('First Chapter'))

para = doc.createElement('para')
chapter.appendChild(para)
para.appendChild(doc.createTextNode("B"))
company = doc.createElement('company')
para.appendChild(company)
company.appendChild(doc.createTextNode('C'))

para.appendChild(doc.createTextNode('.'))

print(doc.toprettyxml(indent = '   '))

