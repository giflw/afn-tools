
from nextgen.keys.observing import Observable
from nextgen.keys import changes as cc
from collections import OrderedDict
from afn.utils.singleton import Singleton as _Singleton
from afn.utils import slicer

_NONE = _Singleton("nextgen.keys.types._NONE")

class ObservableDict(Observable, dict):
    def _get_current_values(self, value_list):
        value_list += self.itervalues()
        super(ObservableDict, self)._get_current_values(value_list)
    
    def __delitem__(self, key):
        value = self[key]
        super(ObservableDict, self).__delitem__(key)
        self._notify_changed([cc.KeyRemoved(self, key, value)])
    
    def __setitem__(self, key, value):
        exists = key in self
        if exists:
            old = self[key]
        super(ObservableDict, self).__setitem__(key, value)
        if exists:
            self._notify_changed([cc.KeyUpdated(self, key, old, value)])
        else:
            self._notify_changed([cc.KeyAdded(self, key, value)])
    
    def clear(self):
        items = self.items()
        super(ObservableDict, self).clear()
        self._notify_changed([cc.KeyRemoved(self, k, v) for (k, v) in items])
    
    def copy(self):
        return ObservableDict(self.iteritems())
    
    def pop(self, key, default=_NONE):
        if key not in self:
            if default is _NONE:
                raise KeyError(key)
            else:
                return default
        value = self[key]
        del self[key] # This will call __delitem__, which will handle posting
        # the KeyRemoved event
        return value
    
    def popitem(self):
        if len(self) == 0:
            raise KeyError()
        key, value = self.iteritems().next()
        del self[key] # This will handle posting the KeyRemoved event
        return key, value
    
    def setdefault(self, key, default=None):
        if key not in self:
            self[key] = default # This will handle posting the KeyAdded event
            return default
        return self[key]
    
    def update(self, e, **f):
        changes = []
        if hasattr(e, "keys"):
            for key in e:
                value = e[key]
                if key in self:
                    changes.append(cc.KeyUpdated(self, key, self[key], value))
                else:
                    changes.append(cc.KeyAdded(self, key, value))
                super(ObservableDict, self).__setitem__(key, value)
        else:
            for key, value in e:
                if key in self:
                    changes.append(cc.KeyUpdated(self, key, self[key], value))
                else:
                    changes.append(cc.KeyAdded(self, key, value))
                super(ObservableDict, self).__setitem__(key, value)
        for key, value in f.iteritems():
            if key in self:
                changes.append(cc.KeyUpdated(self, key, self[key], value))
            else:
                changes.append(cc.KeyAdded(self, key, value))
            super(ObservableDict, self).__setitem__(key, value)
        self._notify_changed(changes)
    
    def __str__(self):
        return self.__repr__()
    
    def __repr__(self):
        return "<ObservableDict: %s>" % super(ObservableDict, self).__repr__()


class ObservableList(Observable, list):
    def _get_current_values(self, value_list):
        value_list += self.itervalues()
        super(ObservableDict, self)._get_current_values(value_list)
    
    # TODO: finish this up, and use afn.utils.slicer to implement slicing, and
    # see if Py3 has that and submit it as a patch if it doesn't
    
    def __delitem__(self, s):
        if isinstance(s, (int, long)):
            s = slice(s, s + 1)
        indexes = list(slicer(len(self), s.start, s.stop, s.step))
        changes = [cc.ItemRemoved(self, i, self[i]) for i in indexes]
        super(ObservableList, self).__delitem__(s)
        self._notify_changed(changes)
    
    def __delslice__(self, start, stop):
        self.__delitem__(slice(start, stop))
    
    def __iadd__(self, items):
        index = len(self)
        super(ObservableList, self).__iadd__(items)
        changes = [cc.ItemInserted(self, i, self[i]) for i in range(index, len(self))]
        self._notify_changed(changes)
    
    def __imul__(self, number):
        index = len(self)
        super(ObservableList, self).__imul__(number)
        changes = [cc.ItemInserted(self, i, self[i]) for i in range(index, len(self))]
        self._notify_changed(changes)
    
    def __setitem__(self, s, item):
        if isinstance(s, (int, long)):
            old = self[s]
            super(ObservableList, self).__setitem__(s, item)
            self._notify_changed([cc.ItemUpdated(self, s, old, item)])
        else:
            raise NotImplementedError("Assignments to list slices of "
                                      "ObservableList instances haven't been "
                                      "implemented yet.")
    
    def __setslice__(self, start, stop, item):
        self.__setitem__(slice(start, stop), item)
    
    def append(self, item):
        super(ObservableList, self).append(item)
        self._notify_changed([cc.ItemInserted(self, len(self) - 1, item)])
    
    def extend(self, iterable):
        # As far as I can tell, extend and __iadd__ behave the exact same way
        self += iterable
    
    def insert(self, index, item):
        super(ObservableList, self).insert(index, item)
        self._notify_changed([cc.ItemInserted(self, index, item)])
    
    def pop(self, index=None):
        if index is None:
            index = len(self) - 1
        item = self.pop(index)
        self._notify_changed([cc.ItemRemoved(self, index, item)])
    
    def remove(self, value):
        del self[self.index(value)] # __del__ will handle posting the
        # ItemRemoved notification for us
    
    def reverse(self):
        super(ObservableList, self).reverse()
        length = len(self)
        highest = length - 1
        changes = [cc.ItemsSwapped(self, highest - i, i, self[i], self[highest - i]) for i in range(length / 2)]
        self._notify_changed(changes)
    
    def sort(self, *args):
        raise NotImplementedError("Sorting an OrderedList is not currently "
                                  "supported. It will be supported at some "
                                  "point in the near future.")










































