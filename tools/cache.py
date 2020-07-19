import abc
import logging
import threading


class Node:

    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.next = None
        self.prev = None

    def __eq__(self, other):
        return self.key == other.key and self.value == other.value

    def set_next(self, nxt):
        self.next = nxt

    def __str__(self):
        return f"{self.key}:{self.value}"

    def __repr__(self):
        return f"{self.key}:{self.value}"


class FullCapacityError(Exception):
    pass


class DoubleList:

    def __init__(self, cap=300):
        self.assert_cap(cap)
        self.head = None
        self.tail = None
        self.size = 0
        self.cap = cap
        self.__cursor = self.head

    @staticmethod
    def assert_cap(cap):
        if cap <= 0:
            raise ValueError(f'cap must grate than 0')
        if cap > 65535:
            logging.warning(f"too large cap for cache,current cap:{cap}")

    def __len__(self):
        return self.size

    def is_full(self) -> bool:
        return self.size >= self.cap

    def __insert_head(self, node):
        if not self.head:
            self.head = node
            self.tail = node
        else:
            node.next = self.head
            self.head.prev = node
            self.head = node
            self.head.prev = None
        self.size += 1
        return node

    def __append(self, node):
        if not self.tail:
            self.tail = node
            self.head = node
        else:
            self.tail.next = node
            node.prev = self.tail
            self.tail = node
            self.tail.next = None
        self.size += 1
        return node

    def pop(self) -> Node:
        return self.__remove_head()

    def peek(self) -> Node:
        return self.head

    def assert_size(self):
        if self.size > self.cap:
            raise FullCapacityError(f"list max cap is {self.cap}")

    def append(self, node):
        self.assert_size()
        return self.__append(node)

    def insert_head(self, node):
        self.assert_size()
        return self.__insert_head(node)

    def remove(self, node=None):
        return self.__remove(node)

    def pop_last(self):
        return self.__remove_tail()

    def __remove_head(self):
        if not self.head:
            return
        node = self.head
        if not node:
            self.head = self.tail = None
            return
        self.head = node.next
        self.prev = None
        self.size -= 1
        return node

    def __remove_tail(self):
        if not self.tail:
            return
        if self.head == self.tail:
            self.head = self.tail = None
            return
        node = self.tail
        self.tail = node.prev
        self.tail.next = None
        self.size -= 1
        return node

    def __rm(self, node):
        node.prev.next = node.next
        node.nexr.pre = node.prev
        self.size -= 1

    def __remove(self, node):
        if self.head == node:
            return self.__remove_head()
        elif self.tail == node:
            return self.__remove_tail()
        else:
            self.__rm(node)
        return node

    def __iter__(self):
        return self

    def __next__(self):
        if not self.__cursor:
            self.__cursor = self.head
            raise StopIteration()
        data = self.__cursor
        self.__cursor = self.__cursor.next
        return data

    def is_empty(self) -> bool:
        return self.size == 0


class Cache(metaclass=abc.ABCMeta):

    def __init__(self, cap=300):
        self.__cap = cap
        self.list = DoubleList(self.__cap)

    @abc.abstractmethod
    def get(self, key):
        pass

    @abc.abstractmethod
    def put(self, key, value):
        pass

    def capacity(self):
        return self.__cap

    def __len__(self):
        return self.list.__len__()

    def __getitem__(self, item):
        return self.get(item)

    def __setitem__(self, key, value):
        self.put(key, value)

    def is_empty(self):
        return self.list.is_empty()


class FiIFOCache(Cache):

    def __init__(self):
        super().__init__()
        self.map = {}

    def get(self, key):
        node = self.map.get(key)
        if node:
            return node.value
        return None

    def put(self, key, value):
        node = self.map.get(key)
        if node:
            self.list.remove(node)
            node.value = value
        else:
            if self.list.is_full():
                node = self.list.pop()
                del self.map[node.key]
            node = Node(key, value)
            self.map[key] = node
        self.list.append(node)


class LRUCache(Cache):

    def __init__(self, cap=65535):
        super().__init__(cap)
        self.__map = {}

    def get(self, key):
        node = self.__map.get(key)
        if node:
            self.list.remove(node)
            self.list.insert_head(node)
            return node.value
        return None

    def put(self, key, value):
        node = self.__map.get(key)
        if node:
            self.list.remove(node)
            node.value = value
        else:
            if self.list.is_full():
                last_node = self.list.pop_last()
                del self.__map[last_node.key]
            node = Node(key, value)
            self.__map[key] = node
        self.list.insert_head(node)


class Frequency:
    __slots__ = ["__a", "__lock"]

    def __init__(self):
        self.__a = 1
        self.__lock = threading.RLock()

    def increment(self):
        with self.__lock:
            self.__a += 1

    def decrement(self):
        with self.__lock:
            self.__a -= 1

    def __add__(self, other):
        with self.__lock:
            self.__a += other
        return self

    def __sub__(self, other):
        with self.__lock:
            self.__a -= other
        return self

    def __divmod__(self, other):
        with self.__lock:
            self.__a.__divmod__(other)
        return self

    def __mul__(self, other):
        with self.__lock:
            self.__a.__mul__(other)
        return self

    @property
    def value(self):
        return self.__a

    def __hash__(self):
        return self.__a.__hash__()


class LFUNode(Node):

    def __init__(self, key, value):
        super().__init__(key, value)
        self.frequency = Frequency()


class LFUCache(Cache):

    def get(self, key):
        node = self.map.get(key)
        if node:
            self.__freq(node)
            return node.value
        return None

    def put(self, key, value):

        node = self.map.get(key)
        if node:
            node.value = value
            self.__freq(node)
        else:
            if self.list.is_full():
                minum = min(self.frequency_map)
                node = self.frequency_map[minum].pop()
                del self.map[node.key]
            node = LFUNode(key, value)
            self.map[key] = node
            if node.frequency not in self.frequency_map:
                self.frequency_map[node.frequency] = DoubleList()
            self.frequency_map[node.frequency].append(node)

    def __init__(self):
        super().__init__()
        self.map = {}
        self.frequency_map = {}

    def __freq(self, node: LFUNode):
        """
        update frequency
        :param node:
        :return:
        """
        freq = node.frequency
        lst = self.frequency_map[freq]
        node = lst.remove(node)
        if lst.is_empty():
            del self.frequency_map[freq]
        freq.increment()
        if freq not in self.frequency_map:
            self.frequency_map[freq] = DoubleList()
        self.frequency_map[freq].append(node)
