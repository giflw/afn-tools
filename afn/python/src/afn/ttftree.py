"""
Experimental implementation of functional 2-3 finger trees that I'm working on.

I'm hoping to replace stm.avl with these, which'll give O(1) list insertion,
appending, and removal from either end to stm.tlist.TList.

I'm also planning on implementing custom measures (which could also be done
with stm.avl), which'll give the ability for, e.g., an ordered list to also
function as a priority queue.
"""

# Credit goes to http://maniagnosis.crsr.net/2010/11/finger-trees.html for
# giving my brain just the right information it needed to finally understand
# 2-3 finger trees 

from collections import Sequence

class TTFTreeError(Exception):
    pass


class TreeIsEmpty(TTFTreeError):
    """
    Exception raised from within Empty when things like get_first or
    without_first are called on it.
    """
    def __str__(self):
        return "This tree is empty"


class Measure(object):
    """
    An object used to compute a tree's annotation.
    
    Measures consist of a function capable of converting values in a tree to
    values in a particular monoid (the convert attribute of Measure objects)
    and the monoid's binary operation (the operator attribute) and identity
    element (the identity attribute). The value of any given tree is the
    monoidal sum of the values produced by the conversion function for all
    values contained within the tree.
    """
    def __init__(self, convert, operator, identity):
        self.convert = convert
        self.operator = operator
        self.identity = identity
    
    def __repr__(self):
        return "<Measure: convert=%r, operator=%r, identity=%r>" % (self.convert, self.operator, self.identity)


MEASURE_ITEM_COUNT = Measure(lambda v: 1, lambda a, b: a + b, 0)


def create_node_measure(measure):
    """
    Given a particular measure, return an identical measure that operates on
    Node objects containing values accepted by the given measure.
    """
    return Measure(lambda node: node.annotation, measure.operator, measure.identity)


class Node(Sequence):
    def __init__(self, measure, *values):
        if len(values) not in (2, 3):
            raise Exception("Nodes must have 2 or 3 children")
        self._values = values
        self.measure = measure
        self.annotation = reduce(measure.operator, map(measure.convert, values))
    
    def __getitem__(self, index):
        if isinstance(index, slice):
            return Node(self.measure, *self._values[index])
        else:
            return self._values[index]
    
    def __len__(self):
        return len(self._values)
    
    def __add__(self, other):
        return Node(self.measure, *self._values + other._values)
    
    def __repr__(self):
        return "<Node: %s>" % ", ".join([repr(v) for v in self])


class Digit(Sequence):
    def __init__(self, measure, *values):
        if len(values) not in (1, 2, 3, 4):
            raise Exception("Digits must have 1, 2, 3, or 4 children; the "
                            "children given were %r" % list(values))
        self._values = values
        self.measure = measure
        self.annotation = reduce(measure.operator, map(measure.convert, values))
    
    def partition_digit(self, initial_annotation, predicate):
        """
        partition_digit(function) => ((...), (...))
        
        Note that the two return values are tuples, not Digits, as they may
        need to be empty.
        """
        split_point = 0
        while split_point < len(self):
            current_annotation = self.measure.operator(initial_annotation, self.measure.convert(self[split_point]))
            if predicate(current_annotation):
                break
            else:
                split_point += 1
                initial_annotation = current_annotation
        return self._values[:split_point], self._values[split_point:]
    
    def __getitem__(self, index):
        if isinstance(index, slice):
            return Digit(self.measure, *self._values[index])
        else:
            return self._values[index]
    
    def __len__(self):
        return len(self._values)
    
    def __add__(self, other):
        return Digit(self.measure, *self._values + other._values)
    
    def __repr__(self):
        return "<Digit: %s>" % ", ".join([repr(v) for v in self])


class Tree(object):
    # is_empty -> bool
    
    # get_first() -> item
    # without_first() -> Tree
    # add_first(item) -> Tree
    # get_last() -> item
    # without_last() -> Tree
    # add_last(item) -> Tree
    
    # append(tree) -> Tree
    # prepend(tree) -> Tree
    pass


def to_tree(measure, sequence):
    tree = Empty(measure)
    for value in sequence:
        tree = tree.add_last(value)
    return tree


class Empty(Tree):
    is_empty = True
    
    def __init__(self, measure):
        self.measure = measure
        self.annotation = measure.identity
    
    def get_first(self):
        raise TreeIsEmpty
    
    def without_first(self):
        raise TreeIsEmpty
    
    def add_first(self, item):
        return Single(self.measure, item)
    
    def get_last(self):
        raise TreeIsEmpty
    
    def without_last(self):
        raise TreeIsEmpty
    
    def add_last(self, item):
        return Single(self.measure, item)
    
    def prepend(self, other):
        return other
    
    def append(self, other):
        return other
    
    def iterate_values(self):
        if False:
            yield None
    
    def partition(self, initial_annotation, predicate):
        return self, self
    
    def __repr__(self):
        return "<Empty>"


class Single(Tree):
    is_empty = False
    
    def __init__(self, measure, item):
        self.measure = measure
        self.annotation = measure.convert(item)
        self.item = item
    
    def get_first(self):
        return self.item
    
    def without_first(self):
        return Empty(self.measure)
    
    def add_first(self, new_item):
        return Deep(self.measure, Digit(self.measure, new_item), Empty(create_node_measure(self.measure)), Digit(self.measure, self.item))
    
    def get_last(self):
        return self.item
    
    def without_last(self):
        return Empty(self.measure)
    
    def add_last(self, new_item):
        return Deep(self.measure, Digit(self.measure, self.item), Empty(create_node_measure(self.measure)), Digit(self.measure, new_item))
    
    def prepend(self, other):
        return other.add_last(self.item)
    
    def append(self, other):
        return other.add_first(self.item)
    
    def iterate_values(self):
        yield self.item
    
    def partition(self, initial_annotation, predicate):
        if predicate(self.measure.operator(initial_annotation, self.annotation)):
            return Empty(self.measure), self
        else:
            return self, Empty(self.measure)
    
    def __repr__(self):
        return "<Single: %r>" % (self.item,)


def deep_left(measure, maybe_left, spine, right):
    if not maybe_left:
        if spine.is_empty:
            return to_tree(measure, right)
        else:
            return Deep(measure, Digit(measure, *spine.get_first()), spine.without_first(), right)
    else:
        return Deep(measure, Digit(measure, *maybe_left), spine, right)


def deep_right(measure, left, spine, maybe_right):
    if not maybe_right:
        if spine.is_empty:
            return to_tree(measure, left)
        else:
            return Deep(measure, left, spine.without_last(), Digit(measure, *spine.get_last()))
    else:
        return Deep(measure, left, spine, Digit(measure, *maybe_right))


class Deep(Tree):
    is_empty = False
    
    def __init__(self, measure, left, spine, right):
        self.measure = measure
        self.annotation = measure.operator(measure.operator(left.annotation, spine.annotation), right.annotation)
        self.left = left
        self.spine = spine
        self.right = right
    
    def get_first(self):
        return self.left[0]
    
    def without_first(self):
        if len(self.left) > 1:
            return Deep(self.measure, self.left[1:], self.spine, self.right)
        elif not self.spine.is_empty:
            return Deep(self.measure, Digit(self.measure, *self.spine.get_first()), self.spine.without_first(), self.right)
        elif len(self.right) == 1:
            return Single(self.measure, self.right[0])
        elif len(self.right) == 2:
            return Deep(self.measure, self.right[0:1], self.spine, self.right[1:2])
        elif len(self.right) == 3:
            return Deep(self.measure, self.right[0:2], self.spine, self.right[2:3])
        elif len(self.right) == 4:
            return Deep(self.measure, self.right[0:2], self.spine, self.right[2:4])
    
    def add_first(self, new_item):
        if len(self.left) < 4:
            return Deep(self.measure, Digit(self.measure, new_item) + self.left, self.spine, self.right)
        else:
            node = Node(self.measure, self.left[1], self.left[2], self.left[3])
            return Deep(self.measure, Digit(self.measure, new_item, self.left[0]), self.spine.add_first(node), self.right)
    
    def get_last(self):
        return self.right[-1]
    
    def without_last(self):
        if len(self.right) > 1:
            return Deep(self.measure, self.left, self.spine, self.right[:-1])
        elif not self.spine.is_empty:
            return Deep(self.measure, self.left, self.spine.without_last(), Digit(self.measure, *self.spine.get_last()))
        elif len(self.left) == 1:
            return Single(self.measure, self.left[0])
        elif len(self.left) == 2:
            return Deep(self.measure, self.left[0:1], self.spine, self.left[1:2])
        elif len(self.left) == 3:
            return Deep(self.measure, self.left[0:1], self.spine, self.left[1:3])
        elif len(self.left) == 4:
            return Deep(self.measure, self.left[0:2], self.spine, self.left[2:4])
    
    def add_last(self, new_item):
        if len(self.right) < 4:
            return Deep(self.measure, self.left, self.spine, self.right + Digit(self.measure, new_item))
        else:
            node = Node(self.measure, self.right[0], self.right[1], self.right[2])
            return Deep(self.measure, self.left, self.spine.add_last(node), Digit(self.measure, self.right[3], new_item))
    
    def prepend(self, other):
        return other.append(self)
    
    def append(self, other):
        """
        Concatenate the specified tree onto the end of this tree.
        
        Time complexity: O(log min(m, n)), i.e. logarithmically in the size of
        the smaller of self and other.
        """
        if not isinstance(other, Deep):
            return other.prepend(self)
        return Deep(self.measure, self.left, self._fold_up(self, other), other.right)
    
    def _fold_up(self, left_tree, right_tree):
        middle_items = list(left_tree.right) + list(right_tree.left)
        spine = left_tree.spine
        while middle_items:
            # Could be optimized to not remove items from the front of a list,
            # which is a bit slow; perhaps reverse middle_items and pop from
            # the end of the list, or use a sliding index that we increment as
            # we go and don't modify the list at all
            if len(middle_items) == 2:
                spine = spine.add_last(Node(self.measure, middle_items[0], middle_items[1]))
                del middle_items[0:2]
            elif len(middle_items) == 4:
                spine = spine.add_last(Node(self.measure, middle_items[0], middle_items[1]))
                spine = spine.add_last(Node(self.measure, middle_items[2], middle_items[3]))
                del middle_items[0:4]
            else:
                spine = spine.add_last(Node(self.measure, middle_items[0], middle_items[1], middle_items[2]))
                del middle_items[0:3]
        return spine.append(right_tree.spine)
    
    def iterate_values(self):
        for v in self.left:
            yield v
        for node in self.spine.iterate_values():
            for v in node:
                yield v
        for v in self.right:
            yield v
    
    def partition(self, initial_annotation, predicate):
        left_annotation = self.measure.operator(initial_annotation, self.left.annotation)
        spine_annotation = self.measure.operator(left_annotation, self.spine.annotation)
        # right_annotation = self.measure.operator(spine_annotation, self.right.annotation)
        if predicate(left_annotation):
            # Split is in the left measure
            left_items, right_items = self.left.partition_digit(initial_annotation, predicate)
            return to_tree(self.measure, left_items), deep_left(self.measure, right_items, self.spine, self.right)
        elif predicate(spine_annotation):
            # Split is somewhere in the spine
            left_spine, right_spine = self.spine.partition(left_annotation, predicate)
            # Rightmost node in right_spine is the one where the predicate
            # became true (and note that right_spine will never be empty; if it
            # were, the predicate wouldn't have become true on our spine at
            # all), so we need to extract it and split it up.
            split_node = right_spine.get_first()
            right_spine = right_spine.without_first()
            before_digit, after_digit = Digit(self.measure, *split_node).partition_digit(self.measure.operator(left_annotation, left_spine.annotation), predicate)
            return deep_right(self.measure, self.left, left_spine, before_digit), deep_left(self.measure, after_digit, right_spine, self.right)
        else:
            left_items, right_items = self.right.partition_digit(spine_annotation, predicate)
            return deep_right(self.measure, self.left, self.spine, left_items), to_tree(self.measure, right_items)
    
    def __repr__(self):
        return "<Deep: left=%r, spine=%r, right=%r>" % (self.left, self.spine, self.right)


def value_iterator(tree):
    """
    A generator function that yields each value from the given tree in
    succession.
    
    Each item is yielded in amortized constant time.
    
    The returned iterator only holds references to values that have yet to be
    produced; values earlier on in the tree will not be held on to, and as such
    can be garbage collected if nothing else holds references to them.
    """
    while not tree.is_empty:
        yield tree.get_first()
        tree = tree.without_first()
    





















