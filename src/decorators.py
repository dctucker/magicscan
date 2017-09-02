import time
from colorama import init, Fore, Style
init()

def timed(text):
	def decorator(func):
		def wrapper(*args, **kwargs):
			t1 = time.time()
			result = func(*args, **kwargs)
			t2 = time.time()
			print Fore.CYAN + text + ":", str(round(t2 - t1, 3)) + 's' + Style.RESET_ALL
			return result
		return wrapper
	return decorator

