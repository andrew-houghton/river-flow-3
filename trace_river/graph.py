from collections import UserDict


class Graph(UserDict):
    """Graph for holding which points are merged and connected
    Keys are tuple of tuples eg ((1,2), (2,2))
    Values are sets of keys eg {((1,2), (2,2)), ((4,2), (1,4))}
    Relationships should be maintained in both directions
    """

    def __delitem__(self, key):
        for neighbour in self[key]:
            old_neighbour_value = self[neighbour]
            old_neighbour_value.remove(key)
        super().__delitem__(key)

    def __setitem__(self, key, value):
        assert key not in value
        for neighbour in value:
            old_neighbour_value = self.get(neighbour, set())
            old_neighbour_value.add(key)
            super().__setitem__(neighbour, old_neighbour_value)
        super().__setitem__(key, value)

    def __repr__(self):
        return f"{type(self).__name__}{self.data}"
