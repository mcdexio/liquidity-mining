from functools import total_ordering, reduce
from decimal import Decimal, Context, ROUND_DOWN


_context = Context(prec=36, rounding=ROUND_DOWN)


# TODO: support any decimals
DECIMALS = 18

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
        pwr = Decimal(10) ** DECIMALS
        dec = Decimal(str(number)) * pwr
        return Wad(int(dec.quantize(1, context=_context)))

    def __repr__(self):
        return "Wad(" + str(self.value) + ")"

    def __str__(self):
        tmp = str(self.value).zfill(19)
        return (tmp[0:len(tmp)-DECIMALS] + "." + tmp[len(tmp)-DECIMALS:len(tmp)]).replace("-.", "-0.")

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
            result = Decimal(self.value) * Decimal(other.value) / (Decimal(10) ** Decimal(DECIMALS))
            return Wad(int(result.quantize(1, context=_context)))
        elif isinstance(other, int):
            return Wad(int((Decimal(self.value) * Decimal(other)).quantize(1, context=_context)))
        else:
            raise ArithmeticError

    def __truediv__(self, other):
        if isinstance(other, Wad):
            return Wad(int((Decimal(self.value) * (Decimal(10) ** Decimal(DECIMALS)) / Decimal(other.value)).quantize(1, context=_context)))
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
        return int(self.value / 10**DECIMALS)

    def __float__(self):
        return self.value / 10**DECIMALS

    @staticmethod
    def min(*args):
        """Returns the lower of the Wad values"""
        return reduce(lambda x, y: x if x < y else y, args[1:], args[0])

    @staticmethod
    def max(*args):
        """Returns the higher of the Wad values"""
        return reduce(lambda x, y: x if x > y else y, args[1:], args[0])


