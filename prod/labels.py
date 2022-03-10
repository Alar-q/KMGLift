from enum import Enum, unique


@unique
class Label(Enum):
    NODATA = 0
    DOWN = 1
    UP = 2
    OTHER = 3

    # def __str__(self):
    #     return str(self.name)


if __name__ == "__main__":
    mem = Label.DOWN
    print(mem.value)
    print(mem.name)
