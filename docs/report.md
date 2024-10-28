## Структура проекта
[Общая структура](#общая-структура)\
[Система управления парком автомобилей](#система-управления-парком-автомобилей)\
[Система оплаты услуг](#система-оплаты-услуг)\
[Автомобиль](#автомобиль)\
[Мобильное приложение клиента](#мобильное-приложение-клиента)

### Общая структура

project/
│── module/ **Название модуля** \
│ │── config/ **Содержит файл с зависимостями которые используются в проекте**\
│ └── requirements.txt\
│ │── data/ **Данные используемые в модуле, наличие по необходимости (может быть instance, в случае использования БД)** \
│ │ └── data.json\
│ │── src/ **Основной код модуля**\
│ │ ├── \_\_init\_\_.py **Инициализация приложения (стандартный для всех модулей)** \
│ │ └── main.py **Код приложения** \
│ │── Dockerfile **Сборка образа (стандартный для всех модулей, по необходимости вносяться изменения)** \
└─── start.py **Запуск модуля**

Перед запуском настроить среду для разработки:

```make dev_install```

Пример запуска:

```python3 module/start.py```

Важно! При локальном запуске (не в Docker образе) заменить URL на localhost и так же порт

Пример:

```MANAGMENT_URL = 'http://management_system:8000'``` на ```MANAGMENT_URL = 'http://0.0.0.0:8001'```

### Система управления парком автомобилей

#### cars

Программный имитатор управления парком автомобилей, содержит простую базу данных для хранения данных клиента

### API

#### URL http://0.0.0.0:8003

|Название метода|Тип запроса|Входные параметры|Ответ (успешный)|Описание|
|:--|:--|:--|:--|:--|
|/cars|GET||list[string]|Опрашивает доступные автомобили и отдаёт список свободных автомобилей|
|/tariff|GET||list[string]|Отдает список тарифов|
|/telemetry/<string:brand>|POST|Имя автомобиля||Функция для получения телеметрии от автомобилей во время поездки|
|/access/<string:name>|POST|Имя клиента|{'access': bool, 'tariff': string, 'car': string}| Проверка доступа клиента до автомобиля|
|/confirm_prepayment/<string:name>|POST|Имя клиента||Фукнция получения потверждений об оплате предоплаты клиента от системы оплаты услуг|
|/confirm_payment/<string:name>|POST|Имя клиента|{'car': string, 'name': string, 'final_amount': int,'created_at': time, 'elapsed_time': int, 'tarif': string}|Фукнция получения потверждений об оплате поездки клиента от системы оплаты услуг, формирует финальный чек о поездке и передаёт клиенту|
|/select/car/<string:brand>|POST|{'client_name': string, 'experience': int, 'tariff': string}|{'id': int, 'amount': int, 'client_id': int, 'status': string}|Бронирование и рассчет предоплаты в зависимости от функций автомобиля|
|/return/<string:name>|POST|Имя клиента|{'id': int, 'amount': int, 'status': string, 'client_id': int}|Рассчёт стоимости всей поездки в зависимости от опыта и тарифа, создание оплаты. Получает запрос от автомобиля|

### Система оплаты услуг

#### payment-system

Программный имитатор банковской системы, содержит базу данных для сохранения операций клиента

### API

#### URL http://0.0.0.0:8000

|Название метода|Тип запроса|Входные параметры|Ответ (успешный)|Описание|
|:--|:--|:--|:--|:--|
|/clients|POST|{"name": string}|{'id': int, 'name': string}|Создает или отдаёт клиента если он существует в базе системы оплаты услуг|
|/clients/<int:client_id>|GET|int|{'id': int, 'name': string}|Получение по ИД (системы оплаты услуг) клиента|
|/clients/<int:client_id>/invoices|GET|int|[{'id': int, 'amount': int, 'status': string}]|Получение всех неоплаченных счётов клиента|
|/invoices|POST|{'client_id': int, 'amount': int}|{'id': int, 'amount': int, 'status': string, 'client_id': int}|Создание оплаты для клиента|
|/invoices/<int:invoice_id>|GET|int|{'id': int, 'amount': int, 'status': string, 'client_id': int}|Получение статуса оплаты по ИД|
|/invoices/<int:invoice_id>/confirm|POST|int|{'id': int, 'status': string, 'final_receipt': {'car': string, 'name': string, 'final_amount': int,'created_at': time, 'elapsed_time': int, 'tarif': string}}|Оплата счёта по ИД и получение финального чека от системы управления парком автомобилей|
|/invoices/<int:invoice_id>/receipt|GET|int|{'id': int, 'amount': int, 'status': string, 'created_at': time,'client_id': id}|Формирование чека от системы оплаты услугу, архивирование оплаты|
|/clients/<int:client_id>/archived_invoices|GET|||Получение архива платежей по ИД клиента (не используется)|
|/clients/<int:client_id>/prepayment|POST|{'amount':int}|{'id': int, 'amount': int, 'client_id': int, 'status': string}|Создание счёта предоплаты|
|/prepayment/<int:prepayment_id>/confirm|POST|int|{'id': int, 'status': string}|Оплата счёта предоплаты|
|/clients/<int:client_id>/prepayments|GET|int|[{'id': int, 'amount': int, 'status': string}]|Получение всех предоплат по ID клиента|

### Автомобиль

#### cars
Программный имитатор автомобилей, эмулирует поезду и взаимодействие с автомобилем\
Доступно добавление автомобилей путем добавления записи в файл **cars.json** по аналогии с записями в файле

### API

#### URL http://0.0.0.0:8001

|Название метода|Тип запроса|Входные параметры|Ответ (успешный)|Описание|
|:--|:--|:--|:--|:--|
|/car/status/all|GET||[{"brand": string,"is_running": bool,"speed": int,"coordinates": (int, int), "occupied_by": string, "trip_time": int, "has_air_conditioner": bool, "has_heater": bool, "has_navigator": bool, "tariff ": string}]|Возвращает все статусы автомобилей|
|/car/start/<string:brand>|POST|Имя автомобиля|string|Запуск автомобиля|
|/car/stop/<string:brand>|POST|Имя автомобиля|string|Остановка автомобиля|
|/car/status/<string:brand>|GET|Имя автомобиля|{"brand": string,"is_running": bool,"speed": int,"coordinates": (int, int), "occupied_by": string, "trip_time": int, "has_air_conditioner": bool, "has_heater": bool, "has_navigator": bool, "tariff ": string}|Получени статуса автомобиля|
|/car/occupy/<string:person>|POST|Имя клиента|string|Арендовать автомобиль|

### Мобильное приложение клиента

#### mobile-client

Программный имитатор мобильного приложения отвечающего за связь со всеми системами

### API 

#### URL http://0.0.0.0:8002

|Название метода|Тип запроса|Входные параметры|Ответ (успешный)|Описание|
|:--|:--|:--|:--|:--|
|/cars|POST|{"name": string, "experience": int}|{'id': int, 'amount': int, 'client_id': int, 'status': string}|Выбор автомобиля из свободных, выбор тарифа и получение счёта для оплаты предоплаты|
|/start_drive|POST|{name: string}|string|Начало поездки, проверка доступа до автомобиля|
|/stop_drive|POST|{name: string}|{'id': int, 'amount': int, 'status': string, 'client_id': int}|Окончание поездки, возвращение автомобиля. Так же присылается итоговая оплата поездки в зависимости от тарифа|
|/prepayment|POST|{'id': int, 'amount': int, 'client_id': int, 'status': string}|{'invoice_id': int}|Оплата предоплаты|
|/final_pay|POST|{'invoice_id': int}|{'car': string, 'name': string, 'final_amount': int,'created_at': time, 'elapsed_time': int, 'tarif': string}|Оплата поездки и получение финального чека|
