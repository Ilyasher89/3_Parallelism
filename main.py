# Импортируем необходимые модули
import multiprocessing  # Для организации параллельных процессов
import random  # Для генерации случайных чисел
import time    # Для имитации времени работы и пауз
import sys     # Для работы с аргументами командной строки

# Функция генерации случайной квадратной матрицы заданного размера
def generate_random_matrix(size):
    """
    Генерирует случайную квадратную матрицу заданного размера.

    Параметры:
        size (int): Размерность матрицы (число строк и столбцов).

    Возвращает:
        list: Двумерный список (матрица) размером size x size, заполненный случайными числами.
    """
    # Создаем матрицу с помощью вложенных списков
    matrix = []
    for _ in range(size):
        # Генерируем строку матрицы
        row = [random.randint(0, 10) for _ in range(size)]
        matrix.append(row)
    return matrix

# Процесс-генератор матриц
def matrix_generator(queue, size, stop_event):
    """
    Генерирует пары случайных матриц и отправляет их в очередь для перемножения.

    Параметры:
        queue (multiprocessing.Queue): Очередь для передачи матриц.
        size (int): Размерность генерируемых матриц.
        stop_event (multiprocessing.Event): Событие для остановки генерации.
    """
    print("Запуск процесса генерации матриц.")
    while not stop_event.is_set():
        # Генерируем две случайные матрицы
        A = generate_random_matrix(size)
        B = generate_random_matrix(size)
        # Отправляем пару матриц в очередь
        queue.put((A, B))
        print("Сгенерированы две матрицы и отправлены в очередь.")
        # Имитация задержки между генерациями
        time.sleep(1)
    # После остановки генерации отправляем специальный сигнал (None) для завершения работы умножителя
    queue.put(None)
    print("Остановка процесса генерации матриц.")

# Процесс перемножения матриц
def matrix_multiplier(queue, stop_event):
    """
    Получает пары матриц из очереди, перемножает их и записывает результат в файл.

    Параметры:
        queue (multiprocessing.Queue): Очередь для получения матриц.
        stop_event (multiprocessing.Event): Событие для остановки умножения.
    """
    print("Запуск процесса перемножения матриц.")
    # Открываем файл для записи результатов
    with open('multiplication_results.txt', 'w') as result_file:
        while True:
            # Получаем пару матриц из очереди
            matrices = queue.get()
            # Проверяем специальный сигнал для завершения работы
            if matrices is None:
                print("Получен сигнал завершения умножения.")
                break
            A, B = matrices
            # Проверяем возможность перемножения матриц
            if len(A[0]) != len(B):
                print("Матрицы не могут быть перемножены: число столбцов A не равно числу строк B")
                continue
            # Перемножаем матрицы
            result_matrix = multiply_matrices(A, B)
            # Записываем результат в файл
            write_matrix_to_file(result_matrix, result_file)
            print("Матрицы перемножены и результат записан в файл.")
    print("Остановка процесса перемножения матриц.")

# Функция перемножения двух матриц
def multiply_matrices(A, B):
    """
    Перемножает две матрицы A и B.

    Параметры:
        A (list): Первая матрица.
        B (list): Вторая матрица.

    Возвращает:
        list: Результирующая матрица.
    """
    # Число строк и столбцов результирующей матрицы
    result_rows = len(A)
    result_cols = len(B[0])
    # Инициализируем результирующую матрицу нулями
    result_matrix = [[0 for _ in range(result_cols)] for _ in range(result_rows)]
    # Выполняем умножение матриц
    for i in range(result_rows):
        for j in range(result_cols):
            for k in range(len(B)):
                result_matrix[i][j] += A[i][k] * B[k][j]
    return result_matrix

# Функция записи матрицы в файл
def write_matrix_to_file(matrix, file):
    """
    Записывает матрицу в файл.

    Параметры:
        matrix (list): Матрица для записи.
        file (file object): Открытый файл для записи.
    """
    for row in matrix:
        # Преобразуем числа в строки
        str_numbers = [str(num) for num in row]
        # Объединяем числа через пробел и добавляем перевод строки
        line = ' '.join(str_numbers) + '\n'
        # Записываем строку в файл
        file.write(line)
    # Добавляем разделитель между матрицами
    file.write('=' * 20 + '\n')

# Главная функция программы
def main():
    """
    Основная функция программы.

    Организует процессы генерации и перемножения матриц, а также механизм остановки.
    """
    # Проверяем наличие аргумента командной строки для размерности матриц
    if len(sys.argv) != 2:
        print("Использование: python программа.py размерность_матрицы")
        sys.exit(1)
    # Получаем размерность матрицы из аргументов командной строки
    try:
        matrix_size = int(sys.argv[1])
    except ValueError:
        print("Размерность матрицы должна быть целым числом.")
        sys.exit(1)
    # Создаем очередь для передачи матриц между процессами
    queue = multiprocessing.Queue()
    # Создаем событие для остановки процессов
    stop_event = multiprocessing.Event()
    # Создаем процессы генерации и умножения матриц
    generator_process = multiprocessing.Process(target=matrix_generator, args=(queue, matrix_size, stop_event))
    multiplier_process = multiprocessing.Process(target=matrix_multiplier, args=(queue, stop_event))
    # Запускаем процессы
    generator_process.start()
    multiplier_process.start()
    # Организуем механизм остановки по пользовательскому вводу
    try:
        while True:
            # Ожидаем ввода команды от пользователя
            command = input("Введите 'stop' для остановки программы: ")
            if command.strip().lower() == 'stop':
                # Устанавливаем событие остановки
                stop_event.set()
                print("Инициирована остановка программы.")
                break
    except KeyboardInterrupt:
        # Обработка прерывания программы (Ctrl+C)
        stop_event.set()
        print("\nПрограмма прервана пользователем.")
    # Ожидаем завершения процессов
    generator_process.join()
    multiplier_process.join()
    print("Программа завершена.")

# Запускаем главную функцию, если скрипт запущен напрямую
if __name__ == '__main__':
    main()