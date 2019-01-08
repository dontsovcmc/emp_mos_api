# -*- coding: utf-8 -*-
from __future__ import print_function
import argparse
import time
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
    try:
        api = MosAPI(token=args.token,
                     user_agent=args.user_agent,
                     guid=args.guid,
                     dev_user_agent=args.dev_user_agent,
                     dev_app_version=args.dev_app_version,
                     timeout=6)

        api.login(args.login, args.pwd)
        p = api.get_profile()

        flats = api.get_flats()

        print('Кол-во квартир: ', len(flats))
        assert flats, 'Добавьте квартиру в приложении Госуслуги Москвы'

        for f in flats:
            # print(f)
            print('Квартира #', flats.index(f) + 1)
            print('Название: ', f['name'])
            print('Адрес: ', f['address'])
            print('Номер кв: ', f['flat_number'])
            print('Номер платежки: ', f['paycode'])

            print('Счет электро: ', f['electro_account'])
            print('Счетчик электро: ', f['electro_device'])

            for x in range (1,13):
                date = '10.{}.2018'.format(x)
                epd = api.get_epd(f['flat_id'], date, False)
                if epd == []:
                    epd = api.get_epd(f['flat_id'], date, False)
                epd_total = epd[0]['amount']
                epd_is_paid = epd[0]['is_paid']
                print(" - Дата: {}, сумма: {}, оплачен: {}.".format(date, epd_total, epd_is_paid))
                time.sleep(1)

            if f['electro_account'] != "":
                electro = api.get_electrocounters(f['flat_id'])
                balance = electro['balance']
                last_zone1 = electro['zones'][0]['value']
                print("Баланс электро: {}, показания 1 зоны: {}".format(balance, last_zone1))
            # data = [{'counter_id': 'T1', 'indication': 6887, 'period': '2018-12-27'}]
            # send = api.send_electrocounters(f['flat_id'], data)

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
