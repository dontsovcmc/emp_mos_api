# -*- coding: utf-8 -*-
import argparse
from emp_mos_api.mos import MosAPI


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
        profile = api.get_profile()

        print u'ФИО: {} {} {}'.format(profile['firstname'], profile['middlename'], profile['lastname'])
        print u'Дата рождения: {}'.format(profile['birthdate'])
        print u'Телефон: {}'.format(profile['msisdn'])
        print u'Эл. почта: {}'.format(profile['email'])

        flats = api.get_flats()

        print u'Кол-во квартир: {}'.format(len(flats))
        assert flats, u'Добавьте квартиру в приложении Госуслуги Москвы'

        for f in flats:
            print u'Квартира #{}'.format(flats.index(f) + 1)
            print u'Название: {}'.format(f['name'])
            print u'Адрес: {}'.format(f['address'])
            print u'Номер кв: {}'.format(f['flat_number'])
            print u'Номер платежки: {}'.format(f['paycode'])

    finally:
        api.logout()
