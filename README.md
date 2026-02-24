Докеризований проєкт для тестового завдання Asvio Junior DevOps Engineer.

**Архітектура проєкту:**
- **FastAPI** бекенд
- **PostgreSQL** базу даних
- **Nginx** зворотний проксі з **TLS (HTTPS)**
- Скрипт ініціалізації бази даних
- Перевірки стану (Healthchecks) для всіх сервісів

Структура репозиторію базується на трьох основних сервісах (`db`, `api`, `nginx`), 
які визначені у файлі `docker-compose.yml`. API надає ендпоінти для перевірки стану та записів про статус сервісу.

---

## Структура проєкту

```text
task_asvio/
├── app/
│   ├── main.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .dockerignore
├── db-init/
│   └── init.sql
├── nginx/
│   └── default.conf
├── certs/               
│   ├── nginx.crt
│   └── nginx.key
├── .env_example
├── docker-compose.yml
└── README.md
```
---

**Можливості API**

API надає наступні ендпоінти:

- ```GET /health``` — перевіряє підключення до БД (виконує `SELECT 1`)

- ```GET /api/v1/get-status``` — повертає записи з таблиці `service_status`

- ```POST /api/v1/set-status``` — додає новий запис про статус

- ```GET /info``` — повертає версію додатку, ім'я хоста та середовище 

Ці ендпоінти реалізовані у файлі `app/main.py`

---

**База даних PostgreSQL.**

Під час запуску PostgreSQL виконує скрипт ініціалізації з `db-init/init.sql`, який:

  - Створює таблицю `service_status`

  - Вставляє початковий запис: `initialization_successful`

Це відбувається завдяки тому, що docker-compose.yml монтує директорію `./db-init у /docker-entrypoint-initdb.d`

---

**Зворотний проксі Nginx**

Nginx слухає порт 443 з TLS та проксіює запити на внутрішній сервіс FastAPI (`api:8000`). Він також відкриває внутрішній ендпоінт для перевірки стану:

```GET /nginx-health``` - повертає `healthy`

Налаштування визначені у `nginx/default.conf`

---

**Перевірки стану (Healthchecks)**

Перевірки стану налаштовані для:

- Postgres (`pg_isready`)

- Nginx (`/nginx-health`)

- API контейнера (`curl http://localhost:8000/health` всередині `Dockerfile`)

Це допомагає гарантувати, що сервіси запускаються у правильному порядку і залишаються працездатними.

---

## Вимоги

    Docker Engine

    Docker Compose v2

У проєкті використовуються:

    postgres:15-alpine

    nginx:alpine 

    FastAPI додаток на Python, зібраний з app/Dockerfile (базовий образ Python 3.13 slim)

---

## Розгортання

**1) Клонування репозиторію:**
   
```bash
git clone https://github.com/nuclearsalo/task_asvio.git
cd task_asvio
```

**2) Створення файлу змінних середовища:**

Перейменуйте `.env_example` у `.env` та заповніть значення:

```
POSTGRES_DB=
POSTGRES_USER=
POSTGRES_PASSWORD=
```

**3) Створення TLS сертифікатів:**

Nginx налаштований на використання:

```
/etc/nginx/certs/nginx.crt

/etc/nginx/certs/nginx.key
```

Згенеруйте самопідписаний сертифікат:

```bash
mkdir -p certs

openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout certs/nginx.key \
  -out certs/nginx.crt \
  -subj "/CN=localhost"
```
Nginx очікує ці файли, оскільки `docker-compose.yml` монтує директорію `./certs` у контейнер, і на них є посилання у `default.conf`.

**4) Запуск проєкту:**

```bash
docker compose up --build
```

Ця команда:

- Запустить PostgreSQL

- Дочекається, поки Postgres стане повністю готовим (`healthy`)

- Збере та запустить додаток FastAPI

- Запустить Nginx на порту `443`

Порядок запуску сервісів контролюється за допомогою depends_on з умовами перевірки стану (`health conditions`).

---

## Використання

Оскільки Nginx налаштований із самопідписаним сертифікатом, використовуйте прапорець `-k` у `curl` для локального тестування.

**Перевірка стану (healthcheck)**
```Bash

curl -k https://localhost/health
```

Очікувана відповідь:
```JSON

{"status":200}
```

`/health` перевіряє підключення до БД і повертає `HTTP 200` у разі успіху.

---

**Отримання поточних статусів**
```Bash

curl -k https://localhost/api/v1/get-status
```
Приклад відповіді:
```JSON

[
  {
    "id": 1,
    "created_at": "2026-01-01T12:00:00",
    "status": "initialization_successful"
  }
]
```

Початковий запис створюється скриптом `db-init/init.sql`

---

**Додавання нового статусу**

```Bash

curl -k -X POST https://localhost/api/v1/set-status \
  -H "Content-Type: application/json" \
  -d '{"status":"service_running"}'
```

Очікувана відповідь:
```JSON

{"message":"Record inserted successfully"}
```

Тіло POST-запиту валідується за допомогою моделі Pydantic StatusItem (`status: str`).

---

**Отримання інформації про додаток**
```Bash

curl -k https://localhost/info
```

Приклад відповіді:
```JSON

{
  "version": "1.0.0",
  "hostname": "fastapi_app",
  "environment": "dev"
}
```

Ендпоінт зчитує змінні середовища `APP_VERSION` та `ENVIRONMENT`.

---

## Примітки

Контейнер з API налаштований на запуск без прав root (користувач `appuser`) у фінальному образі.
Додаток використовує багатокрокову збірку Docker (builder + runner) для встановлення Python-залежностей у віртуальне середовище та їх подальшого копіювання у runtime-образ.

Python залежності:

        fastapi
        uvicorn
        pydantic
        psycopg2-binary

---

## Вирішення проблем

1) *Nginx не запускається*

Переконайтеся, що файли TLS сертифікатів існують:

    certs/nginx.crt

    certs/nginx.key

Вони необхідні для конфігурації Nginx.

2) *API повертає помилки підключення до бази даних*

Перевірте:

  - Значення у файлі .env (POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD),
 
  - Статус (health) контейнера Postgres.
 
  - Логи:
    
```Bash
docker compose logs db
docker compose logs api
docker compose logs nginx
```

API намагається підключитися до БД під час запуску і використовує механізм повторних спроб.

---

## Скріни виконання

*Налаштування середовища та ssh доступу*
<img width="2559" height="1403" alt="ssh_connect" src="https://github.com/user-attachments/assets/9352d237-cb5d-4f4e-befa-e0a83ba1b69d" />

*Успішне встановлення Docker Engine/Docker Compose*
<img width="2559" height="1439" alt="docker_installed_success" src="https://github.com/user-attachments/assets/65518e45-085c-4970-ac1c-6aeddea0b872" />

*Робота над `docker-compose.yml` - налаштування контейнера датабази. Ізольована `app_network`, `db_data volumes` та використання `.env` файла.*
<img width="2556" height="1437" alt="docker_compose_file" src="https://github.com/user-attachments/assets/ed737dfc-58ec-417b-ae85-aa71b9a734cb" />

*Тестування ініціалізації контейнеру PostgreSQL датабази + додатковий тестовий запис*
<img width="2558" height="1439" alt="initialization_successful" src="https://github.com/user-attachments/assets/03620d44-44ac-4975-bbe1-b2de544620de" />
<img width="437" height="86" alt="image" src="https://github.com/user-attachments/assets/73262c57-07ea-42e7-8ae1-cea071a7ca2a" />

*Тестування готового білду проєкту.*
*З логів збірки FastAPI сервісу чітко видно виконання ключових вимог щодо контейнеризації та безпеки:*

*1. Використання мінімального базового образу `python:3.13-slim`*

*2. Застосування багатокрокової збірки (наявність етапів `builder` та `stage-1`)*

*3. Створення непривілейованого користувача `appuser` та групи `appgroup` (крок `[stage-1 5/6]`) для безпечного запуску контейнера без прав root.*

*4. Наприкінці логу видно, що контейнер бази даних `postgres_db` перейшов у статус `Healthy` безпосередньо перед запуском `fastapi_app`. Це підтверджує успішну роботу healthcheck та реалізацію бонусного механізму `wait-for-db`.*
<img width="2558" height="1439" alt="build" src="https://github.com/user-attachments/assets/35da1d26-cbec-4223-a3b1-305f1faea9b5" />

*Приклади успішних запитів curl з очікуваним JSON поверненням*
<img width="755" height="139" alt="image" src="https://github.com/user-attachments/assets/2e881417-a7d6-467d-8b6f-60c7962dcd12" />

---

## Коментар щодо Nginx

Контейнери FastAPI та PostgreSQL у цьому проєкті налаштовані на роботу строго без прав root. Однак, інтернет овермайнд підсказує мені, що стандартний образ `nginx:alpine` запускає свій майстер-процес від імені `root`. "Це пов'язано з тим, що в Linux непривілейовані користувачі не можуть прослуховувати порти з номерами нижче 1024, до яких належить 443." 

Можливим рішенням є використання `nginx-unprivileged:alpine`, налаштувати Nginx на прослуховування внутрішнього високого порту `listen 8443 ssl;`, а у `docker-compose.yml` використати форвард портів Docker для мапінгу зовнішнього трафіку на внутрішній: `ports: - "443:8443"`. Але я тут не знаю як краще зробити.

---

## Ліцензія

Наразі нема.
