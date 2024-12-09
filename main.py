import multiprocessing  # Для организации параллельных процессов
import random  # Для генерации случайных чисел
import time    # Для имитации времени работы и пауз
import sys     # Для работы с аргументами командной строки
import threading  # Для запуска потока ввода команды
import queue as Queue  # Для безопасной передачи данных между потоками
import signal  # Для обработки сигналов прерывания

# Функция генерации случайной квадратной матрицы заданного размера
def generate_random_matrix(size):
    """
    Генерирует случайную квадратную матрицу заданного размера.
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
    """
    print("Запуск процесса генерации матриц.")
    try:
        while not stop_event.is_set():
            # Генерируем две случайные матрицы
            A = generate_random_matrix(size)
            B = generate_random_matrix(size)
            # Отправляем пару матриц в очередь
            queue.put((A, B))
            print("Сгенерированы две матрицы и отправлены в очередь.")
            # Имитация задержки между генерациями
            time.sleep(1)
    except KeyboardInterrupt:
        print("Процесс генерации матриц прерван.")
    finally:
        # После остановки генерации отправляем специальный сигнал (None) для завершения работы умножителя
        queue.put(None)
        print("Остановка процесса генерации матриц.")

# Процесс перемножения матриц
def matrix_multiplier(queue, stop_event):
    """
    Получает пары матриц из очереди, перемножает их и записывает результат в файл.
    """
    print("Запуск процесса перемножения матриц.")
    try:
        # Открываем файл для записи результатов
        with open('multiplication_results.txt', 'w') as result_file:
            while True:
                # Проверяем, установлен ли сигнал остановки и пуста ли очередь
                if stop_event.is_set() and queue.empty():
                    break
                try:
                    # Устанавливаем таймаут, чтобы можно было проверить stop_event
                    matrices = queue.get(timeout=1)
                except Queue.Empty:
                    continue
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
    except KeyboardInterrupt:
        print("Процесс перемножения матриц прерван.")
    finally:
        print("Остановка процесса перемножения матриц.")

# Функция перемножения двух матриц
def multiply_matrices(A, B):
    """
    Перемножает две матрицы A и B.
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

# Функция для обработки пользовательского ввода в отдельном потоке
def user_input_thread(stop_event):
    """
    Ожидает ввода команды 'stop' для остановки программы.
    """
    while not stop_event.is_set():
        try:
            command = input("Введите 'stop' для остановки программы: ")
            if command.strip().lower() == 'stop':
                stop_event.set()
                print("Инициирована остановка программы.")
                break
        except EOFError:
            break
        except KeyboardInterrupt:
            stop_event.set()
            print("\nПрограмма прервана пользователем.")
            break

# Функция для обработки сигналов прерывания
def signal_handler(sig, frame):
    print("\nПолучен сигнал прерывания. Программа завершается.")
    # Устанавливаем событие остановки
    global stop_event
    stop_event.set()

# Главная функция программы
def main():
    """
    Основная функция программы.
    """
    # Глобальное событие остановки
    global stop_event
    stop_event = multiprocessing.Event()

    # Устанавливаем обработчик сигналов
    signal.signal(signal.SIGINT, signal_handler)

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
    # Создаем процессы генерации и умножения матриц
    generator_process = multiprocessing.Process(target=matrix_generator, args=(queue, matrix_size, stop_event))
    multiplier_process = multiprocessing.Process(target=matrix_multiplier, args=(queue, stop_event))
    # Запускаем процессы
    generator_process.start()
    multiplier_process.start()
    # Запускаем поток для ввода команды от пользователя
    input_thread = threading.Thread(target=user_input_thread, args=(stop_event,))
    input_thread.start()
    # Ожидаем завершения потока ввода
    input_thread.join()
    # Ожидаем завершения процессов
    generator_process.join()
    multiplier_process.join()
    print("Программа завершена.")

# Запускаем главную функцию, если скрипт запущен напрямую
if __name__ == '__main__':
    main()