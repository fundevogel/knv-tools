from abc import ABC, abstractmethod


class Maker(ABC):
    # CORE methods

    @abstractmethod
    def build(self) -> None:
        pass
