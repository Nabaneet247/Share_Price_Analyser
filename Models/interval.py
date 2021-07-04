class Interval:
    def __init__(self):
        self._unit = None
        self._value = None
        self._offset = None
        self._abbreviation = None

    @property
    def unit(self):
        return self._unit

    @property
    def value(self):
        return self._value

    @property
    def offset(self):
        return self._offset

    @property
    def abbreviation(self):
        return self._abbreviation

    @unit.setter
    def unit(self, unit_str):
        self._unit = unit_str

    @value.setter
    def value(self, value_int):
        self._value = value_int

    @offset.setter
    def offset(self, offset_obj):
        self._offset = offset_obj

    @abbreviation.setter
    def abbreviation(self, abbreviation):
        self._abbreviation = abbreviation
