
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from lxml import etree

class EUR_Lex:

    @classmethod
    def query(cls, username, password, q=None):
        return Webservice(username, password).query(q)

    @classmethod
    def fetch(cls, celex):
        return Work.fetch(celex)


class Webservice:

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def query(self, q='DTS = 3'):

        def make_payload(page):
            return """<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:sear="http://eur-lex.europa.eu/search">
<soap:Header>
    <wsse:Security xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd" soap:mustUnderstand="true">
    <wsse:UsernameToken xmlns:wsu="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd" wsu:Id="UsernameToken-1">
        <wsse:Username>""" + self.username + """</wsse:Username>
        <wsse:Password Type="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordText">""" + self.password + """</wsse:Password>
    </wsse:UsernameToken>
    </wsse:Security>
</soap:Header>
<soap:Body>
    <sear:searchRequest>
    <sear:expertQuery><![CDATA[ """ + q + """ ]]></sear:expertQuery>
    <sear:page>""" + str(page) + """</sear:page>
    <sear:pageSize>10</sear:pageSize>
    <sear:searchLanguage>en</sear:searchLanguage>
    </sear:searchRequest>
</soap:Body>
</soap:Envelope>
"""

        def fetch_celex_numbers(page):
            endpoint = "http://eur-lex.europa.eu/EURLexWebService"
            headers = { 'Content-Type': "application/soap+xml" }
            payload = make_payload(page).encode('utf-8')
            request = Request(endpoint, payload, headers)
            response = urlopen(request)
            tree = etree.parse(response)
            namespaces = {
                'S': "http://www.w3.org/2003/05/soap-envelope",
                'e': "http://eur-lex.europa.eu/search"
            }
            return [ value.text for value in tree.xpath('S:Body/e:searchResults/e:result/e:content/e:NOTICE/e:WORK/e:ID_CELEX/e:VALUE', namespaces=namespaces) ]

        page = 1
        celex_numbers = fetch_celex_numbers(page)
        while len(celex_numbers) > 0:
            for celex in celex_numbers:
                work = Work.fetch(celex)
                if work is not None: yield work
            page += 1
            celex_numbers = fetch_celex_numbers(page)


class XpathHelper:

    def get_string(self, xpath):
        try:
            return self.root.xpath(xpath)[0].text
        except IndexError:
            return None


class Work(XpathHelper):

    def __init__(self, root):
        self.root = root

    @classmethod
    def fetch(cls, celex):
        celex = celex.replace('(','%28').replace(')', '%29')
        endpoint = "http://publications.europa.eu/resource/celex/" + celex
        headers = {
            'Accept': "application/xml;notice=branch",
            'Accept-Language': "eng"
        }
        request = Request(endpoint, headers=headers)
        try:
            response = urlopen(request)
        except HTTPError as e:
            if e.code == 406:
                return None
            else:
                raise e
        tree = etree.parse(response)
        return Work(tree)

    @property
    def celex(self):
        return self.get_string("WORK/URI[TYPE='celex']/IDENTIFIER | WORK/SAMEAS/URI[TYPE='celex']/IDENTIFIER")

    @property
    def type(self):
        return self.get_string('WORK/WORK_HAS_RESOURCE-TYPE/IDENTIFIER')

    @property
    def year(self):
        return self.get_string('WORK/RESOURCE_LEGAL_YEAR/VALUE')

    @property
    def number(self):
        return self.get_string('WORK/RESOURCE_LEGAL_NUMBER_NATURAL/VALUE')

    @property
    def date(self):
        return self.get_string('WORK/DATE_DOCUMENT/VALUE')

    @property
    def english_expression(self):
        return Expression(self.root.xpath('EXPRESSION')[0])


class Expression(XpathHelper):

    def __init__(self, root):
        self.root = root

    @property
    def language(self):
        return self.get_string('EXPRESSION_USES_LANGUAGE/IDENTIFIER')

    @property
    def title(self):
        return self.get_string('EXPRESSION_TITLE/VALUE')

    @property
    def manifestations(self):
        return [ Manifestation(e) for e in self.root.xpath('../MANIFESTATION') ]

    def get_formex_items(self):
        for manifest in self.manifestations:
            if manifest.format != 'fmx4': continue
            for item in manifest.items:
                if not item.filename.endswith('.xml'): continue
                if item.filename.endswith('.doc.xml'): continue
                yield FormexItem(item.root)


class Manifestation(XpathHelper):

    def __init__(self, root):
        self.root = root

    @property
    def format(self):
        return self.get_string('MANIFESTATION_TYPE/VALUE')

    @property
    def items(self):
        return [ Item(e) for e in self.root.xpath('MANIFESTATION_HAS_ITEM') ]


class Item(XpathHelper):

    def __init__(self, root):
        self.root = root

    @property
    def uri(self):
        return self.get_string('URI/VALUE')

    @property
    def filename(self):
        return self.get_string('TECHMD/STREAM_NAME/VALUE')


class FormexItem(Item):

    def xpath(self, xpath):
        xml = urlopen(self.uri)
        tree = etree.parse(xml)
        return tree.xpath(xpath)
