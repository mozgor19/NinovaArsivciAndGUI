# Bismillahirrahmanirrahim

# Utility functions for debugging, verbose logging, colored terminal output, and performance measurement.

from time import perf_counter

class Logger:
    _FAIL = "\033[91m"
    _ENDC = "\033[0m"
    _WARNING = "\033[93m"
    _GREEN = '\033[92m'
    
    def __init__(self, debug=False, verbose=False, file_name_max_length=30):
        self._DEBUG = debug
        self._VERBOSE = verbose
        self._FILE_NAME_MAX_LENGTH = file_name_max_length

    def enable_debug(self):
        self._DEBUG = True

    def enable_verbose(self):
        self._VERBOSE = True

    def fail(self, message):
        print("HATA! " + self._FAIL + message + self._ENDC)
        exit()

    def warning(self, message):
        print("UYARI! " + self._WARNING + message + self._ENDC)

    def verbose(self, message):
        if self._VERBOSE:
            print("INFO: " + message)

    def new_file(self, file_path):
        print(self._GREEN + "Yeni: " + file_path + self._ENDC)

    def debug(self, message):
        if self._DEBUG:
            print("UUT:  " + message)

    def speed_measure(self, debug_name: str, is_level_debug: bool, return_is_debug_info: bool = False):
        def decorator(func):
            def wrapper(*args, **kwargs):
                start = perf_counter()
                return_val = func(*args, **kwargs)
                end = perf_counter()

                additional_info = return_val[0] if return_is_debug_info else ""

                if is_level_debug:
                    self.debug(f"{additional_info[:self._FILE_NAME_MAX_LENGTH]:<30} {debug_name} {end-start} saniyede tamamlandı.")
                else:
                    self.verbose(f"{additional_info[:self._FILE_NAME_MAX_LENGTH]:<30} {debug_name} {end-start} saniyede tamamlandı.")

                return return_val

            return wrapper
        return decorator
