# -*- coding: utf-8 -*-
from __future__ import print_function
import argparse
from emp_mos_api import MosAPI, Water, Watercounter


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='emp.mos.ru API')
    parser.add_argument('--token', help='application token')
    parser.add_argument('--user_agent', default='okhttp/3.8.1', help='User-Agent header')
    parser.add_argument('--guid', help='some guid')
    parser.add_argument('--dev_user_agent', default='Android', help='application user agent')
    parser.add_argument('--dev_app_version', help='application version')

    parser.add_argument('--login', help='your login (phone number: 7xxxxxxxxxx)')
    parser.add_argument('--pwd', help='your password')

    parser.add_argument('--flat_id', help='id квартиры на сервере. если не указывать, отправится в 1ю.')

    parser.add_argument('--hot', type=float, help='Hot water new value')
    parser.add_argument('--cold', type=float, help='Cold water new value')

    args = parser.parse_args()

    #
    api = MosAPI(token=args.token,
                 user_agent=args.user_agent,
                 guid=args.guid,
                 dev_user_agent=args.dev_user_agent,
                 dev_app_version=args.dev_app_version,
                 verify=True)

    try:
        api.login(args.login, args.pwd)

        if not args.flat_id:
            flats = api.get_flats()
            assert flats, u'Добавьте квартиру в приложении Госуслуги Москвы'
            f = flats[0]
            print('Адрес: ', f['address'])
            print('Номер кв:  ', f['flat_number'])
            print('Номер платежки: ', f['paycode'])

            flat_id = f['flat_id']
        else:
            flat_id = args.flat_id

        counters = api.get_watercounters(flat_id)['counters']

        new_values = []

        hots_json = list(filter(lambda x: x['type'] == Water.HOT, counters))
        if hots_json:
            hot_value = Watercounter.last_value(hots_json[0])
            if hot_value:
                print('Текущее показание горячей воды: {:.2f} m3'.format(hot_value))
            else:
                print('Показания горячей воды не передавались больше 3-х месяцев')

            if args.hot:
                new_values.append(Watercounter.serialize_for_send(hots_json[0], args.hot))
                print('Новое показание горячей воды: {:.2f} m3'.format(args.hot))
        else:
            print('Не найден счетчик горячей воды')

        #
        colds_json = list(filter(lambda x: x['type'] == Water.COLD, counters))
        if colds_json:
            cold_value = Watercounter.last_value(colds_json[0])
            if cold_value:
                print('Текущее показание холодной воды: {:.2f} m3'.format(cold_value))
            else:
                print('Показания холодной воды не передавались больше 3-х месяцев')

            if args.cold:
                new_values.append(Watercounter.serialize_for_send(colds_json[0], args.cold))
                print('Новое показание холодной воды: {:.2f} m3'.format(args.cold))
        else:
            print('Не найден счетчик холодной воды')

        if new_values:
            api.send_watercounters(flat_id, new_values)
            print('Показания отправлены на сервер')

    finally:
        api.logout()  #долго
