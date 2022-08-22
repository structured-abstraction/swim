from django.template.loader import get_template

#-------------------------------------------------------------------------------
# TODO: this is a candidate for refactoring into SWIM proper
class SwimTemplateDecoy:
    """This class duck types the Base model for all templates in swim.

    Intended to be returned from a swim view's match_template method.
    """
    def __init__(self, path, http_content_type):
        self.path = path
        self.http_content_type = http_content_type
        self.body = None

#-------------------------------------------------------------------------------
# TODO: this is a candidate for refactoring into SWIM proper
def load_template_decoy(path, http_content_type='text/html; charset=utf8'):
    """
    Helper which loads template from disk and jams it into a template decoy.
    """
    return SwimTemplateDecoy(path=path, http_content_type=http_content_type)
