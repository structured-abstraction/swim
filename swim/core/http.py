"""
Cherrypy's HeaderElement and AcceptElement - here until we port to CP!
"""
import re

#-------------------------------------------------------------------------------
class HeaderElement:
    """An element (with parameters) from an HTTP header's element list."""

    def __init__(self, value, params=None):
        self.value = value
        if params is None:
            params = {}
        self.params = params

    def __str__(self):
        p = [";%s=%s" % (k, v) for k, v in self.params.items()]
        return u"%s%s" % (self.value, "".join(p))

    def parse(elementstr):
        """Transform 'token;key=val' to ('token', {'key': 'val'})."""
        # Split the element into a value and parameters. The 'value' may
        # be of the form, "token=token", but we don't split that here.
        atoms = [x.strip() for x in elementstr.split(";") if x.strip()]
        if not atoms:
            initial_value = ''
        else:
            initial_value = atoms.pop(0).strip()
        params = {}
        for atom in atoms:
            atom = [x.strip() for x in atom.split("=", 1) if x.strip()]
            key = atom.pop(0)
            if atom:
                val = atom[0]
            else:
                val = ""
            params[key] = val
        return initial_value, params
    parse = staticmethod(parse)



    def from_str(cls, elementstr):
        """Construct an instance from a string of the form 'token;key=val'."""
        ival, params = cls.parse(elementstr)
        return cls(ival, params)
    from_str = classmethod(from_str)


q_separator = re.compile(r'; *q *=')

#-------------------------------------------------------------------------------
class AcceptElement(HeaderElement):
    """An element (with parameters) from an Accept* header's element list.

    AcceptElement objects are comparable; the more-preferred object will be
    "less than" the less-preferred object. They are also therefore sortable;
    if you sort a list of AcceptElement objects, they will be listed in
    priority order; the most preferred value will be first. Yes, it should
    have been the other way around, but it's too late to fix now.
    """

    def from_str(cls, elementstr):
        qvalue = None
        # The first "q" parameter (if any) separates the initial
        # media-range parameter(s) (if any) from the accept-params.
        atoms = q_separator.split(elementstr, 1)
        media_range = atoms.pop(0).strip()
        if atoms:
            # The qvalue for an Accept header can have extensions. The other
            # headers cannot, but it's easier to parse them as if they did.
            qvalue = HeaderElement.from_str(atoms[0].strip())
        media_type, params = cls.parse(media_range)
        if qvalue is not None:
            params["q"] = qvalue
        return cls(media_type, params)
    from_str = classmethod(from_str)

    def qvalue(self):
        val = self.params.get("q", "1")
        if isinstance(val, HeaderElement):
            val = val.value
        return float(val)
    qvalue = property(qvalue, doc="The qvalue, or priority, of this value.")

    def __lt__(self, other):
        return self.qvalue < other.qvalue and str(self) < str(other)

    def __eq__(self, other):
        return self.qvalue == other.qvalue and str(self) == str(other)

#-------------------------------------------------------------------------------
def header_elements(fieldname, fieldvalue):
    """Return a HeaderElement list from a comma-separated header str."""

    if not fieldvalue:
        return None
    headername = fieldname.lower()
    if headername.startswith("accept") or headername == 'te':
        ElementClass = AcceptElement
    else:
        ElementClass = HeaderElement

    result = [ElementClass.from_str(element) for element in fieldvalue.split(",") if element.strip()]

    result.sort()
    return result

