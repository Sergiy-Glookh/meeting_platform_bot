import threading
import time
import speech_recognition as sr
from pydub import AudioSegment

audio_name = "test2"
audio = AudioSegment.from_mp3(f'{audio_name}.mp3')
audio.export(f"{audio_name}.wav", format="wav")

recognizer = sr.Recognizer()
with sr.AudioFile(f"{audio_name}.wav") as source:
    # Читаємо аудіофайл
    audio_data = recognizer.record(source)

available_languages = ['uk-UA', 'ru-RU']
text_results = [None] * len(available_languages)
def recognize_language(language, audio_data, results, index):
        start_time = time.time()
        text = recognizer.recognize_google(audio_data, language=language)
        results[index] = text
        end_time = time.time()
        print(f"Execution time for index {index}: {end_time - start_time:.2f} seconds")

# Створюємо потоки для розпізнавання для кожної мови
threads = []
for i, language in enumerate(available_languages):
    thread = threading.Thread(target=recognize_language, args=(language, audio_data, text_results, i))
    threads.append(thread)
    thread.start()

# Чекаємо, поки всі потоки завершаться
for thread in threads:
    thread.join()
print(threads)
if len(text_results[0]) > len(text_results[1]):
    print("UA Result:\n", text_results[0])
else:
    print("RU Result:\n", text_results[1])