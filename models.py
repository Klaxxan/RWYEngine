class Entry:
    def __init__(self, id, title, description="", category="", tags="", synonyms=""):
        self.id = id
        self.title = title
        self.description = description
        self.category = category
       self.tags = tags
        self.synonyms = synonyms

    def __repr__(self):
        return f"<Entry {self.id}: {self.title}>"


class Relationship:
    def __init__(self, id, entry_a, entry_b, rel_type=""):
        self.id = id
        self.entry_a = entry_a
        self.entry_b = entry_b
        self.type = rel_type

    def __repr__(self):
        return f"<Relationship {self.id}: {self.entry_a} -({self.type})-> {self.entry_b}>"
