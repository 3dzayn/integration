# -*- coding: utf-8 -*-

"""
Пример добавления сообщения типа "Отчет".
Этот модуль демонстритует, как можно устанавливать соединение с базой данных,
создавать сообщения и прикладывать файлы без использования графического интерфейса Cerebro.
Его можно использовать, например, для создания отчетов из Nuke, Maya и других программных продуктов,
в которых возможно исполнение питоновских скриптов.

Модуль использует пакет py_cerebro2 (для Python 2.x), который входит в дистрибутив service-tools (http://cerebrohq.com/distribs/service-tools.zip).
Пакет py_cerebro2 содержит модули для установки соединения с базой данных
и для доступа к файловому хранилищу(Cargador).
Пакет py_cerebro2 использует сторонний пакет psycopg2 (http://initd.org/psycopg/) 
для осущевстления доступа к базе данных PostgreSQL. Возможно вам придется дополнительно установить этот пакет.
Psycopg2 поставляется в дистрибутиве для всех операционных систем (папка py-site-packages). Также его можно
скачать с сайта разработчика (http://initd.org/psycopg/).

Модуль содержит следующие функции:

add_report_to_task - функция для добавления сообщения с приложенным файлом.
get_task_and_message_ids - получение идентификаторов задачи и её сообщения типа "Постановка задачи" по локатору(пути) задачи.
make_thumnails - для генерации эскизов к видео файлам и изображениям.

Для добавления сообщения необходимо вызвать функцию add_report_to_task
и передать ей необходимые параметры.
"""

import fnmatch
import sys
import os
import subprocess

local_dir = os.path.realpath(__file__).replace('\\', '/').rsplit('/', 1)[0]
backend_dir = local_dir + '/../..'
sys.path.append(backend_dir)

from py_cerebro2 import dbtypes, database, cargador, cclib # в этом модуле описаны различные константы, такие как поля данных, флаги и т.п.


# Переменные, которые вам возможно придется изменить, чтобы преспособить сктипт для вашей сети
mirada_path = '//ss/front/releases/images/win32/mirada.exe' # Путь, откуда запускать мираду для генерации эскизов.
#У вас этот параметр скорее всего будет иным.

#Следующие два параметра, хост и порт - это наш главный сервер с базой данных.
#У вас эти параметры могут быть иными, если вы используете свою базу данных
database_host = 'cerebrohq.com'
database_port = 45432

cargador_host = 'ss' # Cетевой адрес машины, где работает севрис каргадор.
# Может быть задано сетевое имя или IP адрес. 'ss' - это имя нашего сервера, у вас этот параметр скорее всего будет иным.

cargador_xmlrpc_port = 4040 # Порт 4040 - это порт для запросов по xmlrpc протоколу.
#У вас порт может быть иным, подробнее об этом смотрите в комментариях модуля cargador пакета py_cerebro2.

cargador_http_port = 4080 # Порт 4080 - это порт для запросов по http протоколу.
#У вас порт может быть иным, подробнее об этом смотрите в комментариях модуля cargador пакета py_cerebro2.



def add_report_to_task(task_url, db_user, db_password, text, work_time, file, file_as_link):
	"""
	Функция по добавлению нового сообщения.
	
	Параметр task_url - тектовый локатор(путь) до задачи.
	
	Формат локатора: '/Проект/Задача 1/Задача 2', то есть по сути путь до задачи.
	Примечание: Имена задач регистрозависимы!

	Параметры db_user и db_password - логин и пароль пользователя Cerebro, который создает отчет.

	Параметр text - текс сообщения
	Параметр work_time - затраченные часы
	Параметр file - путь до файла, который должен быть приложен
	Параметр file_as_link - способ добавления файла к сообщению:
		True - файл добавляется как ссылка;
		False - файл добавляется как вложение, то есть импортируется в файловое хранилище(Cargador).

	Пример вызова функции:
	::
		import report

		report.add_report_to_task('/Проект/Задача 1/Задача 2', 'user', 'password', 'Example report', 1.5, 'с:/temp/Test.file', False)
	::
	"""

	try:

		db = database.Database(database_host, database_port)
		# Устанавливаем соединение с базой данных
		if db.connect_from_cerebro_client() != 0: # пробуем установить соединение с помощью запущенного клиента Cerebro. 
			# Если не выходит, устанавливаем соединение с помощью логина и пароля
			db.connect(db_user, db_password) 
		
		# Получение идентификатора задачи и сообщения типа "Постановка задачи" по локатору задачи
		task = db.task_by_url(task_url) # Получили ID задач
		if len(task) == 0 or task[0] == None: # Проверяем существуют ли задачи с таким локатором
			raise Exception('Задача не найдена')

		messages = db.task_definition(task[0]) # Получили сообщения задачи
		if len(messages) == 0: # Проверяем есть ли у задачи сообщения
			raise Exception('Сообщение отсутствует')
		
		parent_message = messages[dbtypes.MESSAGE_DATA_ID] # Получили ID сообщения
		if parent_message == None or parent_message == 0:
			raise Exception('Сообщение отсутствует')
		"""
		Параметры task и parent_message - это идентификаторы задачи и сообщения к которому добавляется новое сообщение.
		"""
		
		# Создание сообщения типа "Отчет"
		new_message_id = db.add_report(task[0], parent_message, text, int(work_time*60))
		"""
		Выполняем запрос на добавление нового соообщения.		
		Последний параметр, затраченное время, задается в минутах
		Результатом запроса является идентификатор нового сообщения
		"""

		# Приложение файла к отчету
		if file != None and len(file) != 0 and os.path.exists(file): # проверяем, задан ли файл, который нужно приложить к отчету
			
			# генерация эскизов для файла file
			thumbnails = make_thumnails(file) 
			"""
			Если файл является изображением или видео, то можно добавить для него уменшенные эскизы.
			Можно добавить до 3-х эскизов (первый, средний, последний кадры).
			Для генерации эскизов в этом примере мы будем использовать программу Mirada.
			Она постовляется вместе с дистрибутивом Cerebro. Можно использовать и другие программы для генерации,
			например, ffmpeg. Смотрите подробнее об этом в описании функции make_thumnails.
			"""
			
			# Создаем объект для добавления файла и/или эскизов в файловое хранилище (Cargador)
			carga = cargador.Cargador(cargador_host, cargador_xmlrpc_port,  cargador_http_port)
			"""
			Если файл прикладывается как ссылка, то сам файл не будет
			"""
	
			# Добовляем к отчету постановки задач файлы и, заодно, экспортируем их в хранилище
			db.add_attachment(new_message_id, carga, file, thumbnails,  '',  file_as_link)	
			"""
			Если файл прикладывается как ссылка, то сам файл не будет экспортироваться в хранилище,
			но будут экспортированы эскизы.
			
			Пустая строка - это комментарий к вложению. Можете его задать по желанию.
			"""
			
	except BaseException as err:
		print(err)
		raise


def make_thumnails(filename):
	"""
	Принимает на вход полный путь до файла видео или изображения и генерирует эскизы к ним
	Возвращает список путей до файлов эскизов.	

	Генерация эскизов:			
	Если файл является изображением или видео, то можно добавить для него уменшенные эскизы.
	Можно добавить до 3-х эскизов (первый, средний, последний кадры).
	Для генерации эскизов можно использовать программу Mirada.
	Она постовляется вместе с дистрибутивом Cerebro. Можно использовать и другие программы для генерации,
	например, ffmpeg.
	"""
	
	#Пример генерации эскизов с помощью Mirada.	

	if os.path.exists(filename) == False or os.path.exists(mirada_path) == False:
		return list()
	
	gen_path = os.path.dirname(filename) # В качестве директории для генерации эскизов возьмем директорию добавляемого файла

	# Запускаем мираду с необходимыми ключами
	res_code = subprocess.call([mirada_path, filename, '-temp', gen_path, '-hide'])				
	#-temp - директория для генерации эскизов
	#-hide - ключ запуска мирады в скрытом режиме (без загрузки графического интерфейса) для генерации табнейлов.
	
	if res_code != 0:
		raise Exception("Mirada returned bad exit-status.\n" + mirada_path)
	
	#Ищем сгенерированные мирадой эскизы.
	#Имени эскиза формируется из имени файла, даты и времени генерации - filename_yyyymmdd_hhmmss_thumb[number].jpg
	#Например: test.mov_20120305_112354_thumb1.jpg - первый эскиз видео-файла test.mov
	
	thumbnails = list()
	for f in os.listdir(gen_path):
		if fnmatch.fnmatch(f, os.path.basename(filename) + '_*_thumb?.jpg'):
			thumbnails.append(gen_path + '/' + f)

	thumbnails.sort()	
	
	"""
	#Пример генерации эскизов с помощью ffmpeg.
	
	#Для того, чтобы генерить эскизы с помощью ffmpeg, нужно заранее знать длительность видео,
	#чтобы корректно получить средний и последний кадры.
	#Возьмем к примеру ролик длительностью в 30 секунд.

	thumbnails = list() # список файлов для эскизов
	thumbnails.append(filename + '_thumb1.jpg')
	thumbnails.append(filename + '_thumb2.jpg')
	thumbnails.append(filename + '_thumb3.jpg')

	subprocess.call(['ffmpeg', '-i', filename, '-s', '512x512', '-an', '-ss', '00:00:00', '-r', 1, '-vframes', 1, '-y', thumbnails[0]])
	subprocess.call(['ffmpeg', '-i', filename, '-s', '512x512', '-an', '-ss', '15:00:00', '-r', 1, '-vframes', 1, '-y', thumbnails[1]])
	subprocess.call(['ffmpeg', '-i', filename, '-s', '512x512', '-an', '-ss', '30:00:00', '-r', 1, '-vframes', 1, '-y', thumbnails[2]])
	# Описание ключей вы можете посмотреть в документации к ffmpeg
	"""
	
	return thumbnails
