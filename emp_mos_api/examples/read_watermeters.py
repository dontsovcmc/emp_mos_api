# -*- coding: utf-8 -*-
import argparse
import datetime
from emp_mos_api.mos import MosAPI, get_watercounters_id, get_watercounter_value


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
        print u'Адрес: {}'.format(f['address'])
        print u'Номер кв: {}'.format(f['flat_number'])
        print u'Номер платежки: {}'.format(f['paycode'])

        water = api.get_watercounters(f['flat_id'])

        new_values = []

        hot_ids = get_watercounters_id(u'ГВС', water)  # разбираем ответ

        if hot_ids:
            hot_id = hot_ids[0]
            hot_value = get_watercounter_value(hot_id, water)  # разбираем ответ
            print 'Текущее показание горячей воды: {:.2f} m3'.format(hot_value)

            if args.hot:
                new_values.append({
                    'counter_id': hot_id,
                    'period': datetime.datetime.now().strftime("%Y-%m-%d"),
                    'indication': '{:.2f}'.format(args.hot).replace('.', ',')
                })
                print 'Новое показание горячей воды: {:.2f} m3'.format(args.hot)
        else:
            print u'Не найден счетчик горячей воды'

        #
        cold_ids = get_watercounters_id(u'ХВС', water)

        if cold_ids:
            cold_id = cold_ids[0]
            cold_value = get_watercounter_value(cold_id, water)
            print 'Текущее показание холодной воды: {:.2f} m3'.format(cold_value)

            if args.cold:
                new_values.append({
                    'counter_id': cold_id,
                    'period': datetime.datetime.now().strftime("%Y-%m-%d"),
                    'indication': '{:.2f}'.format(args.cold).replace('.', ',')
                })
                print 'Новое показание холодной воды: {:.2f} m3'.format(args.cold)
        else:
            print u'Не найден счетчик холодной воды'

        if new_values:
            api.send_watercounters(f['flat_id'], new_values)
            print 'Показания отправлены на сервер'

    finally:
        api.logout()
