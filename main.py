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
    matrix = []
    for _ in range(size):
        row = [random.randint(0, 10) for _ in range(size)]
        matrix.append(row)
    return matrix

# Процесс-генератор матриц
def matrix_generator(queue, size, stop_event):
    """
    Генерирует пары случайных матриц и отправляет их в очередь для перемножения.
    """
    # Игнорируем сигнал SIGINT в дочернем процессе
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    print("Запуск процесса генерации матриц.")
    try:
        while not stop_event.is_set():
            A = generate_random_matrix(size)
            B = generate_random_matrix(size)
            queue.put((A, B))
            print("Сгенерированы две матрицы и отправлены в очередь.")
            time.sleep(1)
    except Exception as e:
        print(f"Процесс генерации матриц прерван: {e}")
    finally:
        # Отправляем сигнал завершения
        queue.put(None)
        print("Остановка процесса генерации матриц.")

# Процесс перемножения матриц
def matrix_multiplier(queue, stop_event):
    """
    Получает пары матриц из очереди, перемножает их и записывает результат в файл.
    """
    # Игнорируем сигнал SIGINT в дочернем процессе
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    print("Запуск процесса перемножения матриц.")
    try:
        with open('multiplication_results.txt', 'w') as result_file:
            while True:
                if stop_event.is_set() and queue.empty():
                    break
                try:
                    matrices = queue.get(timeout=1)
                except Queue.Empty:
                    continue
                if matrices is None:
                    print("Получен сигнал завершения умножения.")
                    break
                A, B = matrices
                if len(A[0]) != len(B):
                    print("Матрицы не могут быть перемножены: число столбцов A не равно числу строк B")
                    continue
                result_matrix = multiply_matrices(A, B)
                write_matrix_to_file(result_matrix, result_file)
                print("Матрицы перемножены и результат записан в файл.")
    except Exception as e:
        print(f"Процесс перемножения матриц прерван: {e}")
    finally:
        print("Остановка процесса перемножения матриц.")

# Функция перемножения двух матриц
def multiply_matrices(A, B):
    """
    Перемножает две матрицы A и B.
    """
    result_rows = len(A)
    result_cols = len(B[0])
    result_matrix = [[0 for _ in range(result_cols)] for _ in range(result_rows)]
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
        str_numbers = [str(num) for num in row]
        line = ' '.join(str_numbers) + '\n'
        file.write(line)
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
            # Игнорируем KeyboardInterrupt в потоке ввода
            break

# Функция для обработки сигналов прерывания
def signal_handler(sig, frame):
    global signal_received
    if not signal_received:
        print("\nПолучен сигнал прерывания. Программа завершается.")
        signal_received = True
        # Устанавливаем событие остановки
        stop_event.set()

# Главная функция программы
def main():
    """
    Основная функция программы.
    """
    # Глобальное событие остановки
    global stop_event
    stop_event = threading.Event()

    global signal_received
    signal_received = False

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

    # Создаем событие остановки для процессов
    process_stop_event = multiprocessing.Event()

    # Создаем процессы генерации и умножения матриц
    generator_process = multiprocessing.Process(target=matrix_generator, args=(queue, matrix_size, process_stop_event))
    multiplier_process = multiprocessing.Process(target=matrix_multiplier, args=(queue, process_stop_event))

    # Запускаем процессы
    generator_process.start()
    multiplier_process.start()

    # Запускаем поток для ввода команды от пользователя
    input_thread = threading.Thread(target=user_input_thread, args=(stop_event,))
    input_thread.start()

    # Ожидаем установки события остановки
    while not stop_event.is_set():
        time.sleep(0.1)

    # Устанавливаем событие остановки для процессов
    process_stop_event.set()

    # Ожидаем завершения потока ввода
    input_thread.join()

    # Ожидаем завершения процессов
    generator_process.join()
    multiplier_process.join()

    print("Программа завершена.")

# Запускаем главную функцию, если скрипт запущен напрямую
if __name__ == '__main__':
    main()