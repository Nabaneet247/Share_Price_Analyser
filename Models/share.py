from Models.ltp import LTP


class Share:
    def __init__(self):
        self._symbol = None
        self._name = None
        self._ltp = LTP()

    @property
    def symbol(self):
        return self._symbol

    @symbol.setter
    def symbol(self, symbol):
        self._symbol = symbol

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name
