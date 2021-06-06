from ..components import Molecule


class Payments(Molecule):
    # CORE methods

    def export(self) -> list:
        data = []

        for child in self._children:
            data.append(child.export())

        return data
