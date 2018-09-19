# -*- coding: utf-8 -*-
from __future__ import print_function
import argparse
from emp_mos_api.mos import MosAPI, \
    get_flat_id, get_flat_address, get_flat_paycode, get_flat_number, \
    get_watercounters_by_type, get_watercounter_last_value, \
    get_watercounter_id, watercounter_new_value_json, \
    HOT_WATER, COLD_WATER


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='emp.mos.ru API')
    parser.add_argument('--token', help='application token')
    parser.add_argument('--user_agent', default='okhttp/3.8.1', help='User-Agent header')
    parser.add_argument('--guid', help='some guid')
    parser.add_argument('--dev_user_agent', default='Android', help='application user agent')
    parser.add_argument('--dev_app_version', help='application version')

    parser.add_argument('--login', help='your login (phone number: 7xxxxxxxxxx)')
    parser.add_argument('--pwd', help='your password')

    parser.add_argument('--hot', type=float, help='Hot water new value')
    parser.add_argument('--cold', type=float, help='Cold water new value')

    args = parser.parse_args()

    #
    api = MosAPI(token=args.token,
                 user_agent=args.user_agent,
                 guid=args.guid,
                 dev_user_agent=args.dev_user_agent,
                 dev_app_version=args.dev_app_version)

    try:
        api.login(args.login, args.pwd)

        flats = api.get_flats()
        assert flats, u'Добавьте квартиру в приложении Госуслуги Москвы'
        f = flats[0]
        print('Адрес: ', get_flat_address(f))
        print('Номер кв:  ', get_flat_number(f))
        print('Номер платежки: ', get_flat_paycode(f))

        json_data = api.get_watercounters(get_flat_id(f))
        json_wc = api.get_watercounters(json_data)

        new_values = []

        #
        hots_json = get_watercounters_by_type(HOT_WATER, json_wc) # разбираем ответ

        if hots_json:
            hot_value = get_watercounter_last_value(hots_json[0])
            print('Текущее показание горячей воды: {:.2f} m3'.format(hot_value))

            if args.hot:
                new_values.append(watercounter_new_value_json(get_watercounter_id(hots_json[0]), args.hot))
                print('Новое показание горячей воды: {:.2f} m3'.format(args.hot))
        else:
            print('Не найден счетчик горячей воды')

        #
        colds_json = get_watercounters_by_type(COLD_WATER, json_wc)
        if colds_json:
            cold_value = get_watercounter_last_value(colds_json[0])
            print('Текущее показание холодной воды: {:.2f} m3'.format(cold_value))

            if args.cold:
                new_values.append(watercounter_new_value_json(get_watercounter_id(colds_json[0]), args.cold))
                print('Новое показание холодной воды: {:.2f} m3'.format(args.cold))
        else:
            print('Не найден счетчик холодной воды')

        if new_values:
            api.send_watercounters(get_flat_id(f), new_values)
            print('Показания отправлены на сервер')

    finally:
        api.logout()
