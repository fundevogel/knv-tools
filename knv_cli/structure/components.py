# Works with Python v3.10+
# See https://stackoverflow.com/a/33533514
from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import List


class Component(metaclass=ABCMeta):
    # PROPS

    @property
    def parent(self) -> Component:
        return self._parent


    @parent.setter
    def parent(self, parent: Component):
        self._parent = parent


    # CORE methods

    @abstractmethod
    def export(self) -> None:
        pass


class Molecule(Component):
    def __init__(self):
        self._children: List[Component] = []


    # ADMINISTRATION methods

    def add(self, component):
        self._children.append(component)
        component.parent = self


    def remove(self, component):
        self._children.remove(component)
        component.parent = None


    # CORE methods

    @abstractmethod
    def export(self) -> None:
        pass


class Atom(Component):
    # CORE methods

    @abstractmethod
    def export(self) -> None:
        pass
