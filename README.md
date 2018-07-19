### Неофициальная библиотека для запросов к Единой мобильной платформе города Москвы 

[Сайт](http://mosapps.mos.ru/dev)

Для выполнения запросов требуются:
- уникальный ключ вашего приложения (token), [выданный Правительством Москвы](http://mosapps.mos.ru/dev).
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

## Поддержка вызовов

### Авторизация
Авторизируемся на сервере при помощи номера телефона и пароля, полученного из приложения
```
api.login(args.login, args.pwd)
```
### Завершение сессии
```
api.logout()
```
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
water = api.get_watercounters(flat_id)
```
### Отправить новые показания воды
```
api.send_watercounters(flat_id, new_values)
```

## Примеры:
[examples](https://github.com/dontsovcmc/emp_mos_ru/tree/master/emp_mos_api/examples)


