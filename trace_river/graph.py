from collections import UserDict


# Keys are tuples
# Values are lists of tuples (which match existing keys)
# When deleting a key go through all the nodes listed in the value and edit them


class Graph(UserDict):
    def __delitem__(self, key):
        for neighbour in self[key]:
            old_neighbour_value = self[neighbour]
            updated_value = [i for i in old_neighbour_value if i != key]
            if updated_value == []:
                super().__delitem__(neighbour)
            else:
                super().__setitem__(neighbour, updated_value)
        super().__delitem__(key)

    def __setitem__(self, key, value):
        print(key, value)
        for neighbour in value:
            old_neighbour_value = self.get(neighbour, [])
            super().__setitem__(neighbour, old_neighbour_value + [key,])
        super().__setitem__(key, value)

    def add_neighbour(self, key, neighbour):
        if key in self:
            self[key].append(neighbour)
            old_neighbour_value = self.get(neighbour, [])
            super().__setitem__(neighbour, old_neighbour_value + [key,])
        else:
            self[key] = [neighbour]

    def __repr__(self):
        return f"{type(self).__name__}{self.data}"


if __name__ == '__main__':
    twd = Graph()
    point_a = ((1,1))
    point_b = ((2,2))
    point_c = ((3,3))
    twd[point_a] = [point_b]
    print(twd)
    twd.add_neighbour(point_c, point_b)
    print(twd)
    del twd[point_b]
    print(twd)
