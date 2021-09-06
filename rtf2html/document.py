class _BaseElement(object):
    def __init__(self, properties={}, content=[]):
        self.properties = {}
        self.content = []

        for (k, v) in properties.items():
            self[k] = v

        for item in content:
            self.append(item)

    def __setitem__(self, key, value):
        self.properties[key] = value

    def __getitem__(self, key):
        return self.properties.get(key)

    def append(self, item):
        self.content.append(item)


class Container(_BaseElement):
    pass


class Text(_BaseElement):
    pass


class Image(_BaseElement):
    pass


class Html(Text):
    pass

