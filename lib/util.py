import itertools


def existing_dir(d):
    if not d.exists():
        d.mkdir(parents=True)
    assert d.is_dir()
    return d


class Fixer:
    """
    Class implementing support for book-keeping about things to fix, grouped by language name.
    """
    __item_class__ = None

    def __init__(self, specs):
        self.fixes = {
            lg: list(fixes) for lg, fixes in itertools.groupby(
                sorted([self.__item_class__.from_spec(s) for s in specs], key=lambda f: f.language),
                lambda f: f.language,
            )
        }
        assert self.fixes

    @property
    def all_done(self):
        return not any(bool(len(f)) for f in self.fixes.values())
