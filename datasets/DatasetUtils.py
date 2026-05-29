import csv


class DatasetUtils:
    def __init__(self, path: str, column: str, index: int = 0, window: int = 100):
        self.path = path
        self.column = column
        self.window = window
        self.current_index = index

        self.delimiter = self._detect_delimiter()
        self.headers = self._get_headers()

        if self.column not in self.headers:
            raise ValueError(f"Coluna '{self.column}' não encontrada no dataset.")

        self.column_position = self.headers.index(self.column)

        # Controle da janela
        self.window_start = None
        self.window_end = None
        self.buffer = []

        # Carrega a primeira janela
        self._load_window(self.current_index)

    def _detect_delimiter(self):
        with open(self.path, 'r', encoding='utf-8') as file:
            sample = file.readline()
            if sample.count(';') > sample.count(','):
                return ';'
            return ','

    def _get_headers(self):
        with open(self.path, 'r', encoding='utf-8') as file:
            reader = csv.reader(file, delimiter=self.delimiter)
            return next(reader)

    def _load_window(self, start_index: int):
        self.buffer = []
        self.window_start = start_index
        self.window_end = start_index + self.window

        with open(self.path, 'r', encoding='utf-8') as file:
            reader = csv.reader(file, delimiter=self.delimiter)
            next(reader)  # pula header

            for i, row in enumerate(reader):
                if i < self.window_start:
                    continue
                if i >= self.window_end:
                    break
                self.buffer.append(row[self.column_position])

    def getValue(self, index: int):
        # Se o índice estiver fora da janela atual, recarrega
        if (
            self.window_start is None or
            index < self.window_start or
            index >= self.window_end
        ):
            self._load_window(index)

        buffer_index = index - self.window_start

        if buffer_index < 0 or buffer_index >= len(self.buffer):
            return None
            #raise IndexError("Índice fora do range do dataset.")

        return self.buffer[buffer_index]
