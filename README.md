# Телеграм-бот PHPSupport

Аналог биржи фрилансеров для выполнения заказов по 1С.
Заказчик покупает подписку на бота и размещаеет заявку (название, описание, прикрепляет файлы)
Фрилансеры видят заявки и берут в работу понравившиеся заявки.

Реализованы чаты клиента с фрилансером, база данных на Джанго, прикручена оплата при выборе тарифа

## Примеры работы ботов:
### Телеграм бот

![max example](gifs/client.gif)

![max example](gifs/freelancer.gif)


Работу бота можно посмотреть по ссылке:
```
https://t.me/freelance_super_bot
```

## Запуск:

### 1. Копируем содержимое проекта себе в рабочую директорию
```
git clone https://github.com/EshiNanase/freelance_bot.git
```

### 2. Устанавливаем библиотеки:
```
pip install -r requirements.txt
```

### 3. Для хранения переменных окружения создаем файл .env и указываем следующее:
```python
TG_BOT_TOKEN = 'your_token'
SECRET_KEY='your_secretcode'
DJANGO_SETTINGS_MODULE=freelance.settings
DEBUG = True
ALLOWED_HOSTS=31.184.254.14,127.0.0.1,localhost
DATABASE_ENGINE=django.db.backends.sqlite3
DATABASE_NAME=db.sqlite3
API_URL=http://31.184.254.14
либо для запуска на локальном компьютере
API_URL=http://127.0.0.1:8000
```

### 4. Запуск
Создайте базу данных SQLite

```sh
python3 manage.py migrate
```

Запустите сервер

```
python3 manage.py runserver
```

Запустите бота
```
python freelance_bot.py
```
