class EmptyXMLError(ValueError):
    """Ошибка пустого XML-файла."""


class InvalidXMLError(ValueError):
    """Ошибка невалидного XML-файла."""


class TableNameError(ValueError):
    """Ошибка отсутствующей таблицы."""


class EmptyFeedsListError(ValueError):
    """Ошибка пустой коллекции с фидами."""


class DirectoryCreationError(ValueError):
    """Ошибка создания дериктории."""


class GetTreeError(ValueError):
    """Ошибка получения дерева XML-файла."""


class SaveDataBaseError(ValueError):
    """Ошибка сохранения данных в бд."""


class CleanDataBaseError(ValueError):
    """Ошибка удаления данных из бд."""


class StructureXMLError(ValueError):
    """Ошибка структуры XML-файла."""
