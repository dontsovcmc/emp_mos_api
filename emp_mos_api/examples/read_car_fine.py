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

    parser.add_argument('--sts', help='your car sts')

    args = parser.parse_args()

    #
    try:
        api = MosAPI(token=args.token,
                     user_agent=args.user_agent,
                     guid=args.guid,
                     dev_user_agent=args.dev_user_agent,
                     dev_app_version=args.dev_app_version,
                     timeout=6)

        api.login(args.login, args.pwd)

        car_fines = api.get_car_fines(args.sts)
        unpaid = car_fines['unpaid']
        print("Неоплаченных штрафов: {}".format(len(unpaid)))

        for u in unpaid:
            print("\nНомер: {}".format(u['seriesAndNumber']))
            print("Дата: {}".format(u['date']))
            print("Место: {}".format(u['offence_place']))
            print("Статья: {}".format(u['offenceType']))
            print("Сумма: {}".format(u['cost']))
            print("is_discount: {}".format(u['is_discount']))
            print("drive_license: {}".format(u['drive_license']))
            print("sts_number: {}".format(u['sts_number']))
            print("executionState: {}".format(u['executionState']))
            print("is_fssp: {}".format(u['is_fssp']))


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
