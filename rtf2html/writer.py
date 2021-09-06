import io

from rtf2html import document

_tagNames = {
    'bold': 'strong',
    'italic': 'em',
    'underline': 'u', # ?
}


class XHTMLWriter:
    @classmethod
    def write(cls, doc, target=None, pretty=False):
        if target is None:
            target = io.BytesIO()

        writer = XHTMLWriter(doc, target, pretty)
        final = writer.go()
        final.seek(0)
        return final

    def __init__(self, doc, target, pretty=False):
        self.document = doc
        self.target = target
        self.pretty = pretty
        self.dispatch = {
            # document.List: self._list,
            # document.Paragraph: self._paragraph,
            document.Container: self._container,
            document.Html: self._html,
            document.Text: self._text
        }
        self.listLevel = -1

    def go(self):
        self.listLevel = -1

        tag = Tag(None)
        for element in self.document.content:
            handler = self.dispatch[element.__class__]
            tag.content.extend(handler(element))

        tag.render(self.target)
        return self.target

    def _container(self, container):
        tag = Tag(None)
        for element in container.content:
            handler = self.dispatch[element.__class__]
            tag.content.extend(handler(element))

        if self.pretty:
            return [_prettyBreak, tag, _prettyBreak]
        else:
            return [tag]

    def _html(self, html):
        h = Tag("html")
        for text in html.content:
            h.content.append(text)
        return [h]

    def _paragraph(self, paragraph):
        p = Tag("p")
        for text in paragraph.content:
            p.content.append(self._text(text))

        if self.pretty:
            return [_prettyBreak, p, _prettyBreak]
        else:
            return [p]

    def _list(self, lst):
        self.listLevel += 1

        ul = Tag("ul")

        for entry in lst.content:
            li = Tag("li")
            for element in entry.content:
                handler = self.dispatch[element.__class__]
                li.content.extend(handler(element))
            ul.content.append(li)

        self.listLevel -= 1

        return [ul]

    def _text(self, text):
        if 'url' in text.properties:
            tag = Tag("a")
            tag.attrs['href'] = text.properties['url']
        else:
            tag = Tag(None)

        current = tag

        for prop in ('bold', 'italic', 'underline'):
            if prop in text.properties:
                new_tag = Tag(_tagNames[prop])
                current.content.append(new_tag)
                current = new_tag

        for prop in ('sub', 'super'):
            if prop in text.properties:
                if current.tag is None:
                    new_tag = Tag("span")
                    current.content.append(new_tag)
                    current = new_tag
                current.attrs['style'] = "vertical-align: %s; font-size: smaller" % prop

        current.content.append(u"".join(text.content))

        return [tag]


class _PrettyBreak:
    def __repr__(self):
        return "PrettyBreak"


_prettyBreak = _PrettyBreak()


class Tag(object):
    def __init__(self, tag, attrs=None, content=None):
        self.tag = tag
        self.attrs = attrs or {}
        self.content = content or []

    def render(self, target):

        if self.tag == 'html':
            for c in self.content:
                target.write(c.encode("utf-8"))
            return

        if self.tag is not None:
            attr_string = self.attr_string()
            if attr_string:
                attr_string = " " + attr_string
            target.write(('<%s%s>' % (self.tag, attr_string)).encode("utf-8"))

        for c in self.content:
            if isinstance(c, Tag):
                c.render(target)
            elif c is _prettyBreak:
                target.write(b'\n')
            else:
                if type(c) != str:
                    c = str(c)
                target.write(quote_text(c).encode("utf-8").replace(b'\n', b'<br />'))

        if self.tag is not None:
            target.write(('</%s>' % self.tag).encode("utf-8"))

    def attr_string(self):
        return " ".join(
            '%s="%s"' % (k, quote_attr(v))
            for (k, v) in self.attrs.items())

    def __repr__(self):
        return "T(%s)[%s]" % (self.tag, repr(self.content))


def quote_text(text):
    return text.replace(
        u"&", u"&amp;").replace(
        u"<", u"&lt;").replace(
        u">", u"&gt;")


def quote_attr(text):
    return quote_text(text).replace(
        u'"', u"&quot;").replace(
        u"'", u"&apos;")
