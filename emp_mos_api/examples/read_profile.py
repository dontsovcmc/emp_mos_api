# -*- coding: utf-8 -*-
from __future__ import print_function
import argparse
from emp_mos_api.mos import MosAPI, \
    get_flat_name, get_flat_address, get_flat_paycode, get_flat_number, \
    get_profile_firstname, get_profile_middlename, get_profile_lastname, \
    get_profile_birthdate, get_profile_msisdn, get_profile_email


# Код написан общим для python2, python3 синтаксисом благодаря
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
                 dev_app_version=args.dev_app_version)

    try:
        api.login(args.login, args.pwd)
        p = api.get_profile()

        print('ФИО: ', get_profile_firstname(p),
              ' ', get_profile_middlename(p),
              ' ', get_profile_lastname(p))
        print('Дата рождения: ', get_profile_birthdate(p))
        print('Телефон: ', get_profile_msisdn(p))
        print('Эл. почта: ', get_profile_email(p))

        flats = api.get_flats()

        print('Кол-во квартир: ', len(flats))
        assert flats, 'Добавьте квартиру в приложении Госуслуги Москвы'

        for f in flats:
            print('Квартира #', flats.index(f) + 1)
            print('Название: ', get_flat_name(f))
            print('Адрес: ', get_flat_address(f))
            print('Номер кв: ', get_flat_number(f))
            print('Номер платежки: ', get_flat_paycode(f))

    finally:
        api.logout()
