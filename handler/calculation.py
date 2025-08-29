import numpy as np

from handler.constants import (
    DECIMAL_ROUNDING,
    LOWER_OUTLIER_PERCENTILE,
    UPPER_OUTLIER_PERCENTILE
)


def calc_quantile(data):
    """
    Удаляет выбросы с помощью метода межквартильного размаха (IQR).
    Args:
        data: Входные данные.
    Returns:
        Отфильтрованный массив без выбросов.
    """
    array = np.array(data)
    Q1 = np.quantile(array, LOWER_OUTLIER_PERCENTILE)
    Q3 = np.quantile(array, UPPER_OUTLIER_PERCENTILE)
    IQR = Q3 - Q1
    lower_outlier_threshold = Q1 - 1.5 * IQR
    upper_outlier_threshold = Q3 + 1.5 * IQR
    filtered_data = array[
        (array >= lower_outlier_threshold) & (array <= upper_outlier_threshold)
    ]
    return filtered_data.tolist()


def clear_min(data):
    """Находит минимальное значение в коллекции без выбросов."""
    filtered_data = calc_quantile(data)
    return min(filtered_data)


def clear_max(data):
    """Находит максимальное значение в коллекции без выбросов."""
    filtered_data = calc_quantile(data)
    return max(filtered_data)


def clear_median(data):
    """Находит медиану в коллекции без выбросов."""
    filtered_data = calc_quantile(data)
    return np.median(filtered_data)


def clear_avg(data):
    """Находит среднее значение в коллекции без выбросов."""
    filtered_data = calc_quantile(data)
    return round(sum(filtered_data) / len(filtered_data), DECIMAL_ROUNDING)
