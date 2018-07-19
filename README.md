### Неофициальная библиотека для запросов к серверу Госуслуг г. Москва emp.mos.ru

Для выполнения запросов требуются:
- уникальный ключ вашего приложения (token), выданный Правительством Москвы 
- некий guid (guid)
- при работе с телефона указывается user-agent и версия приложения

Создаем объект api
```
from emp_mos_api.mos import MosAPI

api = MosAPI(token=args.token,
             user_agent=args.user_agent,
             guid=args.guid,
             dev_user_agent=args.dev_user_agent,
             dev_app_version=args.dev_app_version)
```

Авторизируемся на сервере при помощи номера телефона и пароля, полученного из приложения
```
api.login(args.login, args.pwd)
```

## Поддержка вызовов

### Получить профиль и адрес
```
response = api.get_profile()
```
### Получить список квартир
```
flats = api.get_flats()
```
### Получить список счетчиков воды
```
water = api.get_watercounters(flats[0]['flat_id'])
```
### Отправить новые показания воды
```
api.send_watercounters(flats[0]['flat_id'], new_values)
```

## Примеры:
В папке examples


