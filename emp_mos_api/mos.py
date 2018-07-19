# -*- coding: utf-8 -*-
import requests
import datetime
import argparse
from copy import deepcopy


def check_error(answer):
    """
    :param answer: JSON
    {
        u'errorCode': 0, # 0-OK, 401-Auth error
        u'execTime': 0.138262,
        u'errorMessage': u'', # error message
        u'session_id': u'6c3333333c33333e44e21e7d43c46e03',
        u'result': None or JSON
    }
    :return:
    """
    if answer['errorCode'] != 0:
        raise Exception(u'Error code: {0}, message: {1}'.format(answer['errorCode'], answer['errorMessage']))


counter_types = {
    1: u'ХВС',
    2: u'ГВС'
}


class MosAPI(object):

    def __init__(self, **kwargs):
        self.session = requests.Session()
        self.session_id = None
        self.token = kwargs.get('token')
        self.user_agent = kwargs.get('user_agent')

        self.guid = kwargs.get('guid')
        self.dev_app_version = kwargs.get('dev_app_version')
        self.dev_user_agent = kwargs.get('dev_user_agent')

        self.headers = {'Cache-Control': 'no-cache',
                   'Host': 'emp.mos.ru',
                   'Connection': 'Keep-Alive',
                   'Accept-Encoding': 'gzip',
                   'User-Agent': self.user_agent}

        self.pheaders = deepcopy(self.headers)
        self.pheaders.update({
            'X-Cache-ov': '15552000',
            'X-Cache-ov-mode': 'FORCE_NETWORK'
        })

    def is_active(self):
        """
        :return: True если уже залогинился
        """
        return self.session_id is not None

    def login(self, telephone, pwd):
        """
        :param telephone: Телефон. Вид: 7xxxxxxxxxx
        :param pwd: Пароль из приложения Госуслуги Москвы
        :return: JSON
        {
            u'execTime': 0.138262,
            u'errorMessage': u'',
            u'session_id': u'6c3333333c33333e44e21e7d43c46e03',
            u'errorCode': 0,
            u'result': {
                u'is_filled': True,
                u'surname': u'x',
                u'name': u'x',
                u'session_id': u'6c3333333c33333e44e21e7d43c46e03'},
                u'request_id': u'UN=PRO-12345678-1234-1234-1234-123456789123'
            }
        }
        """
        login_data = {
            'device_info': {
                'guid': self.guid,
                'user_agent': self.dev_user_agent,
                'app_version': self.dev_app_version
            },
            'auth': {
                'login': telephone,
                'password': pwd,
                'guid': self.guid
            }
        }

        ret = self.session.post('https://emp.mos.ru/v1.0/auth/virtualLogin',
                     params={'token': self.token},
                     headers={'Content-Type': 'application/json; charset=UTF-8',
                              'Connection': 'Keep-Alive',
                              'Accept-Encoding': 'gzip',
                              'User-Agent': self.user_agent,
                              'cache-control': 'no-cache',
                              'Host': 'emp.mos.ru',
                              'Accept': '*/*'},
                     verify=False,
                     json=login_data)

        response = ret.json()
        check_error(response)
        self.session_id = response['session_id']
        return response['result']

    def get_profile(self):
        """
        :return: JSON
        {
        u'profile': {
            u'drive_license': None,
            u'firstname': u'x',
            u'middlename': u'x',
            u'lastname': u'x',
            u'birthdate': u'dd.mm.YYYY',
            u'msisdn': u'71234567890',  # your telephone
            u'email_confirmed': True,
            u'email': u'x@x.ru'
            }
        }
        """
        assert self.session_id

        ret = self.session.get('https://emp.mos.ru/v1.0/profile/get',
                    params={'token': self.token,
                            'info[guid]': self.guid,
                            'auth[session_id]': self.session_id
                            },
                    headers=self.pheaders)

        response = ret.json()
        check_error(response)
        return response['result']['profile']

    def get_flats(self):
        """
        :return: JSON array
        [{
            u'name': u'x',
            u'paycode': u'1234567890',
            u'flat_id': u'1234567',
            u'electro_account': None,
            u'flat_number': u'0',
            u'unad': u'0',
            u'address': u'x',
            u'electro_device': None,
            u'unom': u'1234567' # Идентификатор дома
        },{
            ...
        }
        ]
        """
        assert self.session_id

        ret = self.session.get('https://emp.mos.ru/v1.0/flat/get',
                    params={'token': self.token,
                            'info[guid]': self.guid,
                            'auth[session_id]': self.session_id
                            },
                    headers=self.pheaders)

        response = ret.json()
        check_error(response)
        return response['result']

    def get_watercounters(self, flat_id):
        """
        :param flat_id: unicode string from flat_response
                        response[0]['flat_id']
        :return:
        {
            u'stat_title': u'x',
                u'archive': [
                    {
                        u'cold_indication': 1.55,
                        u'hot_indication': 1.2,
                        u'period': u'2017-08-31+03:00'
                    }, {
                        u'cold_indication': 1.3,
                        u'hot_indication': 0.39999999999998,
                        u'period': u'2017-09-30+03:00'
                    }, {
                        +10 эл-тов. Всего 12.
                    }],
                u'counters': [
                    {
                        u'checkup': u'2021-08-08+03:00', # дата поверки
                        u'counterId': 123456, # id счетчика в emp.mos.ru
                        u'num': u'123456',  # серийный номер счетчика
                        u'type': 1,  # ХВС
                        u'indications': [
                            {
                                u'indication': u'200.24',
                                u'period': u'2018-07-31+03:00'
                            }, {
                                u'indication': u'200.6',
                                u'period': u'2018-06-30+03:00'
                            }, {
                                u'indication': u'200.5',
                                u'period': u'2018-05-31+03:00'
                            }, {
                                u'indication': u'200.5',
                                u'period': u'2018-04-30+03:00'
                            }]
                    },{
                        u'checkup': u'2019-08-08+03:00',
                        u'counterId': 123456,
                        u'num': u'123456',
                        u'type': 2, # ГВС
                        u'indications': [
                            {
                                u'indication': u'100.42',
                                u'period': u'2018-07-31+03:00'
                            }, {
                                u'indication': u'100.8',
                                u'period': u'2018-06-30+03:00'
                            }, {
                                u'indication': u'100.4',
                                u'period': u'2018-05-31+03:00'
                            }, {
                                u'indication': u'100.6',
                                u'period': u'2018-04-30+03:00'
                            }]
                }]
        }
        """
        assert self.session_id
        wheaders = deepcopy(self.headers)
        wheaders.update({
                'X-Clears-tags': 'WATER_COUNTERS',
                'X-Cache-ov-mode': 'DEFAULT',
                'Content-Type': 'application/json; charset=UTF-8' })

        wcrequest = {
            'flat_id': flat_id,
            'is_widget': False,
            'info': {
                'guid': self.guid
            },
            'auth': {
                'session_id': self.session_id
            }
        }

        ret = self.session.post('https://emp.mos.ru/v1.0/watercounters/get',
                     params={'token': self.token},
                     headers=wheaders,
                     json=wcrequest)

        response = ret.json()
        check_error(response)
        return response['result']

    def send_watercounters(self, flat_id, counters_data):
        """
        :param flat_id: unicode string from flat_response['flat_id']
        :param counters_data: array of
            [{
                'counter_id': u'123456', # ['counters'][0]['counterId']
                'period': datetime.datetime.now().strftime("%Y-%m-%d"),
                'indication': 'xxx,xx'
            }, {
                ...
            }]
        :return:
        """
        assert self.session_id

        wheaders = deepcopy(self.headers)
        wheaders.update({
                'X-Clears-tags': 'WATER_COUNTERS',
                'Content-Type': 'application/json; charset=UTF-8'
            })

        wcrequest = {'flat_id': flat_id,
                     'counters_data': counters_data,
                     'info': {
                        'guid': self.guid
                     },
                     'auth': {
                        'session_id': self.session_id
                     }}

        ret = self.session.post('https://emp.mos.ru/v1.0/watercounters/addValues',
                     params={'token': self.token},
                     headers=wheaders,
                     json=wcrequest)

        response = ret.json()
        check_error(response)
        return response['result']

    def logout(self):
        if self.session_id:
            logout_data = {
                'info': {
                    'guid': self.guid
                },
                'auth': {
                    'session_id': self.session_id
                }
            }
            ret = self.session.post('https://emp.mos.ru/v1.0/auth/logout',
                         params={'token': self.token},
                         headers=self.headers,
                         json=logout_data)

            response = ret.json()
            check_error(response)
            self.session_id = None
            return response['result']


def get_watercounters_id(water_type, response):
    """
    :param water_type: ГВС, ХВС
    :param response: get_watercounters() response
    :return: array of int or NULL
    """
    counters = filter(lambda x: counter_types[x['type']] == water_type, response['counters'])
    if counters:
        return list(c['counterId'] for c in counters)


def get_watercounter_value(counterId, response):
    """
    :param counterId: ['counters'][x]['counterId']
    :param response: get_watercounters() response
    :return: float
    """
    for c in response['counters']:
        if c['counterId'] == counterId:
            if 'indications' in c:
                indications = c['indications']
                indications.sort(key=lambda x: x['period'])  # alphabetical sort data =)
                assert indications
                return float(indications[-1]['indication'])

