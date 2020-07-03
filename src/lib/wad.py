from functools import total_ordering, reduce
from decimal import *


_context = Context(prec=1000, rounding=ROUND_DOWN)


@total_ordering
class Wad:
    def __init__(self, value):
        if isinstance(value, Wad):
            self.value = value.value
        elif isinstance(value, int):
            # assert(value >= 0)
            self.value = value
        else:
            raise ArithmeticError

    @classmethod
    def from_number(cls, number):
        # assert(number >= 0)
        pwr = Decimal(10) ** 18
        dec = Decimal(str(number)) * pwr
        return Wad(int(dec.quantize(1, context=_context)))

    def __repr__(self):
        return "Wad(" + str(self.value) + ")"

    def __str__(self):
        tmp = str(self.value).zfill(19)
        return (tmp[0:len(tmp)-18] + "." + tmp[len(tmp)-18:len(tmp)]).replace("-.", "-0.")

    def __add__(self, other):
        if isinstance(other, Wad):
            return Wad(self.value + other.value)
        else:
            raise ArithmeticError

    def __sub__(self, other):
        if isinstance(other, Wad):
            return Wad(self.value - other.value)
        else:
            raise ArithmeticError

    def __mul__(self, other):
        if isinstance(other, Wad):
            result = Decimal(self.value) * Decimal(other.value) / (Decimal(10) ** Decimal(18))
            return Wad(int(result.quantize(1, context=_context)))
        elif isinstance(other, int):
            return Wad(int((Decimal(self.value) * Decimal(other)).quantize(1, context=_context)))
        else:
            raise ArithmeticError

    def __truediv__(self, other):
        if isinstance(other, Wad):
            return Wad(int((Decimal(self.value) * (Decimal(10) ** Decimal(18)) / Decimal(other.value)).quantize(1, context=_context)))
        else:
            raise ArithmeticError

    def __abs__(self):
        return Wad(abs(self.value))

    def __eq__(self, other):
        if isinstance(other, Wad):
            return self.value == other.value
        else:
            raise ArithmeticError

    def __lt__(self, other):
        if isinstance(other, Wad):
            return self.value < other.value
        else:
            raise ArithmeticError

    def __int__(self):
        return int(self.value / 10**18)

    def __float__(self):
        return self.value / 10**18

    @staticmethod
    def min(*args):
        """Returns the lower of the Wad values"""
        return reduce(lambda x, y: x if x < y else y, args[1:], args[0])

    @staticmethod
    def max(*args):
        """Returns the higher of the Wad values"""
        return reduce(lambda x, y: x if x > y else y, args[1:], args[0])
