# -*- coding: utf-8 -*-
from __future__ import print_function
import argparse
from emp_mos_api import MosAPI, AuthException, EmpServerException

# Код написан общим для python2, python3 благодаря
# http://python-future.org/compatible_idioms.html

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='emp.mos.ru API')
    parser.add_argument('--token', help='application token')
    parser.add_argument('--user_agent', default='okhttp/3.8.1', help='User-Agent header')
    parser.add_argument('--guid', help='some guid')
    parser.add_argument('--dev_user_agent', default='Android', help='application user agent')
    parser.add_argument('--dev_app_version', help='application version')

    parser.add_argument('--login', help='your login (phone number: 7xxxxxxxxxx)')
    parser.add_argument('--pwd', help='your password')

    args = parser.parse_args()

    #
    api = MosAPI(token=args.token,
                 user_agent=args.user_agent,
                 guid=args.guid,
                 dev_user_agent=args.dev_user_agent,
                 dev_app_version=args.dev_app_version,
                 timeout=6)

    try:
        api.login(args.login, args.pwd)
        p = api.get_profile()

        print('ФИО: ', p['firstname'],
              ' ', p['middlename'],
              ' ', p['lastname'])
        print('Дата рождения: ', p['birthdate'])
        print('Телефон: ', p['msisdn'])
        print('Эл. почта: ', p['email'])

        flats = api.get_flats()

        print('Кол-во квартир: ', len(flats))
        assert flats, 'Добавьте квартиру в приложении Госуслуги Москвы'

        for f in flats:
            print('Квартира #', flats.index(f) + 1)
            print('Название: ', f['name'])
            print('Адрес: ', f['address'])
            print('Номер кв: ', f['flat_number'])
            print('Номер платежки: ', f['paycode'])

    except AuthException as err:
        print('Некорректный логин или пароль')
    except EmpServerException as err:
        print('Ошибка сервера: {}'.format(err))
    except Exception as err:
        print('Ошибка: {}'.format(err))
    finally:
        try:
            api.logout()
        except Exception as err:
            print('Ошибка: {}'.format(err))
